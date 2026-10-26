"""
AliXRobot motion profiles (v2.0)
Pure Python, no GUI code.

Single source of truth for:
- the profile shapes (linear, smoothstep, s_curve, trapezoidal)
- argument validation (profile name, step count)
- path interpolation between two points

RobotEngine and visualization.geometry both use this module, so a
profile cannot behave differently in different parts of the app.
"""
from __future__ import annotations

from numbers import Integral
from typing import Callable, Sequence

# Fraction of the move spent accelerating (and, symmetrically, decelerating)
# in the trapezoidal profile. 1/3 -> ramp, cruise, ramp in equal thirds.
TRAPEZOID_RAMP = 1.0 / 3.0


def _linear(t: float) -> float:
    return t


def _smoothstep(t: float) -> float:
    """Cubic ease-in-out. Zero velocity at both ends, no cruise phase."""
    return t * t * (3.0 - 2.0 * t)


def _s_curve(t: float) -> float:
    """Quintic ease-in-out (minimum-jerk). Zero velocity and acceleration at both ends."""
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


def _trapezoidal(t: float) -> float:
    """Ramp up, constant-velocity cruise, ramp down."""
    r = TRAPEZOID_RAMP
    v_peak = 1.0 / (1.0 - r)
    if t < r:
        return v_peak * t * t / (2.0 * r)
    if t <= 1.0 - r:
        return v_peak * (t - r / 2.0)
    u = 1.0 - t
    return 1.0 - v_peak * u * u / (2.0 * r)


PROFILES: dict[str, Callable[[float], float]] = {
    "linear": _linear,
    "smoothstep": _smoothstep,
    "s_curve": _s_curve,
    "trapezoidal": _trapezoidal,
}

PROFILE_NAMES: tuple[str, ...] = tuple(PROFILES)


def validate_profile(profile: object) -> str:
    """Return the profile name if valid, otherwise raise ValueError."""
    if not isinstance(profile, str) or profile not in PROFILES:
        raise ValueError(
            f"Unknown profile {profile!r}. "
            f"Valid profiles: {', '.join(PROFILE_NAMES)}."
        )
    return profile


def validate_steps(steps: object) -> int:
    """Return the step count if it is an integer >= 2, otherwise raise ValueError."""
    if isinstance(steps, bool) or not isinstance(steps, Integral):
        raise ValueError(
            f"steps must be an integer >= 2, received {steps!r}."
        )
    if steps < 2:
        raise ValueError(
            f"steps must be >= 2 (a path needs a start and an end), received {steps}."
        )
    return int(steps)


def interpolate_path(
    start: Sequence[float],
    end: Sequence[float],
    steps: int,
    profile: str = "linear",
) -> list[list[float]]:
    """
    Return `steps` points from `start` to `end`, shaped by `profile`.

    The first point is exactly `start` and the last is exactly `end`.
    Points are snapshots at equal TIME intervals: with a non-linear
    profile they are not equally spaced in space.

    Raises ValueError for an unknown profile, a bad step count, or
    start/end of different dimensions.
    """
    validate_profile(profile)
    steps = validate_steps(steps)
    if len(start) != len(end):
        raise ValueError("Start and end points must have the same dimension.")

    shape = PROFILES[profile]
    last = steps - 1
    path: list[list[float]] = []
    for i in range(last + 1):
        s = shape(i / last)
        # (1 - s)*a + s*b is exact at s = 0 and s = 1, unlike a + s*(b - a).
        path.append([
            (1.0 - s) * float(a) + s * float(b)
            for a, b in zip(start, end)
        ])
    return path
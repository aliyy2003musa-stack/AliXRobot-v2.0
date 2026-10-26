"""
Trajectory tests (Finding 3 and related). Plain asserts: run with
    python test_trajectory.py      or      pytest test_trajectory.py
"""
import math

from robotEngine import RobotEngine
from profiles import PROFILE_NAMES, interpolate_path
from visualization.geometry import create_advanced_path


def raises(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as error:
        return str(error)
    except Exception as error:  # wrong exception type
        raise AssertionError(f"expected {exc.__name__}, got {type(error).__name__}: {error}")
    raise AssertionError(f"expected {exc.__name__}, nothing raised")


def ready_engine(dim=2):
    e = RobotEngine()
    pos = [1.0, 0.0] if dim == 2 else [1.0, 0.0, 2.0]
    e.configure_robot(dim, "Articulated", 3, pos)
    e.apply_transformation(translate_by=[5.0, 2.0] if dim == 2 else [5.0, 2.0, 1.0],
                           rotate_degrees=90.0, scale_by=2.0)
    return e


# ---- Finding 3: each failure is distinguishable --------------------------
def test_bad_step_counts_raise_value_error():
    e = ready_engine()
    for bad in (0, 1, -50, True, 2.5, "10", None):
        raises(ValueError, e.generate_trajectory_path, "linear", bad)
        raises(ValueError, create_advanced_path, [0, 0], [1, 1], bad, "linear")


def test_unconfigured_robot_raises_runtime_error():
    msg = raises(RuntimeError, RobotEngine().generate_trajectory_path)
    assert "configured" in msg


def test_configured_but_not_transformed_raises_runtime_error():
    e = RobotEngine()
    e.configure_robot(2, "Articulated", 3, [1.0, 0.0])
    msg = raises(RuntimeError, e.generate_trajectory_path)
    assert "transformation" in msg


def test_unknown_profile_names_raise_and_list_valid_ones():
    e = ready_engine()
    for bad in ("s-curve", "S_CURVE", "Trapezoidal", "quintic", "", None):
        msg = raises(ValueError, e.generate_trajectory_path, bad, 5)
        for name in PROFILE_NAMES:
            assert name in msg
        raises(ValueError, create_advanced_path, [0, 0], [1, 1], 5, bad)


def test_steps_2_is_the_smallest_valid_path():
    e = ready_engine()
    p = e.generate_trajectory_path("linear", 2)
    assert p == [e.position, e.transformed_position]


# ---- correctness of the paths ---------------------------------------------
def test_endpoints_are_exact_for_every_profile_and_size():
    e = ready_engine()
    for profile in PROFILE_NAMES:
        for n in (2, 3, 10, 50, 1000):
            p = e.generate_trajectory_path(profile, n)
            assert len(p) == n
            assert p[0] == e.position, (profile, n)
            assert p[-1] == e.transformed_position, (profile, n)


def test_endpoints_exact_with_wildly_different_magnitudes():
    for profile in PROFILE_NAMES:
        p = interpolate_path([1e16, -3.0], [1.0, 1e-9], 7, profile)
        assert p[0] == [1e16, -3.0] and p[-1] == [1.0, 1e-9]


def test_profiles_are_monotonic():
    for profile in PROFILE_NAMES:
        xs = [q[0] for q in interpolate_path([0.0], [1.0], 2001, profile)]
        assert all(b >= a for a, b in zip(xs, xs[1:])), profile


def test_dimension_is_preserved():
    assert all(len(q) == 2 for q in ready_engine(2).generate_trajectory_path("s_curve", 5))
    assert all(len(q) == 3 for q in ready_engine(3).generate_trajectory_path("s_curve", 5))


def test_profiles_have_their_defining_shapes():
    n = 3001
    v = {}
    for profile in PROFILE_NAMES:
        xs = [q[0] for q in interpolate_path([0.0], [1.0], n, profile)]
        v[profile] = [(b - a) * (n - 1) for a, b in zip(xs, xs[1:])]  # velocity, unit move
    assert math.isclose(max(v["linear"]), 1.0, rel_tol=1e-9)
    assert math.isclose(max(v["smoothstep"]), 1.5, rel_tol=1e-3)
    assert math.isclose(max(v["s_curve"]), 15 / 8, rel_tol=1e-3)
    # trapezoidal: peak 1.5 AND a flat cruise across the middle third
    assert math.isclose(max(v["trapezoidal"]), 1.5, rel_tol=1e-3)
    mid = v["trapezoidal"][int(0.4 * n):int(0.6 * n)]
    assert max(mid) - min(mid) < 1e-9
    # smoothstep has no flat top
    mid = v["smoothstep"][int(0.4 * n):int(0.6 * n)]
    assert max(mid) - min(mid) > 0.05


def test_s_curve_is_not_linear():
    # regression: s_curve once silently produced a linear path
    x = [q[0] for q in interpolate_path([0.0], [1.0], 5, "s_curve")]
    assert math.isclose(x[1], 0.103515625, rel_tol=1e-12)
    assert x[1] != 0.25


def test_geometry_and_engine_agree():
    e = ready_engine()
    for profile in PROFILE_NAMES:
        a = e.generate_trajectory_path(profile, 9)
        b = create_advanced_path(e.position, e.transformed_position, 9, profile)
        assert [tuple(p) + (0.0,) for p in a] == b


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    for name, fn in tests:
        fn()
        print("PASS", name)
    print(f"\n{len(tests)} tests passed")
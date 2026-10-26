"""
AliXRobot Geometry (v2.0)
Geometry/data generation utilities for robot visualization.
This module contains NO PyQt6 code and NO pyqtgraph rendering code.

Responsibilities:
- Generate geometric representations of robots.
- Generate points, links, axes, and frames.
- Provide 2D/3D geometry data to visualization widgets.
- Keep visualization geometry independent from RobotEngine.

The RobotEngine remains responsible for mathematical transformations.
This module only prepares geometry for visualization.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Sequence, Optional

from profiles import interpolate_path

# ============================================================
# TYPES
# ============================================================
Point2D = tuple[float, float]
Point3D = tuple[float, float, float]

# ============================================================
# ROBOT GEOMETRY DATA
# ============================================================
@dataclass
class RobotGeometry:
    """
    Container for robot geometry.
    
    Attributes
    ----------
    joints:
        List of 3D joint positions.
    links:
        List of pairs of 3D points representing robot links.
    origin:
        Robot base/origin.
    end_effector:
        Final robot point.
    """
    joints: list[Point3D]
    links: list[tuple[Point3D, Point3D]]
    origin: Point3D
    end_effector: Point3D

# ============================================================
# VALIDATION
# ============================================================
def validate_point(
    point: Sequence[float],
    dimension: int,
) -> None:
    """
    Validate a point.
    
    Parameters
    ----------
    point:
        Coordinate sequence.
    dimension:
        Expected dimension.
    """
    if dimension not in (2, 3):
        raise ValueError(
            "Dimension must be 2 or 3."
        )
    if len(point) != dimension:
        raise ValueError(
            f"Expected {dimension} coordinates, "
            f"received {len(point)}."
        )

# ============================================================
# CONVERT 2D -> 3D
# ============================================================
def to_3d(
    point: Sequence[float],
) -> Point3D:
    """
    Convert a 2D or 3D point into a 3D point.
    2D:
        [x, y] -> (x, y, 0)
    3D:
        [x, y, z] -> (x, y, z)
    """
    if len(point) == 2:
        return (
            float(point[0]),
            float(point[1]),
            0.0,
        )
    if len(point) == 3:
        return (
            float(point[0]),
            float(point[1]),
            float(point[2]),
        )
    raise ValueError(
        "Point must contain two or three coordinates."
    )

# ============================================================
# DISTANCE
# ============================================================
def distance(
    point_a: Sequence[float],
    point_b: Sequence[float],
) -> float:
    """
    Calculate Euclidean distance between two points.
    """
    if len(point_a) != len(point_b):
        raise ValueError(
            "Points must have the same dimension."
        )
    return math.sqrt(
        sum(
            (
                float(a) - float(b)
            ) ** 2
            for a, b in zip(point_a, point_b)
        )
    )

# ============================================================
# INTERPOLATION
# ============================================================
def interpolate(
    start: Sequence[float],
    end: Sequence[float],
    count: int,
) -> list[Point3D]:
    """
    Generate evenly spaced points between two points.
    Useful for creating robot links or animation paths.
    """
    if len(start) != len(end):
        raise ValueError(
            "Start and end points must have "
            "the same dimension."
        )
    if len(start) not in (2, 3):
        raise ValueError(
            "Points must be 2D or 3D."
        )
    if count < 2:
        raise ValueError(
            "Count must be at least 2."
        )
    start_3d = to_3d(start)
    end_3d = to_3d(end)
    result = []
    for i in range(count):
        t = i / (count - 1)
        x = (
            start_3d[0]
            +
            t * (
                end_3d[0] - start_3d[0]
            )
        )
        y = (
            start_3d[1]
            +
            t * (
                end_3d[1] - start_3d[1]
            )
        )
        z = (
            start_3d[2]
            +
            t * (
                end_3d[2] - start_3d[2]
            )
        )
        result.append(
            (x, y, z)
        )
    return result

# ============================================================
# SINGLE LINK
# ============================================================
def create_link(
    start: Sequence[float],
    end: Sequence[float],
) -> tuple[Point3D, Point3D]:
    """
    Create a robot link between two points.
    """
    return (
        to_3d(start),
        to_3d(end),
    )

# ============================================================
# ROBOT FROM JOINTS
# ============================================================
def create_robot_geometry(
    joints: Sequence[Sequence[float]],
) -> RobotGeometry:
    """
    Create robot geometry from a sequence of joint positions.
    
    Example
    -------
        joints = [
            [0, 0],
            [2, 0],
            [2, 2],
        ]
    Produces two links:
        joint 0 -> joint 1
        joint 1 -> joint 2
    """
    if not joints:
        raise ValueError(
            "At least one joint is required."
        )
    converted = [
        to_3d(point)
        for point in joints
    ]
    links = []
    for index in range(
        len(converted) - 1
    ):
        links.append(
            (
                converted[index],
                converted[index + 1],
            )
        )
    return RobotGeometry(
        joints=converted,
        links=links,
        origin=converted[0],
        end_effector=converted[-1],
    )

# ============================================================
# SIMPLE ROBOT GENERATOR
# ============================================================
def generate_serial_robot(
    origin: Sequence[float],
    link_lengths: Sequence[float],
    dimension: int = 2,
) -> RobotGeometry:
    """
    Generate a simple serial robot.
    This is primarily a visualization helper.
    For now, links are arranged along the positive X axis.
    
    Example
    -------
        generate_serial_robot(
            [0, 0],
            [2, 1, 1],
            2,
        )
    produces:
        (0,0)
           |
        (2,0)
           |
        (3,0)
           |
        (4,0)
    """
    validate_point(
        origin,
        dimension,
    )
    if not link_lengths:
        raise ValueError(
            "At least one link length is required."
        )
    origin_3d = to_3d(origin)
    joints = [
        origin_3d
    ]
    current_x = origin_3d[0]
    current_y = origin_3d[1]
    current_z = origin_3d[2]
    for length in link_lengths:
        current_x += float(length)
        joints.append(
            (
                current_x,
                current_y,
                current_z,
            )
        )
    return create_robot_geometry(
        joints
    )

# ============================================================
# COORDINATE AXES
# ============================================================
def create_axes(
    origin: Sequence[float],
    length: float = 1.0,
) -> dict[str, tuple[Point3D, Point3D]]:
    """
    Create X, Y and Z coordinate axes.
    """
    if length <= 0:
        raise ValueError(
            "Axis length must be positive."
        )
    origin_3d = to_3d(origin)
    x_axis = (
        origin_3d,
        (
            origin_3d[0] + length,
            origin_3d[1],
            origin_3d[2],
        ),
    )
    y_axis = (
        origin_3d,
        (
            origin_3d[0],
            origin_3d[1] + length,
            origin_3d[2],
        ),
    )
    z_axis = (
        origin_3d,
        (
            origin_3d[0],
            origin_3d[1],
            origin_3d[2] + length,
        ),
    )
    return {
        "x": x_axis,
        "y": y_axis,
        "z": z_axis,
    }

# ============================================================
# TRANSFORMATION PATH
# ============================================================
def create_transformation_path(
    original: Sequence[float],
    transformed: Sequence[float],
    samples: int = 50,
) -> list[Point3D]:
    """
    Generate a straight-line path between an original
    and transformed position.
    This is useful for animation.
    """
    return interpolate(
        original,
        transformed,
        samples,
    )

# ============================================================
# V2.0: ADVANCED PATH PROFILES
# ============================================================
def create_advanced_path(
    start: Sequence[float],
    end: Sequence[float],
    samples: int = 50,
    profile: str = "linear",
) -> list[Point3D]:
    """
    Generate a 3D path from start to end shaped by a motion profile.

    Profiles: 'linear', 'smoothstep', 's_curve', 'trapezoidal'.
    The first point is exactly start and the last is exactly end.
    Points are snapshots at equal time intervals, not equally spaced
    in space.

    Raises ValueError for an unknown profile, samples < 2, or
    start/end of different dimensions.
    """
    if len(start) != len(end):
        raise ValueError("Start and end points must have the same dimension.")
    path = interpolate_path(
        to_3d(start),
        to_3d(end),
        samples,
        profile,
    )
    return [(p[0], p[1], p[2]) for p in path]

# ============================================================
# V2.0: WORKSPACE GRID GENERATOR
# ============================================================
def generate_workspace_grid(
    center: Sequence[float],
    radius: float,
    resolution: int = 10,
    dimension: int = 2,
) -> list[Point3D]:
    """
    Generates a point cloud representing the robot's reachable workspace.
    Returns a list of 3D points (z=0 for 2D).
    """
    center_3d = to_3d(center)
    points = []
    step = radius / resolution
    
    x_range = range(-resolution, resolution + 1)
    y_range = range(-resolution, resolution + 1)
    z_range = range(-resolution, resolution + 1) if dimension == 3 else [0]
    
    for x_idx in x_range:
        for y_idx in y_range:
            for z_idx in z_range:
                x = center_3d[0] + x_idx * step
                y = center_3d[1] + y_idx * step
                z = center_3d[2] + z_idx * step
                
                # Simple spherical/circular distance check
                dist = math.sqrt((x_idx * step)**2 + (y_idx * step)**2 + (z_idx * step)**2)
                if dist <= radius:
                    points.append((x, y, z))
                    
    return points

# ============================================================
# V2.0: LINK LENGTH CALCULATOR
# ============================================================
def calculate_link_lengths(
    joints: Sequence[Sequence[float]],
) -> list[float]:
    """
    Calculates the physical length of each link between consecutive joints.
    """
    lengths = []
    for i in range(len(joints) - 1):
        lengths.append(distance(joints[i], joints[i+1]))
    return lengths

# ============================================================
# V2.0: EXPORT FORMATTER
# ============================================================
def geometry_to_export_dict(
    geometry: RobotGeometry,
) -> dict:
    """
    Formats RobotGeometry into a clean dictionary for CSV/JSON export.
    """
    return {
        "origin": list(geometry.origin),
        "end_effector": list(geometry.end_effector),
        "joints": [list(j) for j in geometry.joints],
        "links": [[list(start), list(end)] for start, end in geometry.links],
        "link_lengths": calculate_link_lengths(geometry.joints),
    }
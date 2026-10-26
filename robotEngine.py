"""
AliXRobot Robot Engine (v2.0)
Coordinates robot configuration, mathematical
transformation operations, and advanced path planning.
This module is intentionally independent of the GUI.
"""
from __future__ import annotations
import math
from typing import Sequence
from robotControl_logic import (
    Matrix,
    compose_transform,
    parse_numbers,
    transform_point,
)
from profiles import (
    interpolate_path,
    validate_profile,
    validate_steps,
)


class RobotEngine:
    def __init__(self):
        # =================================================
        # ROBOT CONFIGURATION
        # =================================================
        self.dimension: int | None = None
        self.robot_type: str | None = None
        self.dof: int | None = None
        self.position: list[float] | None = None
        
        # =================================================
        # TRANSFORMATION RESULTS
        # =================================================
        self.transform: Matrix | None = None
        self.transformed_position: list[float] | None = None
        
        # =================================================
        # DYNAMIC PARAMETERS
        # =================================================
        self.velocity = None
        self.acceleration = None
        self.inertia = None
        self.pid = None

    # =====================================================
    # INPUT PARSING
    # =====================================================
    def parse_position(
        self,
        text: str,
        dimension: int,
    ) -> list[float]:
        return parse_numbers(
            text,
            expected_length=dimension,
        )

    # =====================================================
    # ROBOT CONFIGURATION
    # =====================================================
    def configure_robot(
        self,
        dimension: int,
        robot_type: str,
        dof: int,
        position: Sequence[float],
    ) -> None:
        if dimension not in (2, 3):
            raise ValueError(
                "Robot dimension must be 2 or 3."
            )
        if dof < 1:
            raise ValueError(
                "Degrees of freedom must be at least 1."
            )
        if len(position) != dimension:
            raise ValueError(
                f"Expected {dimension} "
                f"position coordinates."
            )
            
        self.dimension = dimension
        self.robot_type = robot_type
        self.dof = int(dof)
        self.position = [
            float(value)
            for value in position
        ]

    # =====================================================
    # APPLY TRANSFORMATION (FIXED INDENTATION BUG)
    # =====================================================
    def apply_transformation(
        self,
        translate_by: Sequence[float] | None = None,
        rotate_degrees: float | None = None,
        scale_by: float | Sequence[float] | None = None,
        axis: str = "z",
    ) -> list[float]:
        if self.dimension is None:
            raise RuntimeError(
                "Robot must be configured "
                "before transformation."
            )
        if self.position is None:
            raise RuntimeError(
                "Robot position has not "
                "been defined."
            )

        # =================================================
        # BUILD TRANSFORMATION MATRIX
        # =================================================
        self.transform = compose_transform(
            dimension=self.dimension,
            translate_by=translate_by,
            rotate_degrees=rotate_degrees,
            scale_by=scale_by,
            axis=axis,
        )
        
        # =================================================
        # CALCULATE & RETURN TRANSFORMED POSITION
        # (FIXED: Moved out of the dead code block below)
        # =================================================
        self.transformed_position = transform_point(
            self.position,
            self.transform,
        )
        return self.transformed_position

    # =====================================================
    # TRANSFORM ALL VERTICES
    # =====================================================
    def transform_vertices(self, vertex_matrix):
        """
        Transform all vertices of the robot.
        vertex_matrix: dimension x vertices  
        (rows = axes, columns = vertices — exactly what 
        MainWindow.get_vertex_matrix() returns).
        """
        matrix = self.get_transform()
        if matrix is None:
            raise RuntimeError("No transformation matrix available.")
            
        dimension = len(vertex_matrix)
        vertex_count = len(vertex_matrix[0]) if dimension else 0
        
        transformed_points = []
        for col in range(vertex_count):
            point = [vertex_matrix[row][col] for row in range(dimension)]
            transformed_points.append(transform_point(point, matrix))
            
        # back to dimension x vertices, matching the table's orientation
        return [
            [transformed_points[col][row] for col in range(vertex_count)]
            for row in range(dimension)
        ]

    # =====================================================
    # RESULTS
    # =====================================================
    def get_transform(
        self,
    ) -> Matrix | None:
        return self.transform

    # -----------------------------------------------------
    def get_position(
        self,
    ) -> list[float] | None:
        return self.position

    # -----------------------------------------------------
    def get_transformed_position(
        self,
    ) -> list[float] | None:
        return self.transformed_position

    # =====================================================
    # ROBOT INFORMATION
    # =====================================================
    def get_robot_info(
        self,
    ) -> dict:
        return {
            "dimension": self.dimension,
            "robot_type": self.robot_type,
            "dof": self.dof,
            "position": self.position,
            "transformed_position": self.transformed_position,
            "transform": self.transform,
        }

    # =====================================================
    # RESET
    # =====================================================
    def reset(
        self,
    ) -> None:
        self.dimension = None
        self.robot_type = None
        self.dof = None
        self.position = None
        self.transform = None
        self.transformed_position = None
        self.velocity = None
        self.acceleration = None
        self.inertia = None
        self.pid = None

    # =====================================================
    # V2.0: ADVANCED TRAJECTORY GENERATOR
    # =====================================================
    def generate_trajectory_path(
        self,
        profile: str = "linear",
        steps: int = 50,
    ) -> list[list[float]]:
        """
        Generate a path from the original to the transformed position.

        Profiles: 'linear', 'smoothstep', 's_curve', 'trapezoidal'.
        The first point is exactly the original position and the last is
        exactly the transformed position. Points are snapshots at equal
        time intervals, not equally spaced waypoints.

        Raises
        ------
        ValueError
            Unknown profile, or steps is not an integer >= 2.
        RuntimeError
            Robot not configured, or no transformation applied yet.
        """
        validate_profile(profile)
        validate_steps(steps)

        if self.dimension is None or self.position is None:
            raise RuntimeError(
                "Robot must be configured before generating a trajectory."
            )
        if self.transformed_position is None:
            raise RuntimeError(
                "Apply a transformation before generating a trajectory."
            )

        return interpolate_path(
            self.position,
            self.transformed_position,
            steps,
            profile,
        )

    # =====================================================
    # V2.0: WORKSPACE CALCULATOR
    # =====================================================
    def calculate_workspace(
        self,
        resolution: int = 10,
    ) -> list[list[float]]:
        """
        Generates a point cloud representing the robot's reachable workspace.
        (Simplified approximation based on current position and DOF).
        """
        if self.position is None:
            return []
            
        workspace_points = []
        # Create a grid around the base position
        range_val = max(1.0, self.dof * 2.0)
        step = range_val / resolution
        
        for x in range(-resolution, resolution + 1):
            for y in range(-resolution, resolution + 1):
                if self.dimension == 3:
                    for z in range(-resolution, resolution + 1):
                        # Simple distance check from base
                        dist = math.sqrt((x*step)**2 + (y*step)**2 + (z*step)**2)
                        if dist <= range_val:
                            workspace_points.append([
                                self.position[0] + x * step,
                                self.position[1] + y * step,
                                self.position[2] + z * step
                            ])
                else:
                    dist = math.sqrt((x*step)**2 + (y*step)**2)
                    if dist <= range_val:
                        workspace_points.append([
                            self.position[0] + x * step,
                            self.position[1] + y * step
                        ])
        return workspace_points

    # =====================================================
    # V2.0: EXPORT DATA FORMATTER
    # =====================================================
    def get_export_data(
        self,
        vertex_matrix=None,
        transformed_vertices=None,
    ) -> dict:
        """
        Packages all robot data into a clean dictionary for PDF/CSV export.
        """
        return {
            "dimension": self.dimension,
            "robot_type": self.robot_type,
            "dof": self.dof,
            "base_position": self.position,
            "transformed_position": self.transformed_position,
            "transformation_matrix": self.transform,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "inertia": self.inertia,
            "pid": self.pid,
            "original_vertices": vertex_matrix,
            "transformed_vertices": transformed_vertices,
        }
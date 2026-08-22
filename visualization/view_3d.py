"""
MCE 308 - 3D Robot Visualization (v2.0)
Lightweight 3D-style robot visualization implemented entirely
with PyQt6 QPainter.
The RobotEngine remains responsible for all mathematical
calculations.
This widget is responsible only for visualization.
"""
from __future__ import annotations
import math
from typing import Any, Optional, Sequence
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import (
    QBrush,
    QFont,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
)


class View3D(QWidget):
    """
    Lightweight 3D-style robot visualization widget.
    Uses dynamic projection to display 3D coordinates on a 2D Qt canvas.
    """

    # =====================================================
    # CONSTRUCTOR
    # =====================================================
    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        
        # -------------------------------------------------
        # ROBOT STATE
        # -------------------------------------------------
        self.position: Optional[list[float]] = None
        self.transformed_position: Optional[list[float]] = None
        self.translation: Optional[list[float]] = None
        self.rotation_degrees: Optional[float] = None
        self.scaling_factor: Optional[float] = None
        self.rotation_axis: Optional[str] = None
        self.transformation_matrix: Any = None
        
        # NEW v2.0: Full robot joint data & workspace
        self.original_joints: Optional[list[list[float]]] = None
        self.transformed_joints: Optional[list[list[float]]] = None
        self.workspace_points: Optional[list[list[float]]] = None
        self.show_workspace: bool = False

        # -------------------------------------------------
        # INTERACTIVE CAMERA STATE (NEW v2.0)
        # -------------------------------------------------
        self.yaw = 45.0       # Rotation around Z axis
        self.pitch = 35.264   # Rotation around X axis (Standard Isometric)
        self.is_dragging = False
        self.last_mouse_pos: Optional[QPointF] = None

        # -------------------------------------------------
        # VISUAL SETTINGS & UI
        # -------------------------------------------------
        self.setMinimumSize(380, 320)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("QWidget { background-color: white; }")

        # NEW v2.0: Button Layout
        self.workspace_button = QPushButton("Toggle Workspace")
        self.save_image_button = QPushButton("Save Image")
        self.reset_camera_button = QPushButton("Reset Camera")
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.workspace_button)
        btn_layout.addWidget(self.save_image_button)
        btn_layout.addWidget(self.reset_camera_button)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addStretch(1)
        main_layout.addLayout(btn_layout)

        # -------------------------------------------------
        # SIGNALS
        # -------------------------------------------------
        self.workspace_button.clicked.connect(self._toggle_workspace)
        self.save_image_button.clicked.connect(self.save_image)
        self.reset_camera_button.clicked.connect(self._reset_camera)

    # =====================================================
    # MOUSE EVENTS (INTERACTIVE CAMERA v2.0)
    # =====================================================
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.is_dragging and self.last_mouse_pos is not None:
            delta = event.position() - self.last_mouse_pos
            self.yaw += delta.x() * 0.5
            self.pitch += delta.y() * 0.5
            # Clamp pitch to prevent flipping
            self.pitch = max(-89.0, min(89.0, self.pitch))
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.last_mouse_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _reset_camera(self):
        self.yaw = 45.0
        self.pitch = 35.264
        self.update()

    def _toggle_workspace(self):
        self.show_workspace = not self.show_workspace
        self.update()

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save 3D View Image", "", "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            # Grab the widget content (excluding the buttons at the bottom)
            # We create a temporary painter to grab just the canvas area
            pixmap = self.grab()
            pixmap.save(file_path)

    # =====================================================
    # UPDATE ROBOT
    # =====================================================
    def update_robot(
        self,
        position: Sequence[float],
        transformed_position: Sequence[float],
        transformation_matrix=None,
        translation=None,
        rotation_degrees=None,
        scaling_factor=None,
        rotation_axis=None,
        axis=None,
        original_joints=None,
        transformed_joints=None,
        workspace_points=None,
        **kwargs,
    ) -> None:
        self.position = self._safe_vector(position)
        self.transformed_position = self._safe_vector(transformed_position)
        self.translation = self._safe_vector(translation) if translation else None
        self.rotation_degrees = float(rotation_degrees) if rotation_degrees is not None else None
        self.scaling_factor = float(scaling_factor) if scaling_factor is not None else None
        self.rotation_axis = rotation_axis if rotation_axis is not None else axis
        self.transformation_matrix = transformation_matrix
        
        # NEW v2.0: Store joints and workspace
        self.original_joints = original_joints
        self.transformed_joints = transformed_joints
        self.workspace_points = workspace_points
        
        self.update()

    # =====================================================
    # PAINT EVENT
    # =====================================================
    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
            
            # Reserve space at the bottom for buttons
            width = self.width()
            height = self.height() - 40 
            
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
            
            self._draw_title(painter)
            
            if self.position is None or self.transformed_position is None:
                self._draw_empty_state(painter, width, height)
                return
                
            scene_scale = self._calculate_scene_scale(width, height)
            origin = QPointF(width * 0.50, height * 0.48)
            
            self._draw_grid(painter, origin, scene_scale)
            self._draw_axes(painter, origin, scene_scale)
            
            # NEW v2.0: Draw Workspace
            if self.show_workspace and self.workspace_points:
                self._draw_workspace(painter, self.workspace_points, origin, scene_scale)
            
            # NEW v2.0: Draw Full Robot Links
            if self.original_joints:
                self._draw_robot_links(painter, self.original_joints, origin, scene_scale, Qt.GlobalColor.red)
            if self.transformed_joints:
                self._draw_robot_links(painter, self.transformed_joints, origin, scene_scale, Qt.GlobalColor.blue)

            original_point = self._project_point(self.position, origin, scene_scale)
            transformed_point = self._project_point(self.transformed_position, origin, scene_scale)
            
            self._draw_transformation_path(painter, original_point, transformed_point)
            
            self._draw_robot_point(painter, original_point, radius=9, label="Original", brush=Qt.GlobalColor.red)
            self._draw_robot_point(painter, transformed_point, radius=11, label="Transformed", brush=Qt.GlobalColor.blue)
            
            self._draw_information(painter, width, height)
        finally:
            painter.end()

    # =====================================================
    # NEW v2.0: DRAW WORKSPACE
    # =====================================================
    def _draw_workspace(self, painter, points, origin, scale):
        painter.setPen(QPen(Qt.GlobalColor.lightGray, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
        for p in points:
            pt = self._project_point(p, origin, scale)
            painter.drawEllipse(pt, 2, 2)

    # =====================================================
    # NEW v2.0: DRAW ROBOT LINKS & JOINTS
    # =====================================================
    def _draw_robot_links(self, painter, joints, origin, scale, color):
        if not joints or len(joints) < 2:
            return
        pen = QPen(color, 4, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        for i in range(len(joints) - 1):
            p1 = self._project_point(joints[i], origin, scale)
            p2 = self._project_point(joints[i+1], origin, scale)
            painter.drawLine(p1, p2)
            
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        for joint in joints:
            p = self._project_point(joint, origin, scale)
            painter.drawEllipse(p, 5, 5)

    # =====================================================
    # TITLE
    # =====================================================
    def _draw_title(self, painter: QPainter) -> None:
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(18, 28, "3D Robot Visualization")
        painter.setFont(QFont("Arial", 9))
        painter.setPen(Qt.GlobalColor.darkGray)
        painter.drawText(18, 47, "Drag to rotate camera (v2.0)")

    # =====================================================
    # EMPTY STATE
    # =====================================================
    def _draw_empty_state(self, painter: QPainter, width: int, height: int) -> None:
        painter.setPen(Qt.GlobalColor.darkGray)
        painter.setFont(QFont("Arial", 12))
        painter.drawText(18, height // 2, "No robot defined.\n\nEnter the robot parameters\nand click \"Define Robot\".")

    # =====================================================
    # GRID
    # =====================================================
    def _draw_grid(self, painter: QPainter, origin: QPointF, scale: float) -> None:
        painter.setPen(QPen(Qt.GlobalColor.lightGray, 1))
        grid_size = 6
        for index in range(-grid_size, grid_size + 1):
            x1 = self._project_point((index, -grid_size, 0), origin, scale)
            x2 = self._project_point((index, grid_size, 0), origin, scale)
            painter.drawLine(x1, x2)
            
            y1 = self._project_point((-grid_size, index, 0), origin, scale)
            y2 = self._project_point((grid_size, index, 0), origin, scale)
            painter.drawLine(y1, y2)

    # =====================================================
    # AXES
    # =====================================================
    def _draw_axes(self, painter: QPainter, origin: QPointF, scale: float) -> None:
        axis_length = 4.0
        x_end = self._project_point((axis_length, 0, 0), origin, scale)
        painter.setPen(QPen(Qt.GlobalColor.red, 3))
        painter.drawLine(origin, x_end)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(x_end + QPointF(7, 5), "X")
        
        y_end = self._project_point((0, axis_length, 0), origin, scale)
        painter.setPen(QPen(Qt.GlobalColor.darkGreen, 3))
        painter.drawLine(origin, y_end)
        painter.drawText(y_end + QPointF(-15, 0), "Y")
        
        z_end = self._project_point((0, 0, axis_length), origin, scale)
        painter.setPen(QPen(Qt.GlobalColor.blue, 3))
        painter.drawLine(origin, z_end)
        painter.drawText(z_end + QPointF(7, 0), "Z")
        
        painter.setPen(Qt.GlobalColor.black)
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.drawEllipse(origin, 4, 4)
        painter.drawText(origin + QPointF(7, 15), "O")

    # =====================================================
    # TRANSFORMATION PATH
    # =====================================================
    def _draw_transformation_path(self, painter: QPainter, original: QPointF, transformed: QPointF) -> None:
        pen = QPen(Qt.GlobalColor.darkGray, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(original, transformed)

    # =====================================================
    # ROBOT POINT
    # =====================================================
    def _draw_robot_point(self, painter: QPainter, point: QPointF, radius: float, label: str, brush) -> None:
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QBrush(brush))
        painter.drawEllipse(point, radius, radius)
        
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(point + QPointF(radius + 7, -radius - 3), label)

    # =====================================================
    # INFORMATION
    # =====================================================
    def _draw_information(self, painter: QPainter, width: int, height: int) -> None:
        panel_width = min(390, width - 30)
        panel_height = 95
        panel_x = 15
        panel_y = height - panel_height - 15
        
        painter.setPen(QPen(Qt.GlobalColor.lightGray, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawRoundedRect(panel_x, panel_y, panel_width, panel_height, 8, 8)
        
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 9))
        x = panel_x + 10
        y = panel_y + 18
        painter.drawText(x, y, "Original: " + self._format_vector(self.position))
        painter.drawText(x, y + 18, "Transformed: " + self._format_vector(self.transformed_position))
        
        rotation_text = "None" if self.rotation_degrees is None else f"{self.rotation_degrees:.3f}°"
        axis_text = "None" if self.rotation_axis is None else str(self.rotation_axis)
        painter.drawText(x, y + 36, f"Rotation: {rotation_text}")
        painter.drawText(x, y + 54, f"Axis: {axis_text}")
        scaling_text = "None" if self.scaling_factor is None else f"{self.scaling_factor:.3f}"
        painter.drawText(x, y + 72, f"Scaling: {scaling_text}")

    # =====================================================
    # SCENE SCALE
    # =====================================================
    def _calculate_scene_scale(self, width: int, height: int) -> float:
        points = []
        if self.position: points.append(self.position)
        if self.transformed_position: points.append(self.transformed_position)
        if self.translation: points.append(self.translation)
        if self.original_joints: points.extend(self.original_joints)
        if self.transformed_joints: points.extend(self.transformed_joints)

        maximum = 1.0
        for point in points:
            if point is None: continue
            for value in point:
                try: maximum = max(maximum, abs(float(value)))
                except (TypeError, ValueError): continue
                
        available = min(width, height) * 0.32
        scale = available / maximum
        return max(8.0, min(scale, 60.0))

    # =====================================================
    # PROJECT POINT (UPGRADED v2.0: DYNAMIC CAMERA)
    # =====================================================
    def _project_point(self, point: Sequence[float], origin: QPointF, scale: float) -> QPointF:
        if point is None:
            return QPointF(origin)
        try: x = float(point[0])
        except (IndexError, TypeError, ValueError): x = 0.0
        try: y = float(point[1])
        except (IndexError, TypeError, ValueError): y = 0.0
        try: z = float(point[2])
        except (IndexError, TypeError, ValueError): z = 0.0
        
        # Convert camera angles to radians
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)
        
        # Rotate around Z axis (yaw)
        x1 = x * math.cos(yaw_rad) - y * math.sin(yaw_rad)
        y1 = x * math.sin(yaw_rad) + y * math.cos(yaw_rad)
        z1 = z
        
        # Rotate around X axis (pitch)
        y2 = y1 * math.cos(pitch_rad) - z1 * math.sin(pitch_rad)
        z2 = y1 * math.sin(pitch_rad) + z1 * math.cos(pitch_rad)
        x2 = x1
        
        # Orthographic projection to 2D screen
        projected_x = origin.x() + x2 * scale
        projected_y = origin.y() - z2 * scale
        
        return QPointF(projected_x, projected_y)

    # =====================================================
    # SAFE VECTOR
    # =====================================================
    @staticmethod
    def _safe_vector(vector) -> Optional[list[float]]:
        if vector is None: return None
        try: values = list(vector)
        except TypeError: return None
        result = []
        for value in values:
            try: result.append(float(value))
            except (TypeError, ValueError): result.append(0.0)
        return result

    # =====================================================
    # CLEAR
    # =====================================================
    def clear(self) -> None:
        self.position = None
        self.transformed_position = None
        self.translation = None
        self.rotation_degrees = None
        self.scaling_factor = None
        self.rotation_axis = None
        self.transformation_matrix = None
        self.original_joints = None
        self.transformed_joints = None
        self.workspace_points = None
        self.show_workspace = False
        self.update()

    # =====================================================
    # FORMAT VECTOR
    # =====================================================
    @staticmethod
    def _format_vector(vector) -> str:
        if vector is None: return "None"
        try: return "[ " + ", ".join(f"{float(value):.3f}" for value in vector) + " ]"
        except (TypeError, ValueError): return str(vector)
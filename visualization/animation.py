"""
AliXRobot Robot Animation (v2.1 — Professional Simulator Edition)
Implements Stage 1-4 of the advanced specification:
- Real manipulator rendering (base/joints/links/end-effector)
- Coordinate frames (World, Base, End-Effector)
- Real trajectory path + motion history
- Live transformation matrix & pose readout
- Velocity/acceleration vectors
- Advanced interpolation (Linear/Cubic/Quintic/Smoothstep/S-Curve)
- Simulation status (FPS, time, progress)
- Visualization toggles
- CSV + PDF telemetry export
"""
from __future__ import annotations
from typing import Optional, Sequence, Callable
import math
import time
import csv
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QFont, QColor, QKeyEvent, QLinearGradient,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLabel, QFrame, QSlider, QFileDialog, QMessageBox, QCheckBox,
    QGroupBox, QScrollArea, QSizePolicy,
)


# ============================================================
# INTERPOLATION PROFILES (mathematically correct)
# ============================================================
class InterpolationProfile:
    """Pure functions — no state, easy to test."""

    @staticmethod
    def linear(t: float) -> float:
        return max(0.0, min(1.0, t))

    @staticmethod
    def cubic(t: float) -> float:
        """Hermite smoothstep: 3t² - 2t³"""
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def quintic(t: float) -> float:
        """Perlin's improved smoothstep: 6t⁵ - 15t⁴ + 10t³
        Continuous position, velocity AND acceleration."""
        t = max(0.0, min(1.0, t))
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    @staticmethod
    def smoothstep(t: float) -> float:
        """Alias for cubic — standard graphics smoothstep."""
        return InterpolationProfile.cubic(t)

    @staticmethod
    def s_curve(t: float) -> float:
        """Trapezoidal velocity profile approximation."""
        t = max(0.0, min(1.0, t))
        if t < 0.5:
            return 2.0 * t * t
        return 1.0 - 2.0 * (1.0 - t) * (1.0 - t)


# ============================================================
# ANIMATION CANVAS — all painting in one place
# ============================================================
class AnimationCanvas(QFrame):
    """Dedicated painting surface. No business logic here."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(380)
        self.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #CBD5E1; border-radius: 6px; }"
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # --- Robot state (set by parent) ---
        self.position: Optional[list[float]] = None
        self.transformed_position: Optional[list[float]] = None
        self.current_position: Optional[list[float]] = None
        self.dimension: int = 2
        self.original_joints: Optional[list[list[float]]] = None
        self.transformed_joints: Optional[list[list[float]]] = None
        self.current_joints: Optional[list[list[float]]] = None
        self.progress: float = 0.0
        self.current_matrix: Optional[list[list[float]]] = None

        # --- Visualization toggles ---
        self.show_robot = True
        self.show_joints = True
        self.show_links = True
        self.show_target = True
        self.show_original = True
        self.show_trajectory = True
        self.show_frames = True
        self.show_grid = True
        self.show_velocity = False
        self.show_acceleration = False
        self.show_motion_history = False
        self.render_mode = "Solid"  # Simple / Wireframe / Solid

        # --- Dynamic data ---
        self.trajectory_points: list[list[float]] = []
        self.motion_history: list[list[list[float]]] = []  # list of joint poses
        self.velocity_vector: Optional[list[float]] = None
        self.acceleration_vector: Optional[list[float]] = None

    # --------------------------------------------------------
    # PROJECTION (isometric, auto-scaled to bounding box)
    # --------------------------------------------------------
    def _compute_projection(self, width: int, height: int):
        """Returns (project_fn, center_3d, scale)."""
        all_points = []
        if self.position: all_points.append(self.position)
        if self.transformed_position: all_points.append(self.transformed_position)
        if self.current_position: all_points.append(self.current_position)
        if self.original_joints: all_points.extend(self.original_joints)
        if self.transformed_joints: all_points.extend(self.transformed_joints)
        if self.trajectory_points: all_points.extend(self.trajectory_points)
        if not all_points:
            return None, None, None

        min_x = min(p[0] for p in all_points)
        max_x = max(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_y = max(p[1] for p in all_points)
        min_z = min((p[2] for p in all_points if len(p) > 2), default=0.0)
        max_z = max((p[2] for p in all_points if len(p) > 2), default=0.0)

        range_x = max(max_x - min_x, 1.0)
        range_y = max(max_y - min_y, 1.0)
        range_z = max(max_z - min_z, 1.0)

        margin = 70
        usable_w = width - 2 * margin
        usable_h = height - 2 * margin - 50

        scale_x = usable_w / (range_x + range_y)
        scale_y = usable_h / (range_z + (range_x + range_y) * 0.35)
        scale = min(scale_x, scale_y) * 0.82

        center = (
            (min_x + max_x) / 2.0,
            (min_y + max_y) / 2.0,
            (min_z + max_z) / 2.0,
        )
        cx, cy = width / 2.0, (height / 2.0) - 25

        def project(pt):
            x, y = float(pt[0]), float(pt[1])
            z = float(pt[2]) if len(pt) > 2 else 0.0
            dx, dy, dz = x - center[0], y - center[1], z - center[2]
            px = cx + (dx - dy) * scale
            py = cy - dz * scale - (dx + dy) * scale * 0.35
            return QPointF(px, py)

        return project, center, scale

    # --------------------------------------------------------
    # PAINT
    # --------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        W, H = self.width(), self.height()

        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        # Title + status
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        painter.drawText(20, 28, "Robot Transformation Animation")
        painter.setFont(QFont("Arial", 9))
        painter.setPen(QPen(Qt.GlobalColor.darkGray))
        painter.drawText(20, 46, f"Mode: {self.dimension}D | Render: {self.render_mode}")

        if self.position is None or self.transformed_position is None:
            painter.setPen(QPen(Qt.GlobalColor.darkGray))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                "No robot loaded.\n\nDefine a robot to start.",
            )
            painter.end()
            return

        if self.current_position is None:
            self.current_position = list(self.position)

        project, center, scale = self._compute_projection(W, H)
        if project is None:
            painter.end()
            return

        # --- Grid ---
        if self.show_grid:
            self._draw_grid(painter, project, center, scale)

        # --- Motion history (ghosts) ---
        if self.show_motion_history and self.motion_history:
            for idx, pose in enumerate(self.motion_history):
                alpha = int(60 * (idx / max(1, len(self.motion_history))))
                self._draw_robot_pose(painter, project, pose, QColor(100, 100, 100, alpha), thin=True)

        # --- Trajectory path ---
        if self.show_trajectory and len(self.trajectory_points) > 1:
            self._draw_trajectory(painter, project)

        # --- Coordinate frames ---
        if self.show_frames:
            self._draw_world_frame(painter, project, center, scale)
            if self.position:
                self._draw_base_frame(painter, project, self.position, scale)
            if self.current_position:
                self._draw_end_effector_frame(painter, project, self.current_position, scale)

        # --- Dashed path (original → target) ---
        start = project(self.position)
        target = project(self.transformed_position)
        painter.setPen(QPen(QColor(180, 180, 180), 1, Qt.PenStyle.DashLine))
        painter.drawLine(start, target)

        # --- Original & Target markers (base point) ---
        if self.show_original:
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.drawEllipse(start, 9, 9)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(start + QPointF(-38, -14), "Original")

        if self.show_target:
            painter.setPen(QPen(Qt.GlobalColor.blue, 2))
            painter.setBrush(QBrush(Qt.GlobalColor.blue))
            painter.drawEllipse(target, 10, 10)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(target + QPointF(14, -14), "Target")

        # --- Original / Target full vertex shapes (outline only,
        #     drawn faintly so the animated "current" robot below
        #     is still the visual focus) ---
        if self.show_original and self.original_joints and len(self.original_joints) >= 2:
            self._draw_static_outline(painter, project, self.original_joints, QColor(220, 50, 50, 120))

        if self.show_target and self.transformed_joints and len(self.transformed_joints) >= 2:
            self._draw_static_outline(painter, project, self.transformed_joints, QColor(30, 80, 220, 120))

        # --- Robot (animated, current pose) ---
        if self.show_robot and self.current_joints:
            color = QColor(20, 120, 60) if self.render_mode == "Solid" else QColor(40, 40, 40)
            self._draw_robot_pose(painter, project, self.current_joints, color, thin=False)

        # --- End-effector highlight ---
        if self.current_position:
            cur = project(self.current_position)
            painter.setPen(QPen(Qt.GlobalColor.darkGreen, 2))
            painter.setBrush(QBrush(Qt.GlobalColor.darkGreen))
            painter.drawEllipse(cur, 13, 13)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(cur + QPointF(16, 5), "EE")

        # --- Velocity / Acceleration vectors ---
        if self.show_velocity and self.velocity_vector and self.current_position:
            self._draw_vector(painter, project, self.current_position, self.velocity_vector, QColor(255, 140, 0), "v")
        if self.show_acceleration and self.acceleration_vector and self.current_position:
            self._draw_vector(painter, project, self.current_position, self.acceleration_vector, QColor(180, 0, 180), "a")

        # --- Live info panel (top-right) ---
        self._draw_info_panel(painter, W)

        # --- Progress bar ---
        bar_y = H - 32
        bar_w = max(100, W - 140)
        painter.setPen(QPen(Qt.GlobalColor.gray, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
        painter.drawRoundedRect(QRectF(70, bar_y, bar_w, 5), 2, 2)
        pw = bar_w * max(0.0, min(1.0, self.progress))
        if pw > 0:
            painter.setBrush(QBrush(Qt.GlobalColor.darkGreen))
            painter.drawRoundedRect(QRectF(70, bar_y, pw, 5), 2, 2)

        painter.end()

    # --------------------------------------------------------
    # Drawing helpers
    # --------------------------------------------------------
    def _draw_grid(self, painter, project, center, scale):
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        span = int(20 / max(scale, 0.1)) + 2
        for i in range(-span, span + 1):
            p1 = project([center[0] + i, center[1] - span, center[2]])
            p2 = project([center[0] + i, center[1] + span, center[2]])
            painter.drawLine(p1, p2)
            p1 = project([center[0] - span, center[1] + i, center[2]])
            p2 = project([center[0] + span, center[1] + i, center[2]])
            painter.drawLine(p1, p2)

    def _draw_world_frame(self, painter, project, center, scale):
        origin = project([center[0], center[1], center[2]])
        L = 22
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        # X
        x_end = project([center[0] + L / scale, center[1], center[2]])
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        painter.drawLine(origin, x_end)
        painter.drawText(x_end + QPointF(4, 4), "Xw")
        # Y
        y_end = project([center[0], center[1] + L / scale, center[2]])
        painter.setPen(QPen(Qt.GlobalColor.darkGreen, 2))
        painter.drawLine(origin, y_end)
        painter.drawText(y_end + QPointF(-14, 0), "Yw")
        # Z
        if self.dimension >= 3:
            z_end = project([center[0], center[1], center[2] + L / scale])
            painter.setPen(QPen(Qt.GlobalColor.blue, 2))
            painter.drawLine(origin, z_end)
            painter.drawText(z_end + QPointF(4, -4), "Zw")

    def _draw_base_frame(self, painter, project, base_pt, scale):
        L = 18
        origin = project(base_pt)
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        x_end = project([base_pt[0] + L / scale, base_pt[1], base_pt[2] if len(base_pt) > 2 else 0])
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        painter.drawLine(origin, x_end)
        painter.drawText(x_end + QPointF(3, 3), "Xb")
        y_end = project([base_pt[0], base_pt[1] + L / scale, base_pt[2] if len(base_pt) > 2 else 0])
        painter.setPen(QPen(Qt.GlobalColor.darkGreen, 2))
        painter.drawLine(origin, y_end)
        painter.drawText(y_end + QPointF(-12, 0), "Yb")
        if self.dimension >= 3 and len(base_pt) > 2:
            z_end = project([base_pt[0], base_pt[1], base_pt[2] + L / scale])
            painter.setPen(QPen(Qt.GlobalColor.blue, 2))
            painter.drawLine(origin, z_end)
            painter.drawText(z_end + QPointF(3, -3), "Zb")

    def _draw_end_effector_frame(self, painter, project, ee_pt, scale):
        L = 14
        origin = project(ee_pt)
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        x_end = project([ee_pt[0] + L / scale, ee_pt[1], ee_pt[2] if len(ee_pt) > 2 else 0])
        painter.setPen(QPen(QColor(200, 80, 0), 2))
        painter.drawLine(origin, x_end)
        y_end = project([ee_pt[0], ee_pt[1] + L / scale, ee_pt[2] if len(ee_pt) > 2 else 0])
        painter.setPen(QPen(QColor(0, 160, 120), 2))
        painter.drawLine(origin, y_end)
        if self.dimension >= 3 and len(ee_pt) > 2:
            z_end = project([ee_pt[0], ee_pt[1], ee_pt[2] + L / scale])
            painter.setPen(QPen(QColor(120, 0, 200), 2))
            painter.drawLine(origin, z_end)

    def _draw_robot_pose(self, painter, project, joints, color, thin: bool):
        if not joints or len(joints) < 1:
            return
        line_w = 2 if thin else (5 if self.render_mode == "Solid" else 2)
        joint_r = 4 if thin else (8 if self.render_mode == "Solid" else 5)

        # Links
        if self.show_links and len(joints) > 1:
            painter.setPen(QPen(color, line_w, Qt.PenStyle.SolidLine))
            if self.render_mode == "Wireframe":
                painter.setPen(QPen(color, line_w, Qt.PenStyle.DashLine))
            for i in range(len(joints) - 1):
                p1 = project(joints[i])
                p2 = project(joints[i + 1])
                painter.drawLine(p1, p2)

        # Joints
        if self.show_joints:
            painter.setPen(QPen(Qt.GlobalColor.black, 1 if thin else 2))
            painter.setBrush(QBrush(color))
            for j in joints:
                p = project(j)
                painter.drawEllipse(p, joint_r, joint_r)

        # Base (first joint) — larger, distinct
        if not thin and self.show_joints and joints:
            base = project(joints[0])
            painter.setBrush(QBrush(QColor(60, 60, 60)))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawEllipse(base, joint_r + 3, joint_r + 3)

        # End-effector (last joint) — distinct
        if not thin and self.show_joints and len(joints) > 1:
            ee = project(joints[-1])
            painter.setBrush(QBrush(QColor(220, 50, 50)))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawEllipse(ee, joint_r + 3, joint_r + 3)

    def _draw_static_outline(self, painter, project, points, color):
        """
        Draw a faint outline connecting a fixed (non-animated) vertex
        set — used for the original and target shapes so the user can
        see the full polygon, not just its base point.
        """
        if len(points) < 2:
            return

        projected = [project(p) for p in points]

        drawn = list(projected)
        if len(projected) >= 3:
            drawn.append(projected[0])

        painter.setPen(QPen(color, 1, Qt.PenStyle.DashLine))
        for p1, p2 in zip(drawn, drawn[1:]):
            painter.drawLine(p1, p2)

    def _draw_trajectory(self, painter, project):
        painter.setPen(QPen(QColor(100, 100, 255, 180), 2, Qt.PenStyle.SolidLine))
        for i in range(len(self.trajectory_points) - 1):
            p1 = project(self.trajectory_points[i])
            p2 = project(self.trajectory_points[i + 1])
            painter.drawLine(p1, p2)
        # Path dots
        painter.setBrush(QBrush(QColor(100, 100, 255, 180)))
        painter.setPen(QPen(Qt.NoPen))
        for p in self.trajectory_points[::max(1, len(self.trajectory_points) // 30)]:
            pt = project(p)
            painter.drawEllipse(pt, 2, 2)

    def _draw_vector(self, painter, project, origin_pt, vector, color, label):
        scale = 3.0  # visual amplification
        end_pt = [origin_pt[i] + vector[i] * scale for i in range(len(origin_pt))]
        p1 = project(origin_pt)
        p2 = project(end_pt)
        painter.setPen(QPen(color, 2))
        painter.drawLine(p1, p2)
        # Arrowhead
        painter.setBrush(QBrush(color))
        painter.drawEllipse(p2, 4, 4)
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(p2 + QPointF(6, -6), label)

    def _draw_info_panel(self, painter, W):
        panel_w, panel_h = 220, 95
        x, y = W - panel_w - 15, 10
        painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawRoundedRect(QRectF(x, y, panel_w, panel_h), 5, 5)
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Consolas", 9))
        cy = y + 16
        if self.current_position:
            painter.drawText(x + 8, cy, f"X: {self.current_position[0]:+.3f}")
            if len(self.current_position) > 1:
                painter.drawText(x + 115, cy, f"Y: {self.current_position[1]:+.3f}")
            cy += 14
            if len(self.current_position) > 2:
                painter.drawText(x + 8, cy, f"Z: {self.current_position[2]:+.3f}")
            else:
                painter.drawText(x + 115, cy, "Z: —")
            cy += 16
        if self.current_matrix:
            painter.drawText(x + 8, cy, "T (row 1):")
            cy += 13
            row1 = self.current_matrix[0] if len(self.current_matrix) > 0 else []
            txt = " ".join(f"{v:+.2f}" for v in row1[:4]) if row1 else "—"
            painter.drawText(x + 8, cy, txt)
            cy += 13
            row2 = self.current_matrix[1] if len(self.current_matrix) > 1 else []
            txt = " ".join(f"{v:+.2f}" for v in row2[:4]) if row2 else "—"
            painter.drawText(x + 8, cy, txt)


# ============================================================
# MAIN WIDGET
# ============================================================
class RobotAnimation(QWidget):
    # Signals for external consumers
    progress_changed = pyqtSignal(float)
    simulation_status_changed = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # --- Robot state ---
        self.robot_definition = None
        self.position = None
        self.transformed_position = None
        self.current_position = None
        self.dimension = 2
        self.original_joints = None
        self.transformed_joints = None
        self.current_joints = None
        self.current_matrix = None

        # --- Kinematics (velocity/acceleration), initialized up
        #     front so _sync_canvas never needs a hasattr() guard ---
        self.velocity_vector: Optional[list[float]] = None
        self.acceleration_vector: Optional[list[float]] = None

        # --- Animation state ---
        self.running = False
        self.progress = 0.0
        self.base_step = 0.012
        self.speed_multiplier = 1.0
        self.profile = "linear"
        self.loop = False

        # --- Timing / FPS ---
        self._last_frame_time = time.perf_counter()
        self.fps = 0.0
        self.elapsed_time = 0.0
        self.iterations = 0

        # --- Telemetry ---
        self.telemetry_x, self.telemetry_y, self.telemetry_z = [], [], []
        self.telemetry_steps = []
        self._prev_position = None
        self._prev_prev_position = None

        # --- Trajectory & history ---
        self.trajectory_points: list[list[float]] = []
        self.motion_history: list[list[list[float]]] = []
        self.max_history = 8

        # --- Timer ---
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._advance_animation)

        # ====================================================
        # UI
        # ====================================================
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 1. Canvas
        self.canvas = AnimationCanvas()
        main_layout.addWidget(self.canvas, stretch=3)

        # 2. Telemetry
        self.telemetry_plot = pg.PlotWidget()
        self.telemetry_plot.setBackground("#1E293B")
        self.telemetry_plot.showGrid(x=True, y=True, alpha=0.3)
        self.telemetry_plot.setLabel("bottom", "Progress (%)")
        self.telemetry_plot.setLabel("left", "Coordinate")
        self.telemetry_plot.setTitle("Real-Time End-Effector Telemetry", color="white", size="10pt")
        self.telemetry_plot.addLegend()
        self.telemetry_plot.setMaximumHeight(120)
        self.telemetry_plot.setMinimumHeight(90)
        self.plot_x = self.telemetry_plot.plot(pen=pg.mkPen('#EF4444', width=2), name="X")
        self.plot_y = self.telemetry_plot.plot(pen=pg.mkPen('#22C55E', width=2), name="Y")
        self.plot_z = self.telemetry_plot.plot(pen=pg.mkPen('#3B82F6', width=2), name="Z")
        main_layout.addWidget(self.telemetry_plot, stretch=1)

        # 3. Timeline
        scrubber_frame = QFrame()
        scrubber_frame.setStyleSheet("QFrame { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; }")
        sl = QHBoxLayout(scrubber_frame)
        sl.setContentsMargins(10, 5, 10, 5)
        sl.addWidget(QLabel("<b>Timeline:</b>"))
        self.scrubber = QSlider(Qt.Orientation.Horizontal)
        self.scrubber.setRange(0, 1000)
        self.scrubber.sliderMoved.connect(self._on_scrub)
        sl.addWidget(self.scrubber, stretch=1)
        self.time_label = QLabel("0.00 / 0.00 s  (0.0%)")
        self.time_label.setStyleSheet("font-family: Consolas; font-size: 10px;")
        sl.addWidget(self.time_label)
        main_layout.addWidget(scrubber_frame)

        # 4a. PRIMARY control bar — always visible.
        #     Transport (Play/Pause/Stop/Loop) plus the two controls
        #     you're likely to touch mid-run (Profile, Speed), kept
        #     compact so they don't crowd the transport buttons.
        primary_ctrl = QFrame()
        primary_ctrl.setStyleSheet("QFrame { background-color: black; border: 1px solid #333; border-radius: 6px; }")
        pl = QHBoxLayout(primary_ctrl)
        pl.setContentsMargins(10, 6, 10, 6)
        pl.setSpacing(5)

        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn = QPushButton("Stop")
        self.loop_btn = QPushButton("Loop")
        self.loop_btn.setCheckable(True)
        self.more_controls_btn = QPushButton("More Controls  \u25be")
        self.more_controls_btn.setCheckable(True)

        for b in (self.play_btn, self.pause_btn, self.stop_btn, self.loop_btn, self.more_controls_btn):
            b.setMinimumHeight(30)
            b.setMinimumWidth(50)

        self.play_btn.setStyleSheet("QPushButton { background:#22C55E; color:black; border-radius:4px; font-weight:bold; }")
        self.pause_btn.setStyleSheet("QPushButton { background:#F59E0B; color:black; border-radius:4px; font-weight:bold; }")
        self.stop_btn.setStyleSheet("QPushButton { background:#EF4444; color:black; border-radius:4px; font-weight:bold; }")
        self.loop_btn.setStyleSheet("QPushButton { background:#64748B; color:white; border-radius:4px; } QPushButton:checked { background:#3B82F6; }")
        self.more_controls_btn.setStyleSheet(
            "QPushButton { background:#334155; color:white; border-radius:4px; font-weight:bold; padding: 0 10px; }"
            " QPushButton:checked { background:#475569; }"
        )
        self.more_controls_btn.setToolTip("Show/hide render mode, view toggles and export")

        # Compact Profile / Speed controls — small font + tight
        # padding so two extra dropdowns fit without crowding the
        # transport buttons.
        compact_combo_style = (
            "QComboBox { background:#222; color:white; border:1px solid #555;"
            " padding: 2px 4px; font-size: 10px; }"
            " QComboBox QAbstractItemView { background:white; color:black; font-size: 10px; }"
        )
        compact_label_style = "color:white; font-size: 10px;"

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Linear", "Cubic", "Quintic", "Smoothstep", "S-Curve"])
        self.profile_combo.setMinimumWidth(78)
        self.profile_combo.setMaximumHeight(24)
        self.profile_combo.setStyleSheet(compact_combo_style)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1x", "2x", "4x"])
        self.speed_combo.setCurrentIndex(2)
        self.speed_combo.setMinimumWidth(52)
        self.speed_combo.setMaximumHeight(24)
        self.speed_combo.setStyleSheet(compact_combo_style)

        profile_label = QLabel("Profile:")
        profile_label.setStyleSheet(compact_label_style)

        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet(compact_label_style)

        pl.addWidget(self.play_btn)
        pl.addWidget(self.pause_btn)
        pl.addWidget(self.stop_btn)
        pl.addWidget(self.loop_btn)
        pl.addStretch()
        pl.addWidget(profile_label)
        pl.addWidget(self.profile_combo)
        pl.addWidget(speed_label)
        pl.addWidget(self.speed_combo)
        pl.addSpacing(6)
        pl.addWidget(self.more_controls_btn)

        main_layout.addWidget(primary_ctrl)

        # 4b. SECONDARY control panel — collapsed by default.
        #     What's left: render mode, view toggles, and exports —
        #     things you set up once per session rather than every run.
        self.secondary_ctrl = QFrame()
        self.secondary_ctrl.setStyleSheet("QFrame { background-color: #1E293B; border: 1px solid #333; border-radius: 6px; }")
        sl2 = QHBoxLayout(self.secondary_ctrl)
        sl2.setContentsMargins(10, 8, 10, 8)
        sl2.setSpacing(5)

        self.render_combo = QComboBox()
        self.render_combo.addItems(["Solid", "Wireframe", "Simple"])
        self.render_combo.setMinimumWidth(90)
        self.render_combo.setStyleSheet("QComboBox { background:#222; color:white; border:1px solid #555; padding:4px; } QComboBox QAbstractItemView { background:white; color:black; }")

        self.export_csv_btn = QPushButton("CSV")
        self.export_pdf_btn = QPushButton("PDF")
        self.trail_btn = QPushButton("Traj")
        self.ghost_btn = QPushButton("Ghosts")
        self.frames_btn = QPushButton("Frames")

        self.trail_btn.setCheckable(True)
        self.ghost_btn.setCheckable(True)
        self.frames_btn.setCheckable(True)

        for b in (self.export_csv_btn, self.export_pdf_btn,
                  self.trail_btn, self.ghost_btn, self.frames_btn):
            b.setMinimumHeight(30)
            b.setMinimumWidth(50)

        self.export_csv_btn.setStyleSheet("QPushButton { background:#3B82F6; color:white; border-radius:4px; font-weight:bold; }")
        self.export_pdf_btn.setStyleSheet("QPushButton { background:#DC2626; color:white; border-radius:4px; font-weight:bold; }")
        self.trail_btn.setStyleSheet("QPushButton { background:#64748B; color:white; border-radius:4px; } QPushButton:checked { background:#10B981; }")
        self.ghost_btn.setStyleSheet("QPushButton { background:#64748B; color:white; border-radius:4px; } QPushButton:checked { background:#8B5CF6; }")
        self.frames_btn.setStyleSheet("QPushButton { background:#64748B; color:white; border-radius:4px; } QPushButton:checked { background:#EC4899; }")

        self.trail_btn.setToolTip("Show actual end-effector trajectory")
        self.ghost_btn.setToolTip("Show fading motion history")
        self.frames_btn.setToolTip("Show coordinate frames (World/Base/EE)")
        self.export_csv_btn.setToolTip("Export raw telemetry samples as CSV")
        self.export_pdf_btn.setToolTip("Export a summarized telemetry report as PDF")

        sl2.addWidget(QLabel("<b style='color:white'>Render:</b>"))
        sl2.addWidget(self.render_combo)
        sl2.addSpacing(8)
        sl2.addWidget(self.trail_btn)
        sl2.addWidget(self.ghost_btn)
        sl2.addWidget(self.frames_btn)
        sl2.addStretch()
        sl2.addWidget(self.export_csv_btn)
        sl2.addWidget(self.export_pdf_btn)

        self.secondary_ctrl.setVisible(False)

        main_layout.addWidget(self.secondary_ctrl)

        # --- Status bar ---
        self.status_bar = QLabel("■ SIMULATION STOPPED  |  FPS: 0  |  Δt: 0.000 s")
        self.status_bar.setStyleSheet(
            "QLabel { background:#0F172A; color:#E2E8F0; padding:6px; border-radius:4px; font-family: Consolas; font-size: 11px; }"
        )
        main_layout.addWidget(self.status_bar)

        # --- Signals ---
        self.play_btn.clicked.connect(self.play)
        self.pause_btn.clicked.connect(self.pause)
        self.stop_btn.clicked.connect(self.stop)
        self.profile_combo.currentTextChanged.connect(self._update_profile)
        self.speed_combo.currentTextChanged.connect(self._update_speed)
        self.render_combo.currentTextChanged.connect(self._update_render)
        self.loop_btn.toggled.connect(lambda v: setattr(self, 'loop', v))
        self.export_csv_btn.clicked.connect(self.export_telemetry_csv)
        self.export_pdf_btn.clicked.connect(self.export_telemetry_pdf)
        self.trail_btn.clicked.connect(lambda: self._toggle_canvas('show_trajectory', self.trail_btn))
        self.ghost_btn.clicked.connect(lambda: self._toggle_canvas('show_motion_history', self.ghost_btn))
        self.frames_btn.clicked.connect(lambda: self._toggle_canvas('show_frames', self.frames_btn))
        self.more_controls_btn.toggled.connect(self._toggle_secondary_controls)

        # Default toggles ON
        self.trail_btn.setChecked(True)
        self.frames_btn.setChecked(True)
        self.canvas.show_trajectory = True
        self.canvas.show_frames = True

        self.setMinimumSize(520, 660)

    # --------------------------------------------------------
    # Toggle helpers
    # --------------------------------------------------------
    def _toggle_canvas(self, attr: str, btn: QPushButton):
        setattr(self.canvas, attr, btn.isChecked())
        self.canvas.update()

    def _toggle_secondary_controls(self, checked: bool):
        self.secondary_ctrl.setVisible(checked)
        self.more_controls_btn.setText(
            "More Controls  \u25b4" if checked else "More Controls  \u25be"
        )

    def _update_profile(self, text: str):
        map_ = {"Linear": "linear", "Cubic": "cubic", "Quintic": "quintic", "Smoothstep": "smoothstep", "S-Curve": "s_curve"}
        self.profile = map_.get(text, "linear")

    def _update_speed(self, text: str):
        map_ = {"0.25x": 0.25, "0.5x": 0.5, "1x": 1.0, "2x": 2.0, "4x": 4.0}
        self.speed_multiplier = map_.get(text, 1.0)

    def _update_render(self, text: str):
        self.canvas.render_mode = text
        self.canvas.update()

    # --------------------------------------------------------
    # Scrubbing
    # --------------------------------------------------------
    def _on_scrub(self, value: int):
        self.progress = value / 1000.0
        t = self._apply_profile(self.progress)
        if self.position and self.transformed_position:
            self.current_position = self._interpolate(self.position, self.transformed_position, t)
            if self.original_joints and self.transformed_joints:
                self.current_joints = [self._interpolate(s, e, t) for s, e in zip(self.original_joints, self.transformed_joints)]
        self._update_matrix()
        self._sync_canvas()

    # --------------------------------------------------------
    # Profile application
    # --------------------------------------------------------
    def _apply_profile(self, t: float) -> float:
        fn = {
            "linear": InterpolationProfile.linear,
            "cubic": InterpolationProfile.cubic,
            "quintic": InterpolationProfile.quintic,
            "smoothstep": InterpolationProfile.smoothstep,
            "s_curve": InterpolationProfile.s_curve,
        }.get(self.profile, InterpolationProfile.linear)
        return fn(t)

    # --------------------------------------------------------
    # Matrix computation (from current position vs original)
    # --------------------------------------------------------
    def _update_matrix(self):
        """Build a homogeneous matrix representing current pose relative to original."""
        if not self.current_position or not self.position:
            self.current_matrix = None
            return
        dim = len(self.position)
        # Translation component
        tx = self.current_position[0] - self.position[0]
        ty = self.current_position[1] - self.position[1] if dim > 1 else 0.0
        tz = self.current_position[2] - self.position[2] if dim > 2 else 0.0
        # Identity + translation (simplified; real rotation needs FK)
        n = dim + 1
        mat = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        mat[0][-1] = tx
        if dim > 1: mat[1][-1] = ty
        if dim > 2: mat[2][-1] = tz
        self.current_matrix = mat

    # --------------------------------------------------------
    # Vertex matrix -> point list
    # --------------------------------------------------------
    @staticmethod
    def _matrix_to_points(matrix):
        """
        Convert a dimension x vertex_count matrix (rows = X, Y[, Z] —
        exactly what MainWindow.get_vertex_matrix() and
        RobotEngine.transform_vertices() return) into a list of
        [x, y(, z)] points, one per vertex.

        Returns None if the matrix is empty/missing so callers can
        fall back to older point-list-shaped data if present.
        """
        if not matrix:
            return None

        dimension = len(matrix)
        vertex_count = len(matrix[0]) if dimension else 0

        if vertex_count == 0:
            return None

        return [
            [float(matrix[row][col]) for row in range(dimension)]
            for col in range(vertex_count)
        ]

    # --------------------------------------------------------
    # Set robot
    # --------------------------------------------------------
    def set_robot(self, robot_definition) -> None:
        if not isinstance(robot_definition, dict):
            return
        self.robot_definition = robot_definition
        self.position = robot_definition.get("position")
        self.transformed_position = robot_definition.get("transformed_position")
        self.dimension = int(robot_definition.get("dimension", 2))

        # -------------------------------------------------
        # JOINT / VERTEX DATA
        #
        # MainWindow stores the full vertex set under
        # "vertices" / "transformed_vertices" as dimension x
        # vertex_count matrices (see get_vertex_matrix() and
        # RobotEngine.transform_vertices()). Convert those into
        # the point-list shape this canvas expects for
        # base/joints/links/end-effector rendering.
        #
        # "original_joints" / "transformed_joints" are kept as
        # a fallback for any caller that still passes an
        # already-list-of-points structure directly.
        # -------------------------------------------------

        vertex_points = self._matrix_to_points(
            robot_definition.get("vertices")
        )

        transformed_vertex_points = self._matrix_to_points(
            robot_definition.get("transformed_vertices")
        )

        self.original_joints = (
            vertex_points
            if vertex_points is not None
            else robot_definition.get("original_joints")
        )

        self.transformed_joints = (
            transformed_vertex_points
            if transformed_vertex_points is not None
            else robot_definition.get("transformed_joints")
        )

        self.timer.stop()
        self.running = False
        self.progress = 0.0
        self.elapsed_time = 0.0
        self.iterations = 0
        self.scrubber.setValue(0)
        self.current_position = list(self.position) if self.position else None
        self.current_joints = [list(j) for j in self.original_joints] if self.original_joints else None
        self.velocity_vector = None
        self.acceleration_vector = None
        self._prev_position = None
        self._prev_prev_position = None
        self.trajectory_points = []
        self.motion_history = []
        self.telemetry_x, self.telemetry_y, self.telemetry_z, self.telemetry_steps = [], [], [], []
        self.plot_x.setData([], []); self.plot_y.setData([], []); self.plot_z.setData([], [])
        self._update_matrix()
        self._sync_canvas()
        self._update_status("STOPPED")

    def _sync_canvas(self):
        self.canvas.position = self.position
        self.canvas.transformed_position = self.transformed_position
        self.canvas.current_position = self.current_position
        self.canvas.dimension = self.dimension
        self.canvas.original_joints = self.original_joints
        self.canvas.transformed_joints = self.transformed_joints
        self.canvas.current_joints = self.current_joints
        self.canvas.progress = self.progress
        self.canvas.current_matrix = self.current_matrix
        self.canvas.trajectory_points = self.trajectory_points
        self.canvas.motion_history = self.motion_history
        self.canvas.velocity_vector = self.velocity_vector
        self.canvas.acceleration_vector = self.acceleration_vector
        self.canvas.update()

    # --------------------------------------------------------
    # Playback
    # --------------------------------------------------------
    def play(self) -> None:
        if self.position is None or self.transformed_position is None:
            return
        if self.progress >= 1.0:
            self.progress = 0.0
            self.current_position = list(self.position)
            if self.original_joints:
                self.current_joints = [list(j) for j in self.original_joints]
            self.telemetry_x, self.telemetry_y, self.telemetry_z, self.telemetry_steps = [], [], [], []
            self.trajectory_points = []
            self.motion_history = []
            self._prev_position = None
            self._prev_prev_position = None
        if self.current_position is None:
            self.current_position = list(self.position)
        self.running = True
        self._last_frame_time = time.perf_counter()
        self.timer.start()
        self._update_status("RUNNING")

    def pause(self) -> None:
        self.running = False
        self.timer.stop()
        self._update_status("PAUSED")

    def stop(self) -> None:
        self.running = False
        self.timer.stop()
        self.progress = 0.0
        self.elapsed_time = 0.0
        self.iterations = 0
        self.scrubber.setValue(0)
        self.current_position = list(self.position) if self.position else None
        self.current_joints = [list(j) for j in self.original_joints] if self.original_joints else None
        self.velocity_vector = None
        self.acceleration_vector = None
        self.telemetry_x, self.telemetry_y, self.telemetry_z, self.telemetry_steps = [], [], [], []
        self.trajectory_points = []
        self.motion_history = []
        self._prev_position = None
        self._prev_prev_position = None
        self.plot_x.setData([], []); self.plot_y.setData([], []); self.plot_z.setData([], [])
        self._update_matrix()
        self._sync_canvas()
        self._update_status("STOPPED")

    # --------------------------------------------------------
    # Animation step
    # --------------------------------------------------------
    def _advance_animation(self) -> None:
        if not self.running:
            return
        if self.position is None or self.transformed_position is None:
            self.stop()
            return

        now = time.perf_counter()
        dt = now - self._last_frame_time
        self._last_frame_time = now
        self.fps = (0.9 * self.fps) + (0.1 * (1.0 / max(dt, 1e-6)))
        self.elapsed_time += dt
        self.iterations += 1

        self.progress += self.base_step * self.speed_multiplier
        if self.progress >= 1.0:
            self.progress = 1.0
            if self.loop:
                self.progress = 0.0
                self.trajectory_points = []
                self.motion_history = []
                self.telemetry_x, self.telemetry_y, self.telemetry_z, self.telemetry_steps = [], [], [], []
                self._prev_position = None
                self._prev_prev_position = None
            else:
                self.running = False
                self.timer.stop()
                self._update_status("STOPPED")

        self.scrubber.blockSignals(True)
        self.scrubber.setValue(int(self.progress * 1000))
        self.scrubber.blockSignals(False)

        t = self._apply_profile(self.progress)
        self.current_position = self._interpolate(self.position, self.transformed_position, t)
        if self.original_joints and self.transformed_joints:
            self.current_joints = [self._interpolate(s, e, t) for s, e in zip(self.original_joints, self.transformed_joints)]

        # Velocity (finite difference)
        if self._prev_position is not None and dt > 0:
            self.velocity_vector = [
                (self.current_position[i] - self._prev_position[i]) / dt
                for i in range(len(self.current_position))
            ]
        else:
            self.velocity_vector = [0.0] * len(self.current_position)

        # Acceleration
        if self._prev_prev_position is not None and self._prev_position is not None and dt > 0:
            self.acceleration_vector = [
                (self.current_position[i] - 2 * self._prev_position[i] + self._prev_prev_position[i]) / (dt * dt)
                for i in range(len(self.current_position))
            ]
        else:
            self.acceleration_vector = [0.0] * len(self.current_position)

        self._prev_prev_position = self._prev_position
        self._prev_position = list(self.current_position)

        # Trajectory
        if self.canvas.show_trajectory:
            self.trajectory_points.append(list(self.current_position))

        # Motion history
        if self.canvas.show_motion_history and self.current_joints:
            self.motion_history.append([list(j) for j in self.current_joints])
            if len(self.motion_history) > self.max_history:
                self.motion_history.pop(0)

        # Telemetry
        self.telemetry_steps.append(self.progress * 100)
        self.telemetry_x.append(self.current_position[0])
        self.telemetry_y.append(self.current_position[1] if len(self.current_position) > 1 else 0.0)
        self.telemetry_z.append(self.current_position[2] if len(self.current_position) > 2 else 0.0)
        self.plot_x.setData(self.telemetry_steps, self.telemetry_x)
        self.plot_y.setData(self.telemetry_steps, self.telemetry_y)
        self.plot_z.setData(self.telemetry_steps, self.telemetry_z)

        self._update_matrix()
        self._update_time_label()
        self._update_status("RUNNING")
        self._sync_canvas()
        self.progress_changed.emit(self.progress)

    # --------------------------------------------------------
    # Interpolation
    # --------------------------------------------------------
    @staticmethod
    def _interpolate(start, end, t):
        if start is None or end is None:
            return None
        if len(start) != len(end):
            return None
        t = max(0.0, min(1.0, float(t)))
        return [float(a) + (float(b) - float(a)) * t for a, b in zip(start, end)]

    # --------------------------------------------------------
    # Status / labels
    # --------------------------------------------------------
    def _update_status(self, state: str):
        icon = {"RUNNING": "●", "PAUSED": "Ⅱ", "STOPPED": "■"}.get(state, "■")
        color = {"RUNNING": "#22C55E", "PAUSED": "#F59E0B", "STOPPED": "#EF4444"}.get(state, "#94A3B8")
        self.status_bar.setText(
            f'<span style="color:{color};font-weight:bold">{icon} SIMULATION {state}</span>'
            f'  |  FPS: {self.fps:.0f}'
            f'  |  Δt: {1.0/max(self.fps,1):.4f} s'
            f'  |  Iterations: {self.iterations}'
        )

    def _update_time_label(self):
        total = 1.0 / self.base_step * 0.03  # approximate total duration in seconds
        self.time_label.setText(
            f"{self.elapsed_time:.2f} / {total:.2f} s  ({self.progress*100:.1f}%)"
        )

    # --------------------------------------------------------
    # Export — CSV
    # --------------------------------------------------------
    def export_telemetry_csv(self):
        if not self.telemetry_steps:
            QMessageBox.information(self, "Export", "No telemetry data. Run animation first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Telemetry CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(["Progress (%)", "Time (s)", "X", "Y", "Z", "Vx", "Vy", "Vz", "Ax", "Ay", "Az"])
            for i, prog in enumerate(self.telemetry_steps):
                x = self.telemetry_x[i] if i < len(self.telemetry_x) else 0
                y = self.telemetry_y[i] if i < len(self.telemetry_y) else 0
                z = self.telemetry_z[i] if i < len(self.telemetry_z) else 0
                # Velocity/acceleration approximated from telemetry
                vx = (self.telemetry_x[i] - self.telemetry_x[i-1]) / 0.03 if i > 0 else 0
                vy = (self.telemetry_y[i] - self.telemetry_y[i-1]) / 0.03 if i > 0 else 0
                vz = (self.telemetry_z[i] - self.telemetry_z[i-1]) / 0.03 if i > 0 else 0
                ax = (vx - ((self.telemetry_x[i-1] - self.telemetry_x[i-2]) / 0.03)) / 0.03 if i > 1 else 0
                ay = (vy - ((self.telemetry_y[i-1] - self.telemetry_y[i-2]) / 0.03)) / 0.03 if i > 1 else 0
                az = (vz - ((self.telemetry_z[i-1] - self.telemetry_z[i-2]) / 0.03)) / 0.03 if i > 1 else 0
                w.writerow([f"{prog:.2f}", f"{self.elapsed_time*prog/100:.4f}", f"{x:.4f}", f"{y:.4f}", f"{z:.4f}",
                            f"{vx:.4f}", f"{vy:.4f}", f"{vz:.4f}", f"{ax:.4f}", f"{ay:.4f}", f"{az:.4f}"])
        QMessageBox.information(self, "Success", f"Telemetry exported to:\n{path}")

    # --------------------------------------------------------
    # Export — PDF
    # --------------------------------------------------------
    def export_telemetry_pdf(self):
        """
        Export a summarized PDF report: run configuration, the
        final transformation matrix, and a downsampled telemetry
        table (raw CSV export stays available for full-resolution
        data).
        """
        if not self.telemetry_steps:
            QMessageBox.information(self, "Export", "No telemetry data. Run animation first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", "", "PDF Files (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            )
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
        except ImportError:
            QMessageBox.warning(
                self,
                "Missing Dependency",
                "PDF export requires the 'reportlab' package.\n"
                "Install it with: pip install reportlab",
            )
            return

        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("Robot Transformation Animation Report", styles["Title"]))
        story.append(Spacer(1, 12))

        vertex_count = len(self.original_joints) if self.original_joints else 1

        summary_lines = [
            f"Dimension: {self.dimension}D",
            f"Vertices tracked: {vertex_count}",
            f"Original base position: {self._format_point(self.position)}",
            f"Transformed base position: {self._format_point(self.transformed_position)}",
            f"Interpolation profile: {self.profile}",
            f"Recorded samples: {len(self.telemetry_steps)}",
        ]

        for line in summary_lines:
            story.append(Paragraph(line, styles["Normal"]))

        story.append(Spacer(1, 16))
        story.append(Paragraph("End-Effector Telemetry (downsampled)", styles["Heading2"]))
        story.append(Spacer(1, 6))

        # Downsample so the table stays a reasonable length in the PDF
        max_rows = 40
        step = max(1, len(self.telemetry_steps) // max_rows)

        table_data = [["Progress (%)", "X", "Y", "Z"]]

        for i in range(0, len(self.telemetry_steps), step):
            table_data.append([
                f"{self.telemetry_steps[i]:.1f}",
                f"{self.telemetry_x[i]:.4f}",
                f"{self.telemetry_y[i]:.4f}" if i < len(self.telemetry_y) else "-",
                f"{self.telemetry_z[i]:.4f}" if i < len(self.telemetry_z) else "-",
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
        ]))

        story.append(table)

        if len(self.telemetry_steps) > max_rows:
            story.append(Spacer(1, 8))
            story.append(Paragraph(
                f"Note: showing every {step} sample(s) of "
                f"{len(self.telemetry_steps)} total. Use the CSV export "
                "for the full-resolution dataset.",
                styles["Italic"],
            ))

        doc.build(story)

        QMessageBox.information(self, "Success", f"PDF report exported to:\n{path}")

    @staticmethod
    def _format_point(point):
        if point is None:
            return "None"
        try:
            return "[ " + ", ".join(f"{float(v):.3f}" for v in point) + " ]"
        except (TypeError, ValueError):
            return str(point)

    # --------------------------------------------------------
    # Keyboard
    # --------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            self.play() if not self.running else self.pause()
        elif event.key() == Qt.Key.Key_Escape:
            self.stop()
        elif event.key() == Qt.Key.Key_Right:
            self._on_scrub(min(1000, self.scrubber.value() + 10))
        elif event.key() == Qt.Key.Key_Left:
            self._on_scrub(max(0, self.scrubber.value() - 10))
        super().keyPressEvent(event)

    # --------------------------------------------------------
    # Clear
    # --------------------------------------------------------
    def clear(self) -> None:
        self.stop()
        self.robot_definition = None
        self.position = None
        self.transformed_position = None
        self.current_position = None
        self.dimension = 2
        self.original_joints = None
        self.transformed_joints = None
        self.current_joints = None
        self.velocity_vector = None
        self.acceleration_vector = None
        self._sync_canvas()
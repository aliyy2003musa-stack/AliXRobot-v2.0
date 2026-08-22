"""
AliXRobot 2D Visualization (v2.0)
PyQtGraph-based 2D robot visualization.
The view does not perform mathematical transformations.
It only visualizes results produced by RobotEngine and Geometry.
"""
from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)
import pyqtgraph as pg
import pyqtgraph.exporters


class View2D(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # =================================================
        # DATA
        # =================================================
        self.original_position = None
        self.transformed_position = None
        self.transformation_matrix = None
        self.translation = None
        self.rotation_degrees = None
        self.scaling_factor = None
        
        # NEW v2.0: Joint data for full robot visualization
        self.original_joints = None
        self.transformed_joints = None
        self.workspace_points = None

        # =================================================
        # PLOT WIDGET
        # =================================================
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setLabel("left", "Y")
        self.plot_widget.setLabel("bottom", "X")
        self.plot_widget.setTitle("2D Robot Transformation", color="k", size="14pt")
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.addLegend()

        # =================================================
        # WORKSPACE PLOT (NEW v2.0)
        # Drawn first so it stays in the background
        # =================================================
        self.workspace_plot = pg.ScatterPlotItem(
            size=4,
            pen=pg.mkPen(None),
            brush=pg.mkBrush(200, 200, 200, 100), # Light gray, semi-transparent
            name="Workspace",
        )
        self.workspace_plot.setVisible(False) # Hidden by default

        # =================================================
        # ROBOT LINKS (NEW v2.0)
        # These represent the physical arms/links of the robot.
        # =================================================
        self.original_link_plot = pg.PlotDataItem(
            pen=pg.mkPen('r', width=4)
        )
        self.transformed_link_plot = pg.PlotDataItem(
            pen=pg.mkPen('b', width=4)
        )

        # =================================================
        # ORIGINAL POINT (Standardized to Red)
        # =================================================
        self.original_plot = pg.ScatterPlotItem(
            size=14,
            pen=pg.mkPen(width=2),
            brush=pg.mkBrush(220, 50, 50),
            name="Original",
        )
        
        # =================================================
        # TRANSFORMED POINT (Standardized to Blue)
        # =================================================
        self.transformed_plot = pg.ScatterPlotItem(
            size=16,
            pen=pg.mkPen(width=2),
            brush=pg.mkBrush(0, 100, 255),
            name="Transformed",
        )
        
        # =================================================
        # TRANSFORMATION LINE
        # =================================================
        self.transformation_line = pg.PlotDataItem(
            pen=pg.mkPen(width=2, style=Qt.PenStyle.DashLine)
        )
        
        # =================================================
        # AXES & ORIGIN
        # =================================================
        self.x_axis = pg.PlotDataItem(pen=pg.mkPen(width=1))
        self.y_axis = pg.PlotDataItem(pen=pg.mkPen(width=1))
        self.origin_plot = pg.ScatterPlotItem(
            size=8,
            pen=pg.mkPen(width=1),
            brush=pg.mkBrush(0, 0, 0),
        )

        # =================================================
        # ADD ITEMS (Order matters for z-index)
        # =================================================
        self.plot_widget.addItem(self.x_axis)
        self.plot_widget.addItem(self.y_axis)
        self.plot_widget.addItem(self.origin_plot)
        self.plot_widget.addItem(self.workspace_plot)
        self.plot_widget.addItem(self.transformation_line)
        self.plot_widget.addItem(self.original_link_plot)
        self.plot_widget.addItem(self.transformed_link_plot)
        self.plot_widget.addItem(self.original_plot)
        self.plot_widget.addItem(self.transformed_plot)

        # =================================================
        # STATUS LABEL
        # =================================================
        self.status_label = QLabel("No robot data")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            """
            QLabel {
                padding: 6px;
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                color: #334155;
            }
            """
        )

        # =================================================
        # BUTTONS (NEW v2.0: Added Save Image & Workspace)
        # =================================================
        self.clear_button = QPushButton("Clear")
        self.reset_button = QPushButton("Reset View")
        self.workspace_button = QPushButton("Toggle Workspace")
        self.save_image_button = QPushButton("Save Image")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.workspace_button)
        button_layout.addWidget(self.save_image_button)

        # =================================================
        # MAIN LAYOUT
        # =================================================
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget, 1)
        layout.addWidget(self.status_label)
        layout.addLayout(button_layout)

        # =================================================
        # SIGNALS
        # =================================================
        self.clear_button.clicked.connect(self.clear)
        self.reset_button.clicked.connect(self.reset_view)
        self.workspace_button.clicked.connect(self.toggle_workspace)
        self.save_image_button.clicked.connect(self.save_plot_image)

        # =================================================
        # INITIAL DRAW
        # =================================================
        self.draw_axes()

    # =====================================================
    # DRAW AXES
    # =====================================================
    def draw_axes(self, length=10):
        self.x_axis.setData([-length, length], [0, 0])
        self.y_axis.setData([0, 0], [-length, length])
        self.origin_plot.setData([0], [0])

    # =====================================================
    # UPDATE ROBOT (UPDATED v2.0)
    # =====================================================
    def update_robot(
        self,
        position,
        transformed_position,
        translation=None,
        rotation_degrees=None,
        scaling_factor=None,
        transformation_matrix=None,
        original_joints=None,
        transformed_joints=None,
        workspace_points=None,
        **kwargs, # Catches any extra arguments safely
    ):
        """
        Receive calculated data from MainWindow.
        """
        if position is None or transformed_position is None:
            return
        if len(position) < 2 or len(transformed_position) < 2:
            return

        # =================================================
        # STORE DATA
        # =================================================
        x1, y1 = float(position[0]), float(position[1])
        x2, y2 = float(transformed_position[0]), float(transformed_position[1])
        
        self.original_position = (x1, y1)
        self.transformed_position = (x2, y2)
        self.translation = translation
        self.rotation_degrees = rotation_degrees
        self.scaling_factor = scaling_factor
        self.transformation_matrix = transformation_matrix
        
        # NEW v2.0: Store joint and workspace data
        self.original_joints = original_joints
        self.transformed_joints = transformed_joints
        self.workspace_points = workspace_points

        # =================================================
        # DRAW WORKSPACE (NEW v2.0)
        # =================================================
        if workspace_points:
            wx = [p[0] for p in workspace_points]
            wy = [p[1] for p in workspace_points]
            self.workspace_plot.setData(wx, wy)
            self.workspace_plot.setVisible(True)
        else:
            self.workspace_plot.setData([], [])
            self.workspace_plot.setVisible(False)

        # =================================================
        # DRAW LINKS (NEW v2.0)
        # =================================================
        self._draw_links()

        # =================================================
        # DRAW POINTS & LINE
        # =================================================
        self.original_plot.setData([x1], [y1])
        self.transformed_plot.setData([x2], [y2])
        self.transformation_line.setData([x1, x2], [y1, y2])

        # =================================================
        # AXES SCALING
        # =================================================
        maximum = max(abs(x1), abs(y1), abs(x2), abs(y2), 1.0)
        if original_joints:
            for j in original_joints: maximum = max(maximum, abs(j[0]), abs(j[1]))
        if transformed_joints:
            for j in transformed_joints: maximum = max(maximum, abs(j[0]), abs(j[1]))
            
        axis_length = max(10.0, maximum * 1.5)
        self.draw_axes(axis_length)

        # =================================================
        # STATUS
        # =================================================
        self.status_label.setText(
            f"Original: ({x1:.3f}, {y1:.3f})    |    "
            f"Transformed: ({x2:.3f}, {y2:.3f})"
        )
        
        # =================================================
        # AUTO RANGE
        # =================================================
        self.plot_widget.enableAutoRange(axis="xy", enable=True)
        self.plot_widget.autoRange()

    # =====================================================
    # NEW v2.0: DRAW LINKS
    # =====================================================
    def _draw_links(self):
        """Draw the physical links connecting the joints."""
        self.original_link_plot.setData([], [])
        self.transformed_link_plot.setData([], [])
        
        if self.original_joints and len(self.original_joints) > 1:
            x = [j[0] for j in self.original_joints]
            y = [j[1] for j in self.original_joints]
            self.original_link_plot.setData(x, y)
            
        if self.transformed_joints and len(self.transformed_joints) > 1:
            x = [j[0] for j in self.transformed_joints]
            y = [j[1] for j in self.transformed_joints]
            self.transformed_link_plot.setData(x, y)

    # =====================================================
    # NEW v2.0: TOGGLE WORKSPACE
    # =====================================================
    def toggle_workspace(self):
        """Toggle the visibility of the workspace point cloud."""
        if self.workspace_plot.isVisible():
            self.workspace_plot.setVisible(False)
        else:
            if self.workspace_points:
                self.workspace_plot.setVisible(True)

    # =====================================================
    # NEW v2.0: SAVE IMAGE
    # =====================================================
    def save_plot_image(self):
        """Export the current plot as a high-resolution PNG."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot Image", "", "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            exporter = pyqtgraph.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.export(file_path)

    # =====================================================
    # SET POSITIONS (Legacy Compatibility)
    # =====================================================
    def set_positions(self, position, transformed_position):
        self.update_robot(position=position, transformed_position=transformed_position)

    # =====================================================
    # CLEAR
    # =====================================================
    def clear(self):
        self.original_plot.clear()
        self.transformed_plot.clear()
        self.transformation_line.clear()
        self.original_link_plot.setData([], [])
        self.transformed_link_plot.setData([], [])
        self.workspace_plot.setData([], [])
        self.workspace_plot.setVisible(False)
        
        self.original_position = None
        self.transformed_position = None
        self.transformation_matrix = None
        self.translation = None
        self.rotation_degrees = None
        self.scaling_factor = None
        self.original_joints = None
        self.transformed_joints = None
        self.workspace_points = None
        
        self.status_label.setText("No robot data")
        self.draw_axes()

    # =====================================================
    # RESET VIEW
    # =====================================================
    def reset_view(self):
        self.plot_widget.enableAutoRange(axis="xy", enable=True)
        self.plot_widget.autoRange()
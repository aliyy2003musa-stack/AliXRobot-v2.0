import sys
import os
import ast
import csv
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QCursor, QTextDocument
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt6.QtPrintSupport import QPrinter

from robotEngine import RobotEngine
from visualization.geometry import generate_workspace_grid
from visualization import (
    View2D,
    View3D,
    RobotAnimation,
)
from _user_guide_content import USER_GUIDE_HTML


# =========================================================
# HELPER FUNCTION FOR RESOURCE PATHS
# =========================================================
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# =========================================================
# USER GUIDE DIALOG
# =========================================================
class UserGuideDialog(QDialog):
    """A professional, scrollable in-app user guide."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AliXRobot v2.0 - User Guide")
        self.resize(900, 700)
        self.setStyleSheet("QDialog { background-color: #0B0F19; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Text Browser for rich HTML content
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(False)
        self.text_browser.setHtml(USER_GUIDE_HTML)
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #000000;
                border: 1px solid #1E293B;
                border-radius: 6px;
                padding: 15px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.text_browser)
        
        # Button layout
        btn_layout = QHBoxLayout()
        
        # Download PDF button
        self.pdf_btn = QPushButton("📥 Download Guide as PDF")
        self.pdf_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626; color: white; border: none; 
                border-radius: 6px; padding: 10px 20px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        self.pdf_btn.clicked.connect(self.download_pdf)
        btn_layout.addWidget(self.pdf_btn)
        
        btn_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close Guide")
        close_btn.setMinimumHeight(40)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #475569; color: white; border: none; 
                border-radius: 6px; padding: 10px 20px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #334155; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def download_pdf(self):
        """Download the guide as a PDF file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save User Guide", "AliXRobot_User_Guide.pdf", "PDF Files (*.pdf)"
        )
        if file_path:
            try:
                doc = QTextDocument()
                doc.setHtml(USER_GUIDE_HTML)
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)
                doc.print(printer)
                
                QMessageBox.information(
                    self, "Success", 
                    f"User Guide downloaded successfully!\n\nSaved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export PDF:\n{str(e)}"
                )


# =========================================================
# MAIN WINDOW
# =========================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # =================================================
        # ENGINE
        # =================================================
        self.engine = RobotEngine()

        # =================================================
        # WINDOW
        # =================================================
        self.setWindowTitle("AliXRobot v2.0")
        self.resize(1250, 750)
        self.setMinimumSize(1000, 650)

        # =================================================
        # ICON
        # =================================================
        try:
            icon_path = get_resource_path("robot_icon.png")
            self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        # =================================================
        # DATA
        # =================================================
        self.combination_results = {}
        self.robot_definition = {}
        self._updating_transformations = False
        self._syncing_position = False

        # =================================================
        # BUILD UI
        # =================================================
        self.setup_ui()

    # =====================================================
    # GENERAL UI HELPERS
    # =====================================================
    @staticmethod
    def heading(text):
        label = QLabel(text)
        label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 7px;
                background-color: #E2E8F0;
                border: 1px solid #CBD5E1;
                color: black;
                border-radius: 10px;
            }
            """
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    # =====================================================
    # VISUALIZATION BUTTON
    # =====================================================
    @staticmethod
    def visualization_button(text):
        button = QPushButton(text)
        button.setMinimumHeight(38)
        button.setStyleSheet(
            """
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 6px 14px;
                font-weight: bold;
                color: #1E293B;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
            QPushButton:pressed {
                background-color: #CBD5E1;
            }
            """
        )
        return button

    # =====================================================
    # SETUP UI
    # =====================================================
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # =================================================
        # PARAMETERS PANEL
        # =================================================
        parameters_panel = QWidget()
        parameters_layout = QVBoxLayout(parameters_panel)
        parameters_layout.setContentsMargins(8, 8, 8, 8)
        parameters_layout.addWidget(self.heading("Robot Parameters"))

        # =================================================
        # DIMENSION
        # =================================================
        self.Dim2 = QRadioButton("2D")
        self.Dim3 = QRadioButton("3D")
        self.Dim2.setChecked(True)
        self.dimension_group = QButtonGroup(self)
        self.dimension_group.addButton(self.Dim2)
        self.dimension_group.addButton(self.Dim3)
        dimension_layout = QHBoxLayout()
        dimension_layout.addWidget(self.Dim2)
        dimension_layout.addWidget(self.Dim3)
        dimension_layout.addStretch()

        # =================================================
        # TRANSFORMATIONS
        # =================================================
        self.translation_button = QCheckBox("Translation")
        self.rotation_checkbox = QCheckBox("Rotation")
        self.scaling_checkbox = QCheckBox("Scaling")
        transform_layout = QVBoxLayout()
        transform_layout.addWidget(self.translation_button)
        transform_layout.addWidget(self.rotation_checkbox)
        transform_layout.addWidget(self.scaling_checkbox)

        # =======================================
        # NUMBER OF ROBOT VERTICES
        # ========================================
        self.robot_vertices = QLineEdit()
        self.robot_vertices.setPlaceholderText("e.g whole numbers: 1 or 2 or 3")
        self.robot_vertices.setMinimumSize(QSize(200, 34))
        self.table = QTableWidget()
        self.table.setMaximumHeight(200)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 60)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.itemChanged.connect(self.sync_table_to_lineedit)
        self.robot_vertices.textChanged.connect(self.update_vertex_table)
        self.Dim2.toggled.connect(self.update_vertex_table)
        self.Dim3.toggled.connect(self.update_vertex_table)

        # =================================================
        # INITIAL POSITION
        # =================================================
        self.robot_ini_posi_box = QLineEdit()
        self.robot_ini_posi_box.setMinimumSize(QSize(200, 34))
        self.robot_ini_posi_box.editingFinished.connect(self.apply_lineedit_to_table)

        # =================================================
        # ROBOT TYPE
        # =================================================
        self.robot_type_combo = QComboBox()
        self.robot_type_combo.addItems([
            "Articulated",
            "SCARA",
            "Cartesian",
            "Delta",
            "Cylindrical",
        ])

        # =================================================
        # DOF
        # =================================================
        self.dof_spin = QSpinBox()
        self.dof_spin.setRange(1, 20)
        self.dof_spin.setValue(6)

        # =================================================
        # VELOCITY
        # =================================================
        self.velocity_input = QLineEdit()
        self.velocity_input.setPlaceholderText("e.g., 1.5")

        # =================================================
        # ACCELERATION
        # =================================================
        self.accel_input = QLineEdit()
        self.accel_input.setPlaceholderText("e.g., 2.0")

        # =================================================
        # INERTIA
        # =================================================
        self.inertia_input = QLineEdit()
        self.inertia_input.setPlaceholderText("e.g., [[1, 0], [0, 1]]")

        # =================================================
        # PID
        # =================================================
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("e.g., [1.0, 0.1, 0.01]")

        # =================================================
        # FORM
        # =================================================
        form = QFormLayout()
        form.addRow("Select robot dimension", dimension_layout)
        form.addRow("Transformations", transform_layout)
        form.addRow("Number of vertices", self.robot_vertices)
        form.addRow("Initial position", self.robot_ini_posi_box)
        form.addRow("Robot type", self.robot_type_combo)
        form.addRow("Degrees of freedom", self.dof_spin)
        form.addRow("Velocity (m/s)", self.velocity_input)
        form.addRow("Acceleration (m/s²)", self.accel_input)
        form.addRow("Inertia matrix", self.inertia_input)
        form.addRow("PID gains [Kp, Ki, Kd]", self.pid_input)
        parameters_layout.addLayout(form)
        parameters_layout.addWidget(self.table)

        # =================================================
        # ACTION BUTTONS
        # =================================================
        self.combination_button = QPushButton("Calculate Transformation Combination (TRS)")
        self.combination_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_transformations_button = QPushButton("Clear Transformations")
        self.clear_transformations_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.define_button = QPushButton("Define Robot")
        self.define_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        parameters_layout.addWidget(self.combination_button)
        parameters_layout.addWidget(self.clear_transformations_button)
        parameters_layout.addWidget(self.define_button)
        parameters_layout.addStretch()

        # =================================================
        # GRAPH PANEL
        # =================================================
        graph_panel = QWidget()
        graph_layout = QVBoxLayout(graph_panel)
        graph_layout.setContentsMargins(8, 8, 8, 8)
        graph_layout.addWidget(self.heading("Graphical Representation"))

        # =================================================
        # VISUALIZATION NAVIGATION
        # =================================================
        visualization_controls = QHBoxLayout()
        self.view_2d_button = self.visualization_button("2D View")
        self.view_3d_button = self.visualization_button("3D View")
        self.animation_button = self.visualization_button("Animation")
        visualization_controls.addWidget(self.view_2d_button)
        visualization_controls.addWidget(self.view_3d_button)
        visualization_controls.addWidget(self.animation_button)
        graph_layout.addLayout(visualization_controls)

        # =================================================
        # VISUALIZATION STACK
        # =================================================
        self.visualization_stack = QStackedWidget()
        self.visualization_stack.setMinimumSize(400, 350)

        # =================================================
        # CREATE VISUALIZATION WIDGETS
        # =================================================
        self.view_2d = View2D(parent=self.visualization_stack)
        self.view_3d = View3D(parent=self.visualization_stack)
        self.robot_animation = RobotAnimation(parent=self.visualization_stack)

        # =================================================
        # ADD TO STACK
        # =================================================
        self.visualization_stack.addWidget(self.view_2d)
        self.visualization_stack.addWidget(self.view_3d)
        self.visualization_stack.addWidget(self.robot_animation)

        # =================================================
        # BUTTON CONNECTIONS
        # =================================================
        self.view_2d_button.clicked.connect(self.show_2d_view)
        self.view_3d_button.clicked.connect(self.show_3d_view)
        self.animation_button.clicked.connect(self.show_animation_view)

        # =================================================
        # DEFAULT VISUALIZATION
        # =================================================
        self.visualization_stack.setCurrentWidget(self.view_2d)

        # =================================================
        # ADD STACK
        # =================================================
        graph_layout.addWidget(self.visualization_stack, 1)

        # =================================================
        # DETAILS PANEL
        # =================================================
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(8, 8, 8, 8)
        details_layout.addWidget(self.heading("Robot Information"))
        self.robot_attributes = QTextEdit()
        self.robot_attributes.setReadOnly(True)
        details_layout.addWidget(self.robot_attributes, 1)

        # NEW: Help / User Guide Button
        self.help_button = QPushButton("❓ Help / User Guide")
        self.help_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.help_button.setStyleSheet("""
            QPushButton { 
                background-color: #3B82F6; color: white; border-radius: 6px; 
                padding: 10px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.help_button.clicked.connect(self.show_user_guide)
        details_layout.addWidget(self.help_button)

        # NEW v2.0: Export Buttons
        export_layout = QHBoxLayout()
        self.export_pdf_button = QPushButton("Export PDF Report")
        self.export_csv_button = QPushButton("Export CSV Data")
        self.export_pdf_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.export_csv_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        self.export_pdf_button.setStyleSheet("""
            QPushButton { background-color: #DC2626; color: white; border-radius: 6px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        self.export_csv_button.setStyleSheet("""
            QPushButton { background-color: #16A34A; color: white; border-radius: 6px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #15803D; }
        """)
        
        export_layout.addWidget(self.export_pdf_button)
        export_layout.addWidget(self.export_csv_button)
        details_layout.addLayout(export_layout)

        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.export_csv_button.clicked.connect(self.export_to_csv)

        # =================================================
        # SPLITTER
        # =================================================
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(parameters_panel)
        splitter.addWidget(graph_panel)
        splitter.addWidget(details_panel)
        splitter.setSizes([330, 500, 330])

        # =================================================
        # OUTER LAYOUT
        # =================================================
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(splitter)

        # =================================================
        # SIGNALS
        # =================================================
        self.Dim2.toggled.connect(self.update_position_coordinate)
        self.Dim3.toggled.connect(self.update_position_coordinate)
        self.translation_button.toggled.connect(self.handle_translation_toggle)
        self.rotation_checkbox.toggled.connect(self.handle_rotation_toggle)
        self.scaling_checkbox.toggled.connect(self.handle_scaling_toggle)
        self.combination_button.clicked.connect(self.ask_combination)
        self.clear_transformations_button.clicked.connect(self.clear_transformations)
        self.define_button.clicked.connect(self.build_robot_definition)

        # =================================================
        # INITIAL STATE
        # =================================================
        self.update_position_coordinate()
        self.refresh_transformation_display()

    # =====================================================
    # SHOW USER GUIDE
    # =====================================================
    def show_user_guide(self):
        """Opens the in-app User Guide dialog."""
        dialog = UserGuideDialog(self)
        dialog.exec()

    # =====================================================
    # VISUALIZATION SWITCHING
    # =====================================================
    def show_2d_view(self):
        self.visualization_stack.setCurrentWidget(self.view_2d)
        self._update_visualization_button_state(self.view_2d_button)

    def show_3d_view(self):
        self.visualization_stack.setCurrentWidget(self.view_3d)
        self._update_visualization_button_state(self.view_3d_button)

    def show_animation_view(self) -> None:
        """Open the animation page and begin animating the current robot."""
        self.visualization_stack.setCurrentWidget(self.robot_animation)
        if self.robot_definition:
            self.robot_animation.set_robot(self.robot_definition)
        self.robot_animation.play()
        self._update_visualization_button_state(self.animation_button)

    def _update_visualization_button_state(self, active_button):
        buttons = [
            self.view_2d_button,
            self.view_3d_button,
            self.animation_button,
        ]
        for button in buttons:
            if button is active_button:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #2563EB;
                        color: white;
                        border: 1px solid #1D4ED8;
                        border-radius: 8px;
                        padding: 6px 14px;
                        font-weight: bold;
                    }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #F1F5F9;
                        color: #1E293B;
                        border: 1px solid #CBD5E1;
                        border-radius: 8px;
                        padding: 6px 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #E2E8F0;
                    }
                """)

    # =====================================================
    # DIMENSION / VISUALIZATION SWITCHING
    # =====================================================
    def update_position_coordinate(self, _checked=False):
        if self.Dim2.isChecked():
            self.robot_ini_posi_box.setPlaceholderText(
                "Input robot position: [x, y] or [[x,y],[x,y],...]"
            )
        else:
            self.robot_ini_posi_box.setPlaceholderText(
                "Input robot position: [x, y, z] or [[x,y,z],[x,y,z],...]"
            )

    # =====================================================
    # TRANSLATION TOGGLE
    # =====================================================
    def handle_translation_toggle(self, checked):
        if self._updating_transformations:
            return
        if checked:
            if not self.ask_translation():
                self._uncheck_transformation(self.translation_button)
        else:
            self.combination_results.pop("Translation vector", None)
            self.refresh_transformation_display()

    # =====================================================
    # ROTATION TOGGLE
    # =====================================================
    def handle_rotation_toggle(self, checked):
        if self._updating_transformations:
            return
        if checked:
            if not self.ask_rotation():
                self._uncheck_transformation(self.rotation_checkbox)
        else:
            self.combination_results.pop("Rotation angle", None)
            self.combination_results.pop("Rotation axis", None)
            self.refresh_transformation_display()

    # =====================================================
    # SCALING TOGGLE
    # =====================================================
    def handle_scaling_toggle(self, checked):
        if self._updating_transformations:
            return
        if checked:
            if not self.ask_scaling():
                self._uncheck_transformation(self.scaling_checkbox)
        else:
            self.combination_results.pop("Scaling factor", None)
            self.refresh_transformation_display()

    # =====================================================
    # SAFE UNCHECK
    # =====================================================
    def _uncheck_transformation(self, checkbox):
        self._updating_transformations = True
        checkbox.setChecked(False)
        self._updating_transformations = False

    # =====================================================
    # TRANSLATION
    # =====================================================
    def ask_translation(self):
        dimension = 2 if self.Dim2.isChecked() else 3
        default = "[0, 0]" if dimension == 2 else "[0, 0, 0]"
        current_value = self.combination_results.get("Translation vector", default)
        value, ok = QInputDialog.getText(
            self,
            "Translation",
            f"Enter translation vector\nExample: {default}",
            text=str(current_value),
        )
        if not ok:
            return False
        value = value.strip()
        if not value:
            QMessageBox.warning(self, "Invalid Translation", "Translation vector cannot be empty.")
            return False
        try:
            self.engine.parse_position(value, dimension)
        except ValueError as error:
            QMessageBox.warning(self, "Invalid Translation", str(error))
            return False
        self.combination_results["Translation vector"] = value
        self.refresh_transformation_display()
        return True

    # =====================================================
    # ROTATION
    # =====================================================
    def ask_rotation(self):
        current_angle = self.combination_results.get("Rotation angle", "")
        value, ok = QInputDialog.getText(
            self,
            "Rotation",
            "Enter rotation angle (degrees):",
            text=str(current_angle),
        )
        if not ok:
            return False
        value = value.strip()
        if not value:
            QMessageBox.warning(self, "Invalid Rotation", "Rotation angle cannot be empty.")
            return False
        try:
            float(value)
        except ValueError:
            QMessageBox.warning(self, "Invalid Rotation", "Please enter a valid numerical angle.")
            return False
        self.combination_results["Rotation angle"] = value

        # =================================================
        # 3D AXIS
        # =================================================
        if self.Dim3.isChecked():
            current_axis = self.combination_results.get("Rotation axis", "z")
            axes = ["x", "y", "z"]
            current_index = axes.index(current_axis) if current_axis in axes else 2
            axis, ok = QInputDialog.getItem(
                self,
                "Rotation Axis",
                "Select rotation axis:",
                axes,
                current_index,
                False,
            )
            if not ok:
                return False
            self.combination_results["Rotation axis"] = axis
        else:
            self.combination_results["Rotation axis"] = "z"
        self.refresh_transformation_display()
        return True

    # =====================================================
    # SCALING
    # =====================================================
    def ask_scaling(self):
        current_value = self.combination_results.get("Scaling factor", "1.0")
        value, ok = QInputDialog.getText(
            self,
            "Scaling",
            "Enter scaling factor (e.g., 1.5):",
            text=str(current_value),
        )
        if not ok:
            return False
        value = value.strip()
        if not value:
            QMessageBox.warning(self, "Invalid Scaling", "Scaling factor cannot be empty.")
            return False
        try:
            float(value)
        except ValueError:
            QMessageBox.warning(self, "Invalid Scaling", "Please enter a valid numerical scaling factor.")
            return False
        self.combination_results["Scaling factor"] = value
        self.refresh_transformation_display()
        return True

    # =====================================================
    # COMBINATION
    # =====================================================
    def ask_combination(self):
        if not self.get_active_transformations():
            QMessageBox.information(self, "No Transformations", "Please select at least one transformation.")
            return
        if self.translation_button.isChecked():
            if not self.ask_translation():
                return
        if self.rotation_checkbox.isChecked():
            if not self.ask_rotation():
                return
        if self.scaling_checkbox.isChecked():
            if not self.ask_scaling():
                return
        self.refresh_transformation_display()

    # =====================================================
    # ACTIVE TRANSFORMATIONS
    # =====================================================
    def get_active_transformations(self):
        active = []
        if self.translation_button.isChecked():
            active.append("Translation")
        if self.rotation_checkbox.isChecked():
            active.append("Rotation")
        if self.scaling_checkbox.isChecked():
            active.append("Scaling")
        return active

    # =====================================================
    # CLEAR TRANSFORMATIONS
    # =====================================================
    def clear_transformations(self):
        self._updating_transformations = True
        self.translation_button.setChecked(False)
        self.rotation_checkbox.setChecked(False)
        self.scaling_checkbox.setChecked(False)
        self._updating_transformations = False
        self.combination_results.clear()
        self.robot_definition = {}

        # =================================================
        # CLEAR VISUALIZATIONS
        # =================================================
        self.view_2d.clear()
        self.view_3d.clear()
        self.robot_animation.clear()
        self.refresh_transformation_display()
        self.show_2d_view()

    # =====================================================
    # REFRESH DISPLAY
    # =====================================================
    def refresh_transformation_display(self):
        lines = []
        lines.append("TRANSFORMATION SETTINGS")
        lines.append("=" * 40)
        active = self.get_active_transformations()
        if not active:
            lines.append("No transformations selected.")
        else:
            lines.append("Active transformations:")
            for transformation in active:
                lines.append(f"  • {transformation}")
            lines.append("")
            lines.append("Parameters:")
            if "Translation vector" in self.combination_results:
                lines.append("  Translation vector: " + str(self.combination_results["Translation vector"]))
            if "Rotation angle" in self.combination_results:
                lines.append("  Rotation angle: " + str(self.combination_results["Rotation angle"]) + " degrees")
            if "Rotation axis" in self.combination_results:
                lines.append("  Rotation axis: " + str(self.combination_results["Rotation axis"]))
            if "Scaling factor" in self.combination_results:
                lines.append("  Scaling factor: " + str(self.combination_results["Scaling factor"]))
        self.robot_attributes.setPlainText("\n".join(lines))

    # =====================================================
    # VECTOR FORMAT
    # =====================================================
    @staticmethod
    def format_vector(vector):
        if vector is None:
            return "None"
        return "[ " + ", ".join(f"{float(value):.4f}" for value in vector) + " ]"

    # =====================================================
    # MATRIX FORMAT
    # =====================================================
    @staticmethod
    def format_matrix(matrix):
        if matrix is None:
            return "None"
        lines = []
        for row in matrix:
            lines.append("[ " + "   ".join(f"{float(value):.4f}" for value in row) + " ]")
        return "\n".join(lines)

    # =====================================================
    # DISPLAY RESULT (UPDATED v2.0)
    # =====================================================
    def display_robot_result(self, dimension, position, transformed_position, matrix, original_vertices=None, transformed_vertices=None):
        lines = []
        lines.append("ROBOT DEFINITION")
        lines.append("=" * 40)
        lines.append(f"Dimension: {dimension}D")
        lines.append("Robot Type: " + self.robot_type_combo.currentText())
        lines.append("Degrees of Freedom: " + str(self.dof_spin.value()))
        lines.append("")
        lines.append("TRANSFORMATION")
        lines.append("=" * 40)
        transformations = self.get_active_transformations()
        lines.append("Operations: " + (", ".join(transformations) if transformations else "None"))
        if self.combination_results:
            lines.append("")
            lines.append("Transformation Parameters:")
            for key, value in self.combination_results.items():
                lines.append(f"  {key}: {value}")
                
        # =================================================
        # BASE POSITION
        # =================================================
        lines.append("")
        lines.append("BASE POSITION (Vertex 1)")
        lines.append("=" * 40)
        lines.append("Original: " + self.format_vector(position))
        lines.append("Transformed: " + self.format_vector(transformed_position))
        
        # =================================================
        # ALL OTHER VERTICES / JOINTS
        # =================================================
        if original_vertices and transformed_vertices:
            lines.append("")
            lines.append("ALL JOINTS / VERTICES")
            lines.append("=" * 40)
            vertex_count = len(original_vertices[0])
            for i in range(vertex_count):
                orig_pt = [original_vertices[row][i] for row in range(dimension)]
                trans_pt = [transformed_vertices[row][i] for row in range(dimension)]
                
                lines.append(f"Vertex {i + 1}:")
                lines.append(f"  Original:    {self.format_vector(orig_pt)}")
                lines.append(f"  Transformed: {self.format_vector(trans_pt)}")
                
        lines.append("")
        lines.append("TRANSFORMATION MATRIX")
        lines.append("=" * 40)
        lines.append(self.format_matrix(matrix))
        lines.append("")
        lines.append("OTHER ROBOT PARAMETERS")
        lines.append("=" * 40)
        lines.append("Velocity: " + (self.velocity_input.text() or "Not specified"))
        lines.append("Acceleration: " + (self.accel_input.text() or "Not specified"))
        lines.append("Inertia: " + (self.inertia_input.text() or "Not specified"))
        lines.append("PID Gains: " + (self.pid_input.text() or "Not specified"))
        self.robot_attributes.setPlainText("\n".join(lines))

    # =====================================================
    # VISUALIZATION BRIDGE (UPDATED v2.0)
    # =====================================================
    def update_visualizations(self, dimension, position, transformed_position, translation, rotation, scaling, axis, matrix, original_joints, transformed_joints, workspace_points):
        """Send calculated robot data to the visualization widgets."""
        if dimension == 2:
            self.view_2d.update_robot(
                position=position,
                transformed_position=transformed_position,
                translation=translation,
                rotation_degrees=rotation,
                scaling_factor=scaling,
                transformation_matrix=matrix,
                original_joints=original_joints,
                transformed_joints=transformed_joints,
                workspace_points=workspace_points,
            )
        else:
            self.view_3d.update_robot(
                position=position,
                transformed_position=transformed_position,
                translation=translation,
                rotation_degrees=rotation,
                scaling_factor=scaling,
                rotation_axis=axis,
                transformation_matrix=matrix,
                original_joints=original_joints,
                transformed_joints=transformed_joints,
                workspace_points=workspace_points,
            )

        self.robot_animation.set_robot(self.robot_definition)

    # =====================================================
    # BUILD ROBOT (UPDATED v2.0)
    # =====================================================
    def build_robot_definition(self):
        try:
            # =================================================
            # 1. DIMENSION
            # =================================================
            dimension = 2 if self.Dim2.isChecked() else 3

            # =================================================
            # 2. POSITION
            # =================================================
            vertex_matrix = self.get_vertex_matrix()
            position = [vertex_matrix[row][0] for row in range(dimension)]

            # =================================================
            # 3. CONFIGURE ENGINE
            # =================================================
            self.engine.configure_robot(
                dimension=dimension,
                robot_type=self.robot_type_combo.currentText(),
                dof=self.dof_spin.value(),
                position=position,
            )

            # =================================================
            # 4. TRANSFORMATIONS
            # =================================================
            translation = None
            rotation = None
            scaling = None
            axis = "z"

            if self.translation_button.isChecked():
                if "Translation vector" not in self.combination_results:
                    raise ValueError("Please enter the translation value.")
                translation = self.engine.parse_position(
                    self.combination_results["Translation vector"],
                    dimension,
                )

            if self.rotation_checkbox.isChecked():
                if "Rotation angle" not in self.combination_results:
                    raise ValueError("Please enter the rotation value.")
                rotation = float(self.combination_results["Rotation angle"])
                if dimension == 3:
                    axis = self.combination_results.get("Rotation axis", "z")

            if self.scaling_checkbox.isChecked():
                if "Scaling factor" not in self.combination_results:
                    raise ValueError("Please enter the scaling value.")
                scaling = float(self.combination_results["Scaling factor"])

            # =================================================
            # 5. ENGINE CALCULATION
            # =================================================
            transformed_position = self.engine.apply_transformation(
                translate_by=translation,
                rotate_degrees=rotation,
                scale_by=scaling,
                axis=axis,
            )

            # =================================================
            # 6. TRANSFORMATION MATRIX & VERTICES
            # =================================================
            matrix = self.engine.get_transform()
            transformed_vertices = self.engine.transform_vertices(vertex_matrix)

            # NEW v2.0: Convert matrices to list of joints for visualization
            vertex_count = len(vertex_matrix[0])
            original_joints = [
                [vertex_matrix[row][col] for row in range(dimension)]
                for col in range(vertex_count)
            ]
            transformed_joints = [
                [transformed_vertices[row][col] for row in range(dimension)]
                for col in range(vertex_count)
            ]

            # NEW v2.0: Calculate Workspace Point Cloud
            workspace_radius = max(1.0, self.dof_spin.value() * 2.0)
            workspace_points = generate_workspace_grid(
                center=position,
                radius=workspace_radius,
                resolution=10,
                dimension=dimension,
            )

            # =================================================
            # 7. STORE ROBOT DEFINITION
            # =================================================
            self.robot_definition = {
                "dimension": dimension,
                "robot_type": self.robot_type_combo.currentText(),
                "dof": self.dof_spin.value(),
                "position": position,
                "vertices": vertex_matrix,
                "transformed_vertices": transformed_vertices,
                "original_joints": original_joints,
                "transformed_joints": transformed_joints,
                "workspace_points": workspace_points,
                "transformations": self.get_active_transformations(),
                "translation": translation,
                "rotation": rotation,
                "scaling": scaling,
                "rotation_axis": axis,
                "transformed_position": transformed_position,
                "transformation_matrix": matrix,
                "velocity": self.velocity_input.text(),
                "acceleration": self.accel_input.text(),
                "inertia": self.inertia_input.text(),
                "pid": self.pid_input.text(),
            }

            # =================================================
            # 8. VISUALIZATION
            # =================================================
            self.update_visualizations(
                dimension=dimension,
                position=position,
                transformed_position=transformed_position,
                translation=translation,
                rotation=rotation,
                scaling=scaling,
                axis=axis,
                matrix=matrix,
                original_joints=original_joints,
                transformed_joints=transformed_joints,
                workspace_points=workspace_points,
            )

            # =================================================
            # 9. DISPLAY INFORMATION
            # =================================================
            self.display_robot_result(
                dimension=dimension,
                position=position,
                transformed_position=transformed_position,
                matrix=matrix,
                original_vertices=vertex_matrix,
                transformed_vertices=transformed_vertices,
            )

            # =================================================
            # 10. AUTOMATIC VIEW
            # =================================================
            if dimension == 2:
                self.show_2d_view()
            else:
                self.show_3d_view()

        # =================================================
        # ERROR HANDLING
        # =================================================
        except (ValueError, KeyError, RuntimeError) as error:
            self.robot_attributes.setPlainText(
                "ERROR\n"
                "========================================\n\n"
                + str(error)
            )
            QMessageBox.warning(self, "Robot Definition Error", str(error))

    # =====================================================
    # NEW v2.0: EXPORT TO PDF
    # =====================================================
    def export_to_pdf(self):
        if not self.robot_definition:
            QMessageBox.warning(self, "Export Error", "Please define a robot first.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return
            
        # Generate HTML Content
        dim = self.robot_definition["dimension"]
        orig_verts = self.robot_definition["vertices"]
        trans_verts = self.robot_definition["transformed_vertices"]
        matrix = self.robot_definition["transformation_matrix"]
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                h1 {{ color: #2563EB; border-bottom: 2px solid #2563EB; padding-bottom: 10px; }}
                h2 {{ color: #1E293B; margin-top: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                th, td {{ border: 1px solid #CBD5E1; padding: 8px; text-align: left; }}
                th {{ background-color: #F1F5F9; }}
                .matrix {{ font-family: monospace; white-space: pre; }}
            </style>
        </head>
        <body>
            <h1>AliXRobot v2.0 - Transformation Report</h1>
            <h2>Robot Configuration</h2>
            <p><b>Dimension:</b> {dim}D<br>
            <b>Type:</b> {self.robot_definition['robot_type']}<br>
            <b>DOF:</b> {self.robot_definition['dof']}</p>
            
            <h2>Transformation Parameters</h2>
            <p>{'<br>'.join([f'{k}: {v}' for k, v in self.combination_results.items()])}</p>
            
            <h2>Vertex Calculations</h2>
            <table>
                <tr><th>Vertex</th><th>Original</th><th>Transformed</th></tr>
        """
        
        vertex_count = len(orig_verts[0])
        for i in range(vertex_count):
            orig_pt = [orig_verts[row][i] for row in range(dim)]
            trans_pt = [trans_verts[row][i] for row in range(dim)]
            html += f"<tr><td>V{i+1}</td><td>{self.format_vector(orig_pt)}</td><td>{self.format_vector(trans_pt)}</td></tr>\n"
            
        html += f"""
            </table>
            
            <h2>Transformation Matrix</h2>
            <div class="matrix">{self.format_matrix(matrix)}</div>
            
            <h2>Dynamic Parameters</h2>
            <p><b>Velocity:</b> {self.velocity_input.text() or 'N/A'}<br>
            <b>Acceleration:</b> {self.accel_input.text() or 'N/A'}</p>
        </body>
        </html>
        """
        
        # Print to PDF
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        
        doc.print(printer)
        QMessageBox.information(self, "Export Success", f"PDF Report saved to:\n{file_path}")

    # =====================================================
    # NEW v2.0: EXPORT TO CSV
    # =====================================================
    def export_to_csv(self):
        if not self.robot_definition:
            QMessageBox.warning(self, "Export Error", "Please define a robot first.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV Data", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return
            
        dim = self.robot_definition["dimension"]
        orig_verts = self.robot_definition["vertices"]
        trans_verts = self.robot_definition["transformed_vertices"]
        matrix = self.robot_definition["transformation_matrix"]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["AliXRobot v2.0 - Data Export"])
            writer.writerow([])
            writer.writerow(["Robot Configuration"])
            writer.writerow(["Dimension", dim])
            writer.writerow(["Type", self.robot_definition['robot_type']])
            writer.writerow(["DOF", self.robot_definition['dof']])
            writer.writerow([])
            
            writer.writerow(["Vertex Calculations"])
            header = ["Vertex"] + [f"Orig_{chr(65+i)}" for i in range(dim)] + [f"Trans_{chr(65+i)}" for i in range(dim)]
            writer.writerow(header)
            
            vertex_count = len(orig_verts[0])
            for i in range(vertex_count):
                orig_pt = [orig_verts[row][i] for row in range(dim)]
                trans_pt = [trans_verts[row][i] for row in range(dim)]
                writer.writerow([f"V{i+1}"] + orig_pt + trans_pt)
                
            writer.writerow([])
            writer.writerow(["Transformation Matrix"])
            for row in matrix:
                writer.writerow(row)
                
        QMessageBox.information(self, "Export Success", f"CSV Data saved to:\n{file_path}")

    # =====================================================
    # VERTEX COUNT -> TABLE
    # =====================================================
    def update_vertex_table(self):
        if self._syncing_position:
            return
        try:
            vertices = int(self.robot_vertices.text())
            if vertices <= 0:
                raise ValueError
        except ValueError:
            self.table.blockSignals(True)
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.table.blockSignals(False)
            return
        dimension = 2 if self.Dim2.isChecked() else 3
        self._rebuild_table(dimension, vertices)

    # =====================================================
    # SHARED TABLE REBUILD (preserves existing values)
    # =====================================================
    def _rebuild_table(self, dimension, vertex_count, values=None):
        axis_labels = ["X", "Y"] if dimension == 2 else ["X", "Y", "Z"]
        old_rows = self.table.rowCount()
        old_cols = self.table.columnCount()
        old_matrix = None
        if values is None and old_rows and old_cols:
            old_matrix = [
                [
                    self.table.item(r, c).text() if self.table.item(r, c) else ""
                    for c in range(old_cols)
                ]
                for r in range(old_rows)
            ]
        self.table.blockSignals(True)
        self.table.setRowCount(dimension)
        self.table.setColumnCount(vertex_count)
        self.table.setVerticalHeaderLabels(axis_labels)
        self.table.setHorizontalHeaderLabels(
            [f"V{col + 1}" for col in range(vertex_count)]
        )
        for row in range(dimension):
            for col in range(vertex_count):
                if values is not None:
                    text = self._format_number(values[row][col])
                elif old_matrix and row < len(old_matrix) and col < len(old_matrix[row]):
                    text = old_matrix[row][col]
                else:
                    text = ""
                self.table.setItem(row, col, QTableWidgetItem(text))
        self.table.blockSignals(False)

    # =====================================================
    # LINE EDIT -> TABLE
    # =====================================================
    def apply_lineedit_to_table(self):
        if self._syncing_position:
            return
        text = self.robot_ini_posi_box.text().strip()
        if not text:
            return
        dimension = 2 if self.Dim2.isChecked() else 3
        try:
            matrix = self.parse_vertices_string(text, dimension)
        except ValueError as error:
            QMessageBox.warning(self, "Invalid Position", str(error))
            return
        vertex_count = len(matrix[0])
        self._syncing_position = True
        try:
            self.robot_vertices.setText(str(vertex_count))
            self._rebuild_table(dimension, vertex_count, values=matrix)
        finally:
            self._syncing_position = False

    # =====================================================
    # TABLE -> LINE EDIT
    # =====================================================
    def sync_table_to_lineedit(self, _item=None):
        if self._syncing_position:
            return
        try:
            matrix = self.get_vertex_matrix()
        except ValueError:
            return
        self._syncing_position = True
        try:
            self.robot_ini_posi_box.setText(self.format_vertices_string(matrix))
        finally:
            self._syncing_position = False

    # =====================================================
    # PARSING / FORMATTING HELPERS
    # =====================================================
    @staticmethod
    def parse_vertices_string(text, dimension):
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            raise ValueError(
                "Could not parse input. Use [x, y, z] or [[x,y,z], [x,y,z], ...]."
            )
        if isinstance(parsed, (int, float)):
            parsed = [parsed]
        if not isinstance(parsed, (list, tuple)):
            raise ValueError("Input must be a list or nested list of numbers.")
        if all(isinstance(v, (int, float)) for v in parsed):
            vertices = [list(parsed)]
        else:
            vertices = [list(v) for v in parsed]
        for i, vertex in enumerate(vertices):
            if len(vertex) != dimension:
                raise ValueError(
                    f"Vertex {i + 1} has {len(vertex)} value(s), "
                    f"expected {dimension} for {dimension}D."
                )
            if not all(isinstance(v, (int, float)) for v in vertex):
                raise ValueError(f"Vertex {i + 1} contains non-numeric values.")
        return [
            [vertices[col][row] for col in range(len(vertices))]
            for row in range(dimension)
        ]

    @staticmethod
    def format_vertices_string(matrix):
        dimension = len(matrix)
        vertex_count = len(matrix[0]) if dimension else 0
        vertices = [
            [matrix[row][col] for row in range(dimension)]
            for col in range(vertex_count)
        ]
        formatted = ", ".join(
            "[" + ", ".join(MainWindow._format_number(v) for v in vertex) + "]"
            for vertex in vertices
        )
        return f"[{formatted}]"

    @staticmethod
    def _format_number(value):
        value = float(value)
        return str(int(value)) if value.is_integer() else f"{value:g}"

    # =====================================================
    # READ TABLE AS MATRIX (dimension x vertices)
    # =====================================================
    def get_vertex_matrix(self):
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        if rows == 0 or cols == 0:
            raise ValueError("No vertex data entered.")
        matrix = []
        for row in range(rows):
            row_values = []
            for col in range(cols):
                item = self.table.item(row, col)
                text = item.text().strip() if item else ""
                if not text:
                    raise ValueError(
                        f"Missing value at row {row + 1}, column {col + 1}."
                    )
                try:
                    row_values.append(float(text))
                except ValueError:
                    raise ValueError(
                        f"Invalid number at row {row + 1}, column {col + 1}: '{text}'"
                    )
            matrix.append(row_values)
        return matrix


# =========================================================
# APPLICATION
# =========================================================
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
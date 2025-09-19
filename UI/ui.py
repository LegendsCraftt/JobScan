from pathlib import Path

from PyQt6.QtCore import (Qt, QPoint,
                          QUrl, QByteArray,
                          QObject)

from PyQt6.QtGui import (QIcon, QAction,
                         QIntValidator)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QCheckBox, QPushButton, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect, QMessageBox,
    QMenu, QRadioButton, QAbstractButton, QSpacerItem, QToolButton)

from UI.preferences_ui import PreferencesPanel
from UI.switch import QToggle
from model.settings import SETTINGS
from control.main_control import MainControl
from control.auth_controller import AuthController
from UI.menu import SlideOverPanel

from UI.styles_l import style as style_L
from UI.styles_d import style as style_D
from assets import resources_rc

class MainUI(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.style = 'dark'
        self.version = 'new'
        self.send_email = False
        self.overwrite = False

        self.signed_in = False


        self.init_ui()

        self.controller = MainControl(self)
        self.auth = AuthController(self)

        self.wire_signals()
        self.add_object_names()
        self.set_states()
        self.load_ui_settings()

        self.auth.bootstrap()


    # --------- setup ---------
    def init_ui(self) -> None:
        self.setWindowTitle("JobScan")
        self.setWindowIcon(QIcon(":/assets/jobscan-transparent-64-ico.ico"))
        self.setMinimumSize(960, 640)
        self.setMaximumSize(960, 640)

        self.setObjectName("root")

        # pos = SETTINGS.value("position", type=QPoint)
        # if pos:
        #     self.move(pos)

        # -- Root Layout --
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)

        # -- Title Section --
        self.title_container = QHBoxLayout()

        self.title_label = QLabel("JobScan")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.options_menu = QPushButton("☰")
        self.menu_panel = SlideOverPanel(self, width=200)
        self.preferences_panel = PreferencesPanel(self, width=350)

        self.sign_in_button = QToolButton()
        self.sign_in_button.setText("Sign in")
        self.sign_in_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.sign_in_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.sign_in_button.setAutoRaise(False)

        self.title_container.addWidget(self.sign_in_button)
        self.title_container.addStretch()
        self.title_container.addWidget(self.title_label)
        self.title_container.addSpacing(352)
        self.title_container.addWidget(self.options_menu)

        self.title_layout = QVBoxLayout()
        self.subtitle_label = QLabel("Pull all related files from any project sequence")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_layout.addLayout(self.title_container)
        self.title_layout.addWidget(self.subtitle_label)


        # -- Job + Package Input Row --
        self.package_layout = QHBoxLayout()
        self.package_layout.setSpacing(12)

        self.job_code_input = QLineEdit()
        self.job_code_input.setPlaceholderText('Job code..')
        self.job_code_input.setFixedHeight(40)
        self.job_code_input.setFixedWidth(120)
        self.job_code_input.setValidator(QIntValidator(0, 99999, self))

        self.package_input = QLineEdit()
        self.package_input.setPlaceholderText("Enter package (e.g., SUB#123)..")
        self.package_input.setFixedHeight(40)
        self.package_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.scan_btn = QPushButton("Scan")
        self.scan_btn.setEnabled(False)
        self.scan_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.package_layout.addWidget(self.job_code_input)
        self.package_layout.addWidget(self.package_input)
        self.package_layout.addWidget(self.scan_btn)

        # -- Output Path Field --
        self.output_path_input = QLineEdit()
        self.output_path_input.setReadOnly(True)
        self.output_path_input.setPlaceholderText("Optional output path...")
        self.output_path_input.setFixedHeight(40)
        self.output_path_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.outpath_button = QPushButton()
        self.outpath_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.out_path_layout = QHBoxLayout()
        self.out_path_layout.setSpacing(4)
        self.out_path_layout.addWidget(self.output_path_input, alignment=Qt.AlignmentFlag.AlignTop)
        self.out_path_layout.addWidget(self.outpath_button, alignment=Qt.AlignmentFlag.AlignTop)

        # -- Options Card Layout --
        self.options_card = QFrame()
        self.options_card.setFrameShape(QFrame.Shape.NoFrame)
        self.options_card.setFixedHeight(215)
        self.options_card.setFixedWidth(360)

        self.options_layout = QVBoxLayout(self.options_card)
        self.options_layout.setContentsMargins(16, 16, 16, 16)
        self.options_layout.setSpacing(8)

        self.email_toggle_layout = QHBoxLayout()
        self.email_toggle = QToggle("Attach to Email")

        self.options_title = QLabel("Include:")
        self.select_all = QCheckBox("Select all")
        self.assemblies_check = QCheckBox("Assemblies")
        self.parts_check = QCheckBox("Parts")
        self.nc_check = QCheckBox("NC")
        self.dxf_check = QCheckBox("DXF")
        self.enc_check = QCheckBox("ENC")

        self.options_title_layout = QHBoxLayout()
        self.options_title_layout.addWidget(self.options_title)
        self.options_title_layout.addStretch()
        self.options_title_layout.addWidget(self.email_toggle)

        self.options_layout.addLayout(self.options_title_layout)
        self.options_layout.addWidget(self.select_all)
        self.options_layout.addSpacing(24)
        self.options_layout.addWidget(self.assemblies_check)
        self.options_layout.addWidget(self.parts_check)
        self.options_layout.addWidget(self.nc_check)
        self.options_layout.addWidget(self.dxf_check)
        self.options_layout.addWidget(self.enc_check)

        self.options_section = QVBoxLayout()
        self.options_section.setSpacing(8)
        self.options_section.setContentsMargins(0, 0, 0, 0)
        self.options_section.addWidget(self.options_card, alignment=Qt.AlignmentFlag.AlignLeft)


        # -- Output + Options Horizontal Layout --
        self.output_options_layout = QHBoxLayout()
        self.output_options_layout.setSpacing(12)
        self.output_options_layout.addLayout(self.out_path_layout, stretch=3)
        self.output_options_layout.addLayout(self.options_section, stretch=2)




        # -- Combined Input + Output+Options Layout --
        self.package_output_layout = QVBoxLayout()
        self.package_output_layout.setSpacing(28)
        self.package_output_layout.addLayout(self.package_layout)
        self.package_output_layout.addLayout(self.output_options_layout)
        # self.package_output_layout.addLayout(self.email_toggle_layout)

        # -- Middle Layout --
        self.middle_layout = QVBoxLayout()
        self.middle_layout.setSpacing(32)
        self.middle_layout.addLayout(self.package_output_layout)

        # -- Footer / Status Layout --
        self.footer_layout = QHBoxLayout()
        self.status_label = QLabel("Ready.")
        self.help_btn = QPushButton("Help")
        self.footer_layout.addWidget(self.status_label)
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.help_btn)

        # -- Assemble All --
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addStretch()
        self.main_layout.addLayout(self.middle_layout)
        self.main_layout.addStretch()
        self.main_layout.addLayout(self.footer_layout)


    def add_object_names(self) -> None:
        self.title_label.setObjectName("titleLabel")
        self.subtitle_label.setObjectName("subtitleLabel")
        self.sign_in_button.setObjectName("signInButton")

        self.options_menu.setObjectName("optionsMenu")

        self.job_code_input.setObjectName("jobCodeInput")
        self.package_input.setObjectName("packageInput")
        self.output_path_input.setObjectName("outputPathInput")
        self.outpath_button.setObjectName("outpathButton")
        self.scan_btn.setObjectName("scanButton")

        self.email_toggle.setObjectName("emailToggle")

        self.options_card.setObjectName("optionsCard")
        self.options_title.setObjectName("optionsTitle")
        self.select_all.setObjectName("selectAllCheckbox")
        self.assemblies_check.setObjectName("assembliesCheckbox")
        self.parts_check.setObjectName("partsCheckbox")
        self.nc_check.setObjectName("ncCheckbox")
        self.dxf_check.setObjectName("dxfCheckbox")
        self.enc_check.setObjectName("encCheckbox")

        self.status_label.setObjectName("statusLabel")
        self.help_btn.setObjectName("helpButton")

    def wire_signals(self) -> None:
        self.sign_in_button.clicked.connect(self.auth.sign_in_clicked)

        self.options_menu.clicked.connect(self.menu_panel.toggle)
        self.menu_panel.preferences_button.clicked.connect(self.preferences_panel.toggle)

        self.preferences_panel.outlook_new_check.toggled.connect(self.controller.outlook__new_ui_handler)
        self.preferences_panel.outlook_old_check.toggled.connect(self.controller.outlook__old_ui_handler)

        self.preferences_panel.overwrite_check.toggled.connect(self.controller.overwrite_handler)

        self.menu_panel.about_button.clicked.connect(self.controller.about)
        self.menu_panel.about_button.clicked.connect(self.menu_panel.toggle)
        self.menu_panel.theme_button.clicked.connect(lambda x: self.controller._theme_toggle(self.style))
        self.menu_panel.help_button.clicked.connect(self.controller.help)
        self.menu_panel.help_button.clicked.connect(self.menu_panel.toggle)


        self.package_input.textChanged.connect(self.controller.status.input_changed)
        self.job_code_input.textChanged.connect(self.controller.status.input_changed)

        self.package_input.textChanged.connect(self.controller.handle_package_change)
        self.job_code_input.textChanged.connect(self.controller.handle_package_change)

        self.job_code_input.inputRejected.connect(self.controller.showInvalidTooltip)

        self.scan_btn.clicked.connect(self.controller.handle_scan_click)
        self.help_btn.clicked.connect(self.controller.help)
        self.select_all.toggled.connect(self.controller.handle_select_all)

        self.outpath_button.clicked.connect(self.controller.browse_outpath)
        self.output_path_input.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.output_path_input.customContextMenuRequested.connect(self.controller.show_outpath_menu)

        self.email_toggle.toggled.connect(self.controller.handle_email_toggle)



        for cb in self.get_checkboxes():
            cb.toggled.connect(self.controller.handle_child_checkbox_toggle)

    def get_checkboxes(self) -> list[QCheckBox]:
        return [
            self.assemblies_check,
            self.parts_check,
            self.nc_check,
            self.dxf_check,
            self.enc_check,
        ]

    def get_selected_targets(self) -> list[str]:
        return [
            label for checkbox, label in zip(
                self.get_checkboxes(),
                ["ASSEMBLY", "PART", "NC", "DXF", "ENC"]
            ) if checkbox.isChecked()
        ]

    def is_ready_to_scan(self) -> bool:
        return bool(self.job_code_input.text().strip() and self.package_input.text().strip())

    def load_ui_settings(self):
        saved_outpath = SETTINGS.value("outputPath", "", type=str)
        saved_theme = SETTINGS.value("theme", "", type=str)
        saved_overwrite = SETTINGS.value("overwrite", False, type=bool)
        saved_email_version = SETTINGS.value("emailVersion", "", type=str)
        saved_email_toggle = SETTINGS.value("sendEmail", False, type=bool)

        if saved_outpath:
            self.output_path_input.setText(saved_outpath)
            if not Path(saved_outpath).exists():
                QMessageBox.warning(self, "Warning", f"Saved output path does not exist: {saved_outpath}"
                                                     f"\nClearing saved path.")
                SETTINGS.setValue("outputPath", "")
                self.output_path_input.setText("")

        if saved_theme:
            self.controller.set_theme(saved_theme)
            self.style = saved_theme
            print(f"[load_ui_settings] Theme restored: {saved_theme}")
        else:
            self.controller.set_theme('dark')
            self.style = 'dark'

        if saved_overwrite:
            self.preferences_panel.overwrite_check.setChecked(saved_overwrite)
            self.overwrite = saved_overwrite
            print(f"[load_ui_settings] Overwrite restored: {saved_overwrite}")

        if saved_email_version:
            if saved_email_version == "new":
                self.preferences_panel.outlook_new_check.setChecked(True)
                self.controller.outlook__new_ui_handler()
            elif saved_email_version == "old":
                self.preferences_panel.outlook_old_check.setChecked(True)
                self.controller.outlook__old_ui_handler()
            print(f"[load_ui_settings] Email version restored: {saved_email_version}")
        else:
            self.preferences_panel.outlook_new_check.setChecked(True)
            self.controller.outlook__new_ui_handler()
            print("[load_ui_settings] No saved email version, defaulting to 'new'")


        self.email_toggle.setChecked(not saved_email_toggle)
        self.send_email = saved_email_toggle


    def set_states(self):
        if SETTINGS.value("overwrite", None) is None:
            self.preferences_panel.overwrite_check.setChecked(True)
            self.overwrite = True


        for cb in (self.assemblies_check, self.parts_check, self.nc_check, self.dxf_check, self.enc_check):
            cb.setChecked(True)

        self.select_all.setChecked(True)
    # --- Pre Defined Function Additions ---

    def closeEvent(self, event):
        SETTINGS.setValue("position", self.pos())
        super().closeEvent(event)

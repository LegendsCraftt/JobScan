from assets import resources_rc


COLOR_TEXT_PRIMARY = "#fff"
COLOR_TEXT_MUTED   = "#888"
PANEL_BG           = "rgba(255, 255, 255, 0.05)"

LE_OUTLINE         = "rgba(255,255,255,0.1)"

BTN_BG             = "rgba(255,255,255,0.04)"
BTN_HOVER          = "rgba(255,255,255,0.1)"
BTN_PRESSED        = "rgba(255,255,255,0.08)"

OUTPATH_BTN_BG     = BTN_BG
OUTPATH_BTN_HOVER  = BTN_HOVER
OUTPATH_BTN_PRESSED= BTN_PRESSED

HELP_HOVER         = "#b3d1ff"

INPUT_RADIUS       = "18px"
BTN_RADIUS         = "10px"
BTN_SMALL_RADIUS   = "6px"


style = f"""


QWidget#root {{
    background-color: #1E1E1E;
    
}}


/* =========================
   Options card
   ========================= */
#optionsCard {{
    border-radius: 18px;
    background: {PANEL_BG};
}}

/* =========================
   Buttons (base)
   ========================= */
QPushButton {{
    border-radius: {BTN_SMALL_RADIUS};
    padding: 4px 6px;
    font-size: 12px;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton:hover {{
    background: {BTN_HOVER};
}}

/* =========================
   Title / Subtitle
   ========================= */
#titleLabel {{
    color: #FFF;
    font-size: 28px;
    font-weight: 700;
}}
#subtitleLabel {{
    font-size: 14px;
    opacity: 0.7;
    color: {COLOR_TEXT_MUTED};  
}}

/* =========================
   Line edits
   ========================= */
   
QLineEdit {{
    background-color: #2D2D2D;
    color: {COLOR_TEXT_PRIMARY};  
}}

QLineEdit::focus {{
    border: .5px solid {LE_OUTLINE};
}}
   
#jobCodeInput {{
    font-size: 16px;
    border-radius: {INPUT_RADIUS};
    padding: 0 14px;
}}
#packageInput {{
    font-size: 16px;
    border-radius: {INPUT_RADIUS};
    padding: 0 14px;
}}
#outputPathInput {{
    font-size: 14px;
    font-style: italic;
    color: {COLOR_TEXT_MUTED};
    border-radius: {INPUT_RADIUS};
    padding: 0 14px;
    max-width: 420px;
    min-width: 420px;
}}

/* =========================
   Options title
   ========================= */
#optionsTitle {{
    font-weight: 600;
    font-size: 16px;
}}

/* =========================
   Status label
   ========================= */
#statusLabel {{
    color: {COLOR_TEXT_MUTED}; 
    font-weight: 600;
    font-size: 13px;
    opacity: 0.75;
}}



/* =========================
   Checkboxes
   ========================= */
QCheckBox {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 14px;
    font-weight: 600;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
}}

QCheckBox::indicator:checked {{
    image: url(":/assets/checkbox.png");
}}

QCheckBox::indicator:checked:hover {{
    image: url(":/assets/checkbox_hover.png");
}}

QCheckBox::indicator:unchecked {{
    image: url(":/assets/unchecked.png");
}}

QCheckBox::indicator:unchecked:hover {{
    image: url(":/assets/unchecked_hover.png");
}}

/* =========================
   Sign in button
   ========================= */
#signInButton {{
    color: #fff;
    border-radius: {BTN_SMALL_RADIUS};
    padding: 2px 4px;
    font-size: 17px;
    font-weight: 600;
    text-align: right;
}}

#signInButton:hover {{
    background: {BTN_HOVER};
}}


/* =========================
   Scan button
   ========================= */
#scanButton {{
    font-size: 12px;
    font-weight: 700;
    padding: 12px 14px;
    background: {BTN_BG};
    border-radius: {BTN_RADIUS};
    color: {COLOR_TEXT_PRIMARY};
}}
#scanButton:hover {{
    background: {OUTPATH_BTN_HOVER};
}}
#scanButton:pressed {{
    background: {BTN_PRESSED};
}}

/* =========================
   Outpath (three-dot) button
   ========================= */
#outpathButton {{
    font-size: 18px;
    font-weight: bold;
    padding: 8px 0px;
    image: url(":/assets/search.png");
    background: {OUTPATH_BTN_BG};
    border-radius: {BTN_RADIUS};
    margin-left: 8px;
}}
#outpathButton:hover {{
    background: {OUTPATH_BTN_HOVER};
    padding-right: 4px;
}}
#outpathButton:pressed {{
    background: {OUTPATH_BTN_PRESSED};
}}

/* =========================
   Help button
   ========================= */
#helpButton:hover {{
    color: {HELP_HOVER};
}}

/* =========================
   Email Toggle
   ========================= */
#emailToggle {{
    font-size: 14px;
    font-weight: 600;
    color: #fff;
}}

#menuSeparator {{
    color: #000;
}}

#separatorBottom {{
}}

#sidePanel {{
    background: #222426;
    border-radius: 12px;
}}

#sidePanelTitle {{
    color: {COLOR_TEXT_PRIMARY};  
    font-size: 18px;
    font-weight: 700;
}}

#sidePanelSubTitle {{
    color: {COLOR_TEXT_PRIMARY}; 
    font-size: 14px; 
    font-weight: 600;
}}

#scrimOverlay {{
    background: rgba(0,0,0,0.1);  /* dim the app while open */
}}

#sidePanelButton:hover {{
    background: {BTN_BG};
}}

#sidePanelButton:pressed {{
    background: {BTN_PRESSED};  
}}


QMessageBox {{
    background-color: #2b2b2b;
    color: #f0f0f0;
    font-size: 14px;
    border: 1px solid #444;
}}

QMessageBox QLabel {{
    color: #dddddd;
    font-size: 14px;
}}
# 
# QPushButton {{
#     background-color: #3c3f41;
#     color: #ffffff;
#     padding: 6px 14px;
#     border-radius: 6px;
# }}
# 
# QPushButton:hover {{
#     background-color: #505357;
# }}


/* =========================
   STUBS for all object names
   ========================= */
QLabel#titleLabel {{}}
QLabel#subtitleLabel {{}}
QLineEdit#jobCodeInput {{}}
QLineEdit#packageInput {{}}
QLineEdit#outputPathInput {{}}
QPushButton#outpathButton {{}}
QPushButton#scanButton {{}}
QFrame#optionsCard {{}}
QLabel#optionsTitle {{}}
QCheckBox#selectAllCheckbox {{}}
QCheckBox#assembliesCheckbox {{}}
QCheckBox#partsCheckbox {{}}
QCheckBox#ncCheckbox {{}}
QCheckBox#dxfCheckbox {{}}
QCheckBox#encCheckbox {{}}
QLabel#statusLabel {{}}
QPushButton#helpButton {{}}
"""



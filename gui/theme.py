"""Dark theme constants and QSS for BeatStyle."""

C = {
    "bg":        "#0c0c14",
    "card":      "#12121c",
    "hover":     "#1a1a28",
    "border":    "#232336",
    "border_hi": "#38385a",
    "accent":    "#6d28d9",
    "accent2":   "#a855f7",
    "text":      "#ededf8",
    "muted":     "#7070a0",
    "green":     "#16a34a",
    "red":       "#dc2626",
    "gold":      "#f59e0b",
}

QSS = f"""
/* ── Base ── */
QMainWindow, QDialog {{
    background: {C['bg']};
}}
QWidget {{
    background: transparent;
    color: {C['text']};
    font-family: "Segoe UI", "SF Pro Display", "Inter", sans-serif;
    font-size: 13px;
}}
QScrollArea {{
    background: {C['bg']};
    border: none;
}}
QScrollBar:vertical {{
    background: {C['card']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {C['border_hi']};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 0;
}}

/* ── Labels ── */
QLabel {{
    background: transparent;
    color: {C['text']};
}}
QLabel#title {{
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
}}
QLabel#subtitle {{
    font-size: 12px;
    color: {C['muted']};
}}
QLabel#section_tag {{
    background: {C['accent']};
    color: #fff;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 2px;
    padding: 3px 10px;
    border-radius: 10px;
}}
QLabel#muted {{
    color: {C['muted']};
    font-size: 12px;
}}

/* ── Cards ── */
QFrame#card {{
    background: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 14px;
}}
QFrame#card:hover {{
    border-color: {C['border_hi']};
}}

/* ── Buttons ── */
QPushButton {{
    background: {C['hover']};
    border: 2px solid {C['border']};
    border-radius: 8px;
    padding: 9px 20px;
    color: {C['text']};
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    border-color: {C['border_hi']};
}}
QPushButton:pressed {{
    background: {C['card']};
}}
QPushButton#primary {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {C['accent']}, stop:1 #4c1d95);
    border: none;
    color: #fff;
    font-size: 15px;
    padding: 14px 40px;
    border-radius: 10px;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #7c3aed, stop:1 #5b21b6);
}}
QPushButton#primary:disabled {{
    background: {C['border']};
    color: {C['muted']};
}}
QPushButton#dl {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #15803d, stop:1 #16a34a);
    border: none;
    color: #fff;
    font-size: 13px;
    padding: 10px 22px;
    border-radius: 8px;
}}
QPushButton#dl:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #166534, stop:1 #15803d);
}}
QPushButton#preset {{
    background: {C['hover']};
    border: 2px solid {C['border']};
    border-radius: 8px;
    color: {C['muted']};
    font-size: 12px;
    padding: 8px 14px;
}}
QPushButton#preset:hover {{
    border-color: {C['border_hi']};
    color: {C['text']};
}}
QPushButton#preset[active=true] {{
    border-color: {C['accent']};
    color: {C['accent2']};
    background: rgba(109,40,217,0.12);
}}

/* ── Style card buttons ── */
QPushButton#style_btn {{
    background: {C['hover']};
    border: 2px solid {C['border']};
    border-radius: 12px;
    padding: 12px 8px;
    text-align: center;
    color: {C['text']};
    font-size: 12px;
}}
QPushButton#style_btn:hover {{
    border-color: {C['border_hi']};
    background: #1e1e2e;
}}
QPushButton#style_btn[selected=true] {{
    border-color: {C['accent']};
    background: rgba(109,40,217,0.14);
}}

/* ── Drop zone ── */
QFrame#dropzone {{
    background: {C['card']};
    border: 2px dashed {C['border']};
    border-radius: 14px;
}}
QFrame#dropzone:hover {{
    border-color: {C['accent']};
    background: rgba(109,40,217,0.05);
}}
QFrame#dropzone[drag=true] {{
    border-color: {C['accent']};
    background: rgba(109,40,217,0.08);
}}

/* ── Slider ── */
QSlider::groove:horizontal {{
    background: {C['border']};
    height: 6px;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {C['accent']};
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}
QSlider::sub-page:horizontal {{
    background: {C['accent']};
    border-radius: 3px;
}}

/* ── Progress bar ── */
QProgressBar {{
    background: {C['hover']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['accent']}, stop:1 {C['accent2']});
    border-radius: 4px;
}}

/* ── Group box for style sections ── */
QGroupBox {{
    background: transparent;
    border: none;
    font-size: 11px;
    font-weight: 700;
    color: {C['muted']};
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 8px;
    padding-top: 16px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 0;
    top: 0;
}}

/* ── Separator ── */
QFrame[frameShape="4"] {{
    color: {C['border']};
}}
"""

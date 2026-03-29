"""
Icons — Lucide-style SVG icon provider for ShadowSIP.
Renders crisp vector icons at any size with theme-aware colors.
"""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtSvg import QSvgRenderer


# Lucide SVG paths (viewBox 0 0 24 24, stroke-based)
ICON_PATHS = {
    # Navigation
    "dialpad": [
        '<rect x="3" y="3" width="7" height="7" rx="1.5"/>',
        '<rect x="14" y="3" width="7" height="7" rx="1.5"/>',
        '<rect x="3" y="14" width="7" height="7" rx="1.5"/>',
        '<rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    ],
    "contacts": [
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>',
        '<circle cx="9" cy="7" r="4"/>',
        '<line x1="19" y1="8" x2="19" y2="14"/>',
        '<line x1="22" y1="11" x2="16" y2="11"/>',
    ],
    "chat": [
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    ],
    "history": [
        '<circle cx="12" cy="12" r="10"/>',
        '<polyline points="12 6 12 12 16 14"/>',
    ],
    "video": [
        '<polygon points="23 7 16 12 23 17 23 7"/>',
        '<rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>',
    ],
    "settings": [
        '<circle cx="12" cy="12" r="3"/>',
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    ],

    # Phone / Call
    "phone": [
        '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    ],
    "phone-off": [
        '<path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7 2 2 0 0 1 1.72 2v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.42 19.42 0 0 1-3.33-2.67m-2.67-3.34a19.79 19.79 0 0 1-3.07-8.63A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91"/>',
        '<line x1="1" y1="1" x2="23" y2="23"/>',
    ],

    # Actions
    "mic": [
        '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>',
        '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/>',
        '<line x1="12" y1="19" x2="12" y2="23"/>',
        '<line x1="8" y1="23" x2="16" y2="23"/>',
    ],
    "mic-off": [
        '<line x1="1" y1="1" x2="23" y2="23"/>',
        '<path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/>',
        '<path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .76-.13 1.49-.36 2.18"/>',
        '<line x1="12" y1="19" x2="12" y2="23"/>',
        '<line x1="8" y1="23" x2="16" y2="23"/>',
    ],
    "volume-2": [
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>',
        '<path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>',
        '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>',
    ],
    "volume-x": [
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>',
        '<line x1="23" y1="9" x2="17" y2="15"/>',
        '<line x1="17" y1="9" x2="23" y2="15"/>',
    ],
    "pause": [
        '<rect x="6" y="4" width="4" height="16"/>',
        '<rect x="14" y="4" width="4" height="16"/>',
    ],
    "shuffle": [  # Transfer
        '<polyline points="16 3 21 3 21 8"/>',
        '<line x1="4" y1="20" x2="21" y2="3"/>',
        '<polyline points="21 16 21 21 16 21"/>',
        '<line x1="15" y1="15" x2="21" y2="21"/>',
        '<line x1="4" y1="4" x2="9" y2="9"/>',
    ],
    "disc": [  # Record
        '<circle cx="12" cy="12" r="10"/>',
        '<circle cx="12" cy="12" r="3"/>',
    ],
    "ban": [  # DND
        '<circle cx="12" cy="12" r="10"/>',
        '<line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>',
    ],
    "user-plus": [
        '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>',
        '<circle cx="8.5" cy="7" r="4"/>',
        '<line x1="20" y1="8" x2="20" y2="14"/>',
        '<line x1="23" y1="11" x2="17" y2="11"/>',
    ],
    "grid": [  # Keypad in-call
        '<rect x="3" y="3" width="7" height="7"/>',
        '<rect x="14" y="3" width="7" height="7"/>',
        '<rect x="14" y="14" width="7" height="7"/>',
        '<rect x="3" y="14" width="7" height="7"/>',
    ],

    # Call direction arrows
    "arrow-up-right": [
        '<line x1="7" y1="17" x2="17" y2="7"/>',
        '<polyline points="7 7 17 7 17 17"/>',
    ],
    "arrow-down-left": [
        '<line x1="17" y1="7" x2="7" y2="17"/>',
        '<polyline points="17 17 7 17 7 7"/>',
    ],

    # Misc
    "search": [
        '<circle cx="11" cy="11" r="8"/>',
        '<line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    ],
    "x": [
        '<line x1="18" y1="6" x2="6" y2="18"/>',
        '<line x1="6" y1="6" x2="18" y2="18"/>',
    ],
    "sun": [
        '<circle cx="12" cy="12" r="5"/>',
        '<line x1="12" y1="1" x2="12" y2="3"/>',
        '<line x1="12" y1="21" x2="12" y2="23"/>',
        '<line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>',
        '<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>',
        '<line x1="1" y1="12" x2="3" y2="12"/>',
        '<line x1="21" y1="12" x2="23" y2="12"/>',
        '<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>',
        '<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
    ],
    "moon": [
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
    ],
    "paperclip": [
        '<path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
    ],
    "send": [
        '<line x1="22" y1="2" x2="11" y2="13"/>',
        '<polygon points="22 2 15 22 11 13 2 9 22 2"/>',
    ],
    "zap": [  # Auto-answer / lightning bolt
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    ],
    "phone-incoming": [
        '<polyline points="16 2 16 8 22 8"/>',
        '<line x1="23" y1="1" x2="16" y2="8"/>',
        '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    ],
    "globe": [
        '<circle cx="12" cy="12" r="10"/>',
        '<line x1="2" y1="12" x2="22" y2="12"/>',
        '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    ],
}


def _build_svg(icon_name: str, color: str = "#000000",
               stroke_width: float = 2.0, size: int = 24) -> bytes:
    """Build an SVG string from icon paths."""
    paths = ICON_PATHS.get(icon_name, [])
    if not paths:
        # Fallback: simple circle
        paths = ['<circle cx="12" cy="12" r="8"/>']

    elements = "\n  ".join(paths)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}"
 viewBox="0 0 24 24" fill="none" stroke="{color}"
 stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
  {elements}
</svg>'''
    return svg.encode("utf-8")


def get_icon(name: str, color: str = "#666666", size: int = 24,
             stroke_width: float = 2.0) -> QIcon:
    """
    Get a QIcon from a Lucide icon name.

    Args:
        name: Icon name from ICON_PATHS
        color: Stroke color (hex)
        size: Icon size in pixels
        stroke_width: SVG stroke width

    Returns:
        QIcon ready to use on buttons/labels
    """
    svg_data = _build_svg(name, color, stroke_width, size)
    renderer = QSvgRenderer(QByteArray(svg_data))

    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def get_pixmap(name: str, color: str = "#666666", size: int = 24,
               stroke_width: float = 2.0) -> QPixmap:
    """
    Get a QPixmap from a Lucide icon name.
    Useful for QLabel.setPixmap().
    """
    svg_data = _build_svg(name, color, stroke_width, size)
    renderer = QSvgRenderer(QByteArray(svg_data))

    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap

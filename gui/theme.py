from __future__ import annotations
from tkinter import ttk

# ── Paleta ────────────────────────────────────────────────────────────────────
SIDEBAR_BG   = "#1A2535"
SIDEBAR_HOV  = "#243045"
BG           = "#F0F4F8"
SURFACE      = "#FFFFFF"
TEXT         = "#1A2332"
TEXT_MUTED   = "#5A6B7B"
TEXT_ON_DARK = "#FFFFFF"
SUBTEXT_DARK = "#8FA3BF"

PRIMARY  = "#2563EB"
SUCCESS  = "#16A34A"
WARNING  = "#D97706"
DANGER   = "#DC2626"
NEUTRAL  = "#475569"

BORDER  = "#DDE3EC"
ROW_ODD = "#F8FAFC"

# ── Fuentes ───────────────────────────────────────────────────────────────────
F_APP_TITLE = ("Segoe UI", 18, "bold")
F_H1        = ("Segoe UI", 15, "bold")
F_H2        = ("Segoe UI", 12, "bold")
F_BODY      = ("Segoe UI", 11)
F_BODY_B    = ("Segoe UI", 11, "bold")
F_SMALL     = ("Segoe UI", 10)
F_ENTRY     = ("Segoe UI", 13)
F_ENTRY_LG  = ("Segoe UI", 20)
F_PRICE     = ("Segoe UI", 18, "bold")
F_TOTAL     = ("Segoe UI", 19, "bold")
F_VUELTO    = ("Segoe UI", 15, "bold")
F_BTN_SIDE  = ("Segoe UI", 11, "bold")
F_BTN       = ("Segoe UI", 11, "bold")

# ── Colores de botones semánticos ─────────────────────────────────────────────
BTN_COLORS = {
    "primary": (PRIMARY,  "#1D4ED8"),
    "success": (SUCCESS,  "#14803E"),
    "warning": (WARNING,  "#B45309"),
    "danger":  (DANGER,   "#B91C1C"),
    "neutral": (NEUTRAL,  "#3A4A5E"),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def setup_treeview_style(widget) -> None:
    """Aplica tema moderno a ttk.Treeview. Llamar una sola vez desde la ventana raíz."""
    s = ttk.Style(widget)
    s.theme_use("clam")
    s.configure("Treeview",
        background=SURFACE, foreground=TEXT,
        fieldbackground=SURFACE, rowheight=28,
        font=F_SMALL, borderwidth=0,
    )
    s.configure("Treeview.Heading",
        background=SIDEBAR_BG, foreground=TEXT_ON_DARK,
        font=F_BODY_B, relief="flat", padding=(8, 6),
    )
    s.map("Treeview",
        background=[("selected", PRIMARY)],
        foreground=[("selected", TEXT_ON_DARK)],
    )
    s.map("Treeview.Heading",
        background=[("active", SIDEBAR_HOV)],
    )


def tag_rows(tree: ttk.Treeview) -> None:
    """Configura tags para filas alternas en un Treeview."""
    tree.tag_configure("odd",  background=ROW_ODD)
    tree.tag_configure("even", background=SURFACE)

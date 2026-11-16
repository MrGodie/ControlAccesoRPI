"""
Generate the low-fidelity wireframes of the mobile access app (Integrativo 4).

Output:
    docs/Interface_5.png  - identification and access request (screens 01-05)
    docs/Interface_6.png  - request result and return to the start (screens 06-09)

The sheets follow the layout of docs/Interface_3.png and docs/Interface_4.png:
light gray canvas, sheet title and subtitle at the top, white screens with a
small-caps header (screen number on the left, state on the right), a footnote
with the requirement each screen covers, and the navigation map at the bottom.

Each screen is drawn at 1080x1920 (9:16 phone) and scaled to fit the grid.
Black and white only: the wireframes show what information appears and where,
not the final visual design. The on-screen copy is in Spanish, like the rest of
the system's interface.

Usage (from the repository root):
    python tools/generate_mobile_wireframes.py [--font-dir DIR]

Requires Pillow. It uses the Inter font if it can find it (the earlier sheets
were rendered with Inter); otherwise it falls back to DejaVu Sans or Arial.
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ layout --

SHEET_WIDTH = 5600
SCREEN_W, SCREEN_H = 1080, 1920          # native phone screen (9:16)
COLUMNS = 5                               # screens per row
GAP = 160                                 # space between screens (as in PI3)
CARD_W = (SHEET_WIDTH - GAP * (COLUMNS - 1)) // COLUMNS
SCALE = CARD_W / SCREEN_W
CARD_H = round(SCREEN_H * SCALE)
CARDS_TOP = 250                           # same top offset as PI3 sheets

MARGIN = 72                               # inner margin of a phone screen

# Grays taken from the PI3 sheets.
CANVAS = (229, 229, 229)
WHITE = (255, 255, 255)
INK = (17, 17, 17)
MUTED = (110, 110, 110)
FAINT = (150, 150, 150)
ROW_FILL = (245, 245, 245)
BORDER = (200, 200, 200)
DISABLED_FILL = (232, 232, 232)
DISABLED_INK = (165, 165, 165)

# ------------------------------------------------------------------- fonts --

FONT_CANDIDATES = {
    "regular": ["Inter-Regular.ttf", "Inter-Regular.otf", "DejaVuSans.ttf", "arial.ttf", "Arial.ttf"],
    "medium": ["Inter-Medium.ttf", "Inter-Medium.otf", "DejaVuSans.ttf", "arial.ttf", "Arial.ttf"],
    "bold": ["Inter-Bold.ttf", "Inter-SemiBold.ttf", "Inter-Bold.otf", "DejaVuSans-Bold.ttf",
             "arialbd.ttf", "Arial Bold.ttf"],
}


def _font_dirs(extra):
    dirs = [extra] if extra else []
    dirs += [
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
        "/usr/share/fonts/truetype/inter", "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/TTF", "/Library/Fonts", os.path.expanduser("~/Library/Fonts"),
        os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"),
    ]
    try:  # matplotlib ships DejaVu Sans, which makes the output portable
        import matplotlib
        dirs.append(os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf"))
    except ImportError:
        pass
    return [d for d in dirs if d and os.path.isdir(d)]


def _find_font(weight, dirs):
    for name in FONT_CANDIDATES[weight]:
        for d in dirs:
            path = os.path.join(d, name)
            if os.path.isfile(path):
                return path
    return None


class Fonts:
    def __init__(self, font_dir=None):
        dirs = _font_dirs(font_dir)
        self.paths = {w: _find_font(w, dirs) for w in FONT_CANDIDATES}
        if not all(self.paths.values()):
            sys.exit("No usable font found; pass --font-dir with Inter, DejaVu Sans or Arial.")
        self._cache = {}

    def get(self, weight, size):
        key = (weight, size)
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(self.paths[weight], size)
        return self._cache[key]


# ---------------------------------------------------------- drawing helpers --

def text_width(draw, text, font, tracking=0):
    if not tracking:
        return draw.textlength(text, font=font)
    return sum(draw.textlength(c, font=font) for c in text) + tracking * (len(text) - 1)


def draw_tracked(draw, xy, text, font, fill, tracking=0):
    """Draw text with extra letter spacing (used for the small-caps labels)."""
    if not tracking:
        draw.text(xy, text, font=font, fill=fill)
        return
    x, y = xy
    for c in text:
        draw.text((x, y), c, font=font, fill=fill)
        x += draw.textlength(c, font=font) + tracking


class Screen:
    """One phone screen drawn at native 1080x1920 resolution."""

    def __init__(self, fonts, number, state):
        self.f = fonts
        self.img = Image.new("RGB", (SCREEN_W, SCREEN_H), WHITE)
        self.d = ImageDraw.Draw(self.img)
        self.y = 0
        self._header(number, state)

    # -- structure --

    def _header(self, number, state):
        font = self.f.get("medium", 22)
        draw_tracked(self.d, (MARGIN, 72), f"{number} · APP DE ACCESO · PUNTO 01", font, MUTED, 2.5)
        label = f"ESTADO: {state}"
        w = text_width(self.d, label, font, 2.5)
        draw_tracked(self.d, (SCREEN_W - MARGIN - w, 72), label, font, MUTED, 2.5)
        self.y = 230

    def title(self, text, size=60):
        self.d.text((MARGIN, self.y), text, font=self.f.get("bold", size), fill=INK)
        self.y += int(size * 1.25)

    def subtitle(self, text):
        self.d.text((MARGIN, self.y), text, font=self.f.get("regular", 32), fill=MUTED)
        self.y += 90

    def space(self, px):
        self.y += px

    def row(self, text, emphasis=False):
        """Gray information row, as in the PI3 sheets. `emphasis` adds a black outline."""
        h = 84
        box = (MARGIN, self.y, SCREEN_W - MARGIN, self.y + h)
        self.d.rectangle(box, fill=ROW_FILL, outline=INK if emphasis else None, width=3)
        font = self.f.get("medium" if emphasis else "regular", 30)
        self.d.text((MARGIN + 24, self.y + h / 2), text, font=font, fill=INK, anchor="lm")
        self.y += h + 16

    def field(self, label, value, placeholder=False, error=False):
        draw_tracked(self.d, (MARGIN, self.y), label, self.f.get("medium", 22), MUTED, 2.5)
        self.y += 40
        h = 96
        box = (MARGIN, self.y, SCREEN_W - MARGIN, self.y + h)
        self.d.rectangle(box, fill=ROW_FILL, outline=INK if error else None, width=3)
        self.d.text((MARGIN + 24, self.y + h / 2), value, font=self.f.get("regular", 34),
                    fill=FAINT if placeholder else INK, anchor="lm")
        self.y += h + 36

    def progress(self, label, fraction):
        draw_tracked(self.d, (MARGIN, self.y), label, self.f.get("medium", 22), MUTED, 2)
        self.y += 40
        x0, x1 = MARGIN, SCREEN_W - MARGIN
        self.d.rectangle((x0, self.y, x1, self.y + 16), fill=ROW_FILL)
        self.d.rectangle((x0, self.y, x0 + (x1 - x0) * fraction, self.y + 16), fill=INK)
        self.y += 60

    # -- bottom area: buttons stay in the thumb zone, footnote at the very end --

    def buttons(self, buttons):
        """buttons: list of (label, kind) with kind in primary/secondary/disabled.
        Drawn full width, stacked from the bottom of the screen upwards."""
        h, gap = 112, 24
        bottom = SCREEN_H - 190
        top = bottom - len(buttons) * h - (len(buttons) - 1) * gap
        y = top
        font = self.f.get("medium", 34)
        for label, kind in buttons:
            box = (MARGIN, y, SCREEN_W - MARGIN, y + h)
            if kind == "primary":
                self.d.rectangle(box, fill=INK)
                color = WHITE
            elif kind == "disabled":
                self.d.rectangle(box, fill=DISABLED_FILL)
                color = DISABLED_INK
            else:
                self.d.rectangle(box, fill=WHITE, outline=BORDER, width=3)
                color = INK
            self.d.text((SCREEN_W / 2, y + h / 2), label, font=font, fill=color, anchor="mm")
            y += h + gap

    def footnote(self, text):
        self.d.text((MARGIN, SCREEN_H - 110), text, font=self.f.get("regular", 24), fill=FAINT)


# ------------------------------------------------------------------ screens --

def screens_sheet_5(f):
    out = []

    s = Screen(f, "01", "IDENTIFICACIÓN")
    s.title("Identifíquese")
    s.subtitle("Laboratorio · Punto 01")
    s.field("CÓDIGO DE USUARIO", "Ej. 1042", placeholder=True)
    s.field("CLAVE", "••••••", placeholder=True)
    s.row("Solo para solicitar acceso a este punto")
    s.buttons([("Identificarme", "primary")])
    s.footnote("FR-15 · Formulario vacío · la app no tiene funciones de administración")
    out.append(s)

    s = Screen(f, "02", "CREDENCIAL INVÁLIDA")
    s.title("Identifíquese")
    s.subtitle("Laboratorio · Punto 01")
    s.field("CÓDIGO DE USUARIO", "1042", error=True)
    s.field("CLAVE", "••••••", error=True)
    s.row("Código o clave incorrectos", emphasis=True)
    s.row("Revise los datos e intente de nuevo")
    s.buttons([("Identificarme", "primary")])
    s.footnote("FR-15 · No indica cuál de los dos campos falló")
    out.append(s)

    s = Screen(f, "03", "ESPERANDO PRESENCIA")
    s.title("Luis Gutiérrez")
    s.subtitle("Identificado · Punto 01")
    s.row("Sensor PIR: sin presencia detectada")
    s.row("Acérquese al punto de acceso")
    s.row("La solicitud se habilita al detectarle")
    s.buttons([("Solicitar acceso", "disabled"), ("Salir", "secondary")])
    s.footnote("FR-16 · Botón deshabilitado hasta que el PIR detecte presencia")
    out.append(s)

    s = Screen(f, "04", "SOLICITUD HABILITADA")
    s.title("Luis Gutiérrez")
    s.subtitle("Identificado · Punto 01")
    s.row("Sensor PIR: presencia detectada", emphasis=True)
    s.row("Ya puede solicitar el acceso")
    s.row("La presencia habilita, no autoriza")
    s.buttons([("Solicitar acceso", "primary"), ("Salir", "secondary")])
    s.footnote("FR-16 · El PIR solo habilita la solicitud")
    out.append(s)

    s = Screen(f, "05", "ENVIANDO")
    s.title("Enviando solicitud...")
    s.subtitle("Luis Gutiérrez · Punto 01")
    s.progress("VALIDANDO EN LA RASPBERRY PI", 0.6)
    s.row("Esperando la respuesta del sistema")
    s.row("No cierre la app")
    s.buttons([("Solicitar acceso", "disabled")])
    s.footnote("FR-20 · Misma validación que botones, interfaz y rostro")
    out.append(s)

    return out


def screens_sheet_6(f):
    out = []

    s = Screen(f, "06", "AUTORIZADO")
    s.title("ACCESO AUTORIZADO", 64)
    s.subtitle("Luis Gutiérrez · Rol: Administrador")
    s.row("Punto 01: puerta abierta")
    s.row("Audio y actuador en el punto de acceso")
    s.row("Intento registrado")
    s.buttons([("Terminar", "primary")])
    s.footnote("Registrado: AUTORIZADO · método APP · vuelve al inicio en 5 s")
    out.append(s)

    s = Screen(f, "07", "RECHAZADO")
    s.title("ACCESO RECHAZADO", 64)
    s.subtitle("Ana Ruíz · Rol: Visitante")
    s.row("Su rol no tiene permiso en este punto")
    s.row("Punto 01: puerta cerrada")
    s.row("Intento registrado")
    s.buttons([("Terminar", "primary")])
    s.footnote("Registrado: DENEGADO_SIN_PERMISO · método APP · vuelve al inicio en 5 s")
    out.append(s)

    s = Screen(f, "08", "FALLO TÉCNICO")
    s.title("NO SE PUDO COMPLETAR", 64)
    s.subtitle("Condición técnica")
    s.row("Esto NO es un acceso rechazado", emphasis=True)
    s.row("El sistema no respondió a tiempo")
    s.row("Reintente o use otro medio de acceso")
    s.buttons([("Reintentar", "primary"), ("Terminar", "secondary")])
    s.footnote("NFR-11 · Un fallo técnico nunca se muestra como rechazo")
    out.append(s)

    s = Screen(f, "09", "REGRESO AL INICIO")
    s.title("Operación terminada")
    s.subtitle("Volviendo a Identificación")
    s.progress("REGRESANDO EN 3 S", 0.4)
    s.row("Se borraron el código y la clave")
    s.row("La siguiente persona inicia desde 01")
    s.buttons([("Ir al inicio", "secondary")])
    s.footnote("FR-19 · La app vuelve a 01 sin datos del intento")
    out.append(s)

    return out


# ------------------------------------------------------------------- sheets --

def render_sheet(f, title, subtitle, screens, navigation, notes, path):
    nav_line = 46
    nav_height = 90 + len(navigation) * nav_line + sum(80 + 46 * len(lines) for _, lines in notes) + 60
    height = CARDS_TOP + CARD_H + 110 + nav_height
    sheet = Image.new("RGB", (SHEET_WIDTH, height), CANVAS)
    d = ImageDraw.Draw(sheet)

    d.text((0, 30), title, font=f.get("bold", 64), fill=INK)
    d.text((0, 112), subtitle, font=f.get("regular", 32), fill=MUTED)

    for i, screen in enumerate(screens):
        card = screen.img.resize((CARD_W, CARD_H), Image.LANCZOS)
        sheet.paste(card, (i * (CARD_W + GAP), CARDS_TOP))

    y = CARDS_TOP + CARD_H + 110
    label_font = f.get("medium", 26)
    body_font = f.get("regular", 28)
    draw_tracked(d, (0, y), "NAVEGACIÓN", label_font, INK, 4)
    y += 62
    for origin, target in navigation:
        d.text((0, y), origin, font=body_font, fill=INK)
        d.text((380, y), target, font=body_font, fill=INK)
        y += nav_line
    for heading, lines in notes:
        y += 34
        draw_tracked(d, (0, y), heading, label_font, INK, 4)
        y += 46
        for line in lines:
            d.text((0, y), line, font=body_font, fill=INK)
            y += 46

    sheet.save(path, optimize=True)
    print(f"wrote {path} ({sheet.width}x{sheet.height})")


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--font-dir", help="directory containing Inter, DejaVu Sans or Arial")
    parser.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "..", "docs"))
    args = parser.parse_args()

    f = Fonts(args.font_dir)
    subtitle = "Baja fidelidad · 1080×1920 por pantalla (celular, 9:16) · Proyecto Integrativo 4"

    render_sheet(
        f,
        "Control de Acceso RPi · PI4 — App móvil (1/2): identificación y solicitud",
        subtitle,
        screens_sheet_5(f),
        [
            ("01 Identificación", "→ (Identificarme, credencial válida) → 03 Esperando presencia | 04 Solicitud habilitada"),
            ("01 Identificación", "→ (credencial inválida) → 02 Credencial inválida → (corregir datos) → 01"),
            ("03 Esperando presencia", "→ (el PIR detecta presencia) → 04 Solicitud habilitada"),
            ("04 Solicitud habilitada", "→ (se pierde la presencia) → 03 Esperando presencia"),
            ("04 Solicitud habilitada", "→ (Solicitar acceso) → 05 Enviando"),
            ("05 Enviando", "→ lámina 2/2 (Interface_6): 06 Autorizado | 07 Rechazado | 08 No se pudo completar"),
            ("03 · 04", "→ (Salir) → 01 Identificación"),
        ],
        [
            ("RUTA ALTERNATIVA", [
                "Si la Raspberry Pi no responde al identificarse, la app muestra 08 No se pudo completar; nunca 02 Credencial inválida.",
            ]),
            ("FUERA DE ALCANCE", [
                "La app no registra usuarios, no modifica permisos, no administra cuentas ni configura el sistema (NFR-09).",
            ]),
        ],
        os.path.join(args.out_dir, "Interface_5.png"),
    )

    render_sheet(
        f,
        "Control de Acceso RPi · PI4 — App móvil (2/2): resultado y regreso al inicio",
        subtitle,
        screens_sheet_6(f),
        [
            ("05 Enviando", "→ 06 Autorizado | 07 Rechazado | 08 No se pudo completar"),
            ("06 · 07", "→ (Terminar, o tras 5 s) → 09 Regreso al inicio"),
            ("08 No se pudo completar", "→ (Reintentar) → 04 Solicitud habilitada si sigue la presencia; si no, 03"),
            ("08 No se pudo completar", "→ (Terminar) → 09 Regreso al inicio"),
            ("09 Regreso al inicio", "→ (3 s, o Ir al inicio) → 01 Identificación, con el formulario vacío"),
        ],
        [
            ("RUTA ALTERNATIVA", [
                "Los botones, la interfaz de la Raspberry Pi y el rostro siguen funcionando igual; la app es un medio de acceso más (NFR-10).",
            ]),
            ("FUERA DE ALCANCE", [
                "La app no registra usuarios, no modifica permisos, no administra cuentas ni configura el sistema (NFR-09).",
            ]),
        ],
        os.path.join(args.out_dir, "Interface_6.png"),
    )


if __name__ == "__main__":
    main()

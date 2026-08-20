#!/usr/bin/env python3
"""Génère les images du site : logo large, logo carré et carte de partage.

POURQUOI CE SCRIPT
    Le texte des images est converti en tracés vectoriels plutôt que laissé
    sous forme de <text>. Les polices manuscrites habituelles (« Comic Sans
    MS », « Chalkboard SE », « Bradley Hand ») n'existent pas sous Linux, où
    le repli générique « cursive » donne une anglaise inadaptée à une ardoise.
    En vectorisant, le rendu est identique sur Linux, Windows et macOS, sans
    police installée ni téléchargement de webfont.

POLICE (PROVENANCE)
    Patrick Hand, sous licence SIL Open Font License 1.1.
    https://fonts.google.com/specimen/Patrick+Hand

    C'est la police à réutiliser pour régénérer ou prolonger ces images. Elle
    est retenue parce qu'elle garde « 5 », « D » et « 1 » nettement distincts,
    ce que des polices plus décoratives (Permanent Marker, Architects
    Daughter) ne font pas : leur « 1 » se lit « I ». Les fichiers produits ne
    contiennent aucune trace de la police — ni commentaire, ni métadonnée —,
    ce fichier est donc le seul endroit où cette information est consignée.

PRÉREQUIS
    pip install fonttools
    et, pour le PNG, un convertisseur SVG -> PNG parmi : rsvg-convert,
    ImageMagick, Inkscape, ou `pip install cairosvg`.

EXEMPLES
    python3 generate_assets.py
    python3 generate_assets.py --code 4D2 --title "Projet 2" --session "Hiver 2027"
    python3 generate_assets.py --font /chemin/vers/PatrickHand-Regular.ttf
"""

from __future__ import annotations

import argparse
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

try:
    from fontTools.misc.transform import Transform
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
except ImportError:
    sys.exit("fontTools est requis : pip install fonttools")

FONT_URL = (
    "https://raw.githubusercontent.com/google/fonts/main/ofl/"
    "patrickhand/PatrickHand-Regular.ttf"
)

# Palette commune aux trois images.
WOOD = "#d8a15d"        # cadre de bois
BORDER = "#234a2b"      # liséré sombre
BOARD = "#2f6b3f"       # ardoise
CHALK = "#f2f2f2"       # craie

# Part de la largeur de l'ardoise occupée par le code du cours, sur le logo.
LOGO_FILL = 0.55


def get_font(font_arg: str | None) -> Path:
    """Retourne le chemin du TTF, en le téléchargeant au besoin."""
    if font_arg:
        path = Path(font_arg)
        if not path.is_file():
            sys.exit(f"Police introuvable : {path}")
        return path

    cache = Path(tempfile.gettempdir()) / "patrickhand-cache" / "PatrickHand-Regular.ttf"
    if cache.is_file() and cache.stat().st_size > 10_000:
        return cache

    cache.parent.mkdir(parents=True, exist_ok=True)
    print("Téléchargement de Patrick Hand...", file=sys.stderr)
    try:
        with urllib.request.urlopen(FONT_URL, timeout=30) as response:
            data = response.read()
    except OSError as exc:
        sys.exit(f"Échec du téléchargement de la police : {exc}\n"
                 f"Téléchargez-la manuellement depuis {FONT_URL} puis utilisez --font.")
    if len(data) < 10_000:
        sys.exit("Le fichier téléchargé n'est pas une police valide.")
    cache.write_bytes(data)
    return cache


def round_path(d: str, digits: int = 2) -> str:
    """Réduit la précision des coordonnées (gain d'environ 40 % sur le fichier)."""
    return re.sub(r"-?\d+\.\d+",
                  lambda m: f"{round(float(m.group(0)), digits):g}", d)


class Typesetter:
    """Convertit du texte en tracés SVG à partir des contours de la police."""

    def __init__(self, font_path: Path) -> None:
        font = TTFont(str(font_path))
        if "fvar" in font:  # fige une police variable sur ses valeurs par défaut
            axes = {axis.axisTag: axis.defaultValue for axis in font["fvar"].axes}
            font = instantiateVariableFont(font, axes, inplace=True)
        self.upem = font["head"].unitsPerEm
        self.glyphs = font.getGlyphSet()
        self.cmap = font.getBestCmap()

    def _names(self, text: str) -> tuple[list[str], list[float]]:
        names = []
        for char in text:
            name = self.cmap.get(ord(char))
            if name is None:
                sys.exit(f"La police ne contient pas le caractère {char!r}.")
            names.append(name)
        return names, [self.glyphs[n].width for n in names]

    def ink_box(self, text: str, size: float) -> tuple[float, float, float, float]:
        """Boîte de l'encre réelle (et non de la chasse), en unités SVG."""
        names, advances = self._names(text)
        pen = BoundsPen(self.glyphs)
        x = 0.0
        for name, advance in zip(names, advances, strict=True):
            self.glyphs[name].draw(TransformPen(pen, Transform().translate(x, 0)))
            x += advance
        x0, y0, x1, y1 = pen.bounds
        scale = size / self.upem
        return x0 * scale, y0 * scale, x1 * scale, y1 * scale

    def path(self, text: str, size: float, cx: float, baseline: float) -> str:
        """Tracé du texte, centré horizontalement sur `cx`."""
        names, advances = self._names(text)
        scale = size / self.upem
        x0, _, x1, _ = self.ink_box(text, size)
        pen = SVGPathPen(self.glyphs)
        x = cx - (x0 + x1) / 2
        for name, advance in zip(names, advances, strict=True):
            self.glyphs[name].draw(
                TransformPen(pen, Transform().translate(x, baseline).scale(scale, -scale)))
            x += advance * scale
        return round_path(pen.getCommands())

    def centered(self, text: str, size: float, cx: float, cy: float) -> str:
        """Tracé dont l'encre est centrée sur (cx, cy)."""
        _, y0, _, y1 = self.ink_box(text, size)
        return self.path(text, size, cx, cy + (y0 + y1) / 2)

    def fit_width(self, text: str, target: float) -> float:
        """Taille nominale pour que l'encre occupe exactement `target`."""
        x0, _, x1, _ = self.ink_box(text, 100)
        return 100 * target / (x1 - x0)


def build_logo(typesetter: Typesetter, code: str, fill: float = LOGO_FILL) -> str:
    """Logo large (navbar et page d'accueil) : 800x500."""
    bx, by, bw, bh = 70, 70, 660, 360
    size = typesetter.fit_width(code, bw * fill)
    d = typesetter.centered(code, size, bx + bw / 2, by + bh / 2)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <!-- Wood frame -->
  <rect x="20" y="20" width="760" height="460" rx="40" fill="{WOOD}"/>
  <!-- Inner dark border -->
  <rect x="55" y="55" width="690" height="390" rx="28" fill="{BORDER}"/>
  <!-- Chalkboard -->
  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="22" fill="{BOARD}"/>

  <path id="label" d="{d}" fill="{CHALK}" stroke="{CHALK}" stroke-width="4"
        stroke-linejoin="round" stroke-linecap="round"/>

  <!-- Chalk -->
  <rect x="570" y="405" width="140" height="28" rx="14" fill="{CHALK}"/>
</svg>
"""


def build_square_logo(typesetter: Typesetter, code: str) -> str:
    """Logo carré 512x512 : favicon, et logo de la barre de navigation.

    Le cadre large du logo devient illisible une fois réduit à 16-32px (favicon)
    ou à la hauteur de la barre de navigation : il est ramené à un liséré et la
    craie posée sur le rebord est retirée, ce qui laisse au code du cours toute
    la place disponible.
    """
    side, frame = 512, 26
    size = typesetter.fit_width(code, side - 2 * frame - 80)
    d = typesetter.centered(code, size, side / 2, side / 2)
    inner = side - 2 * frame
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" width="{side}" height="{side}">
  <rect width="{side}" height="{side}" rx="96" fill="{WOOD}"/>
  <rect x="{frame}" y="{frame}" width="{inner}" height="{inner}" rx="72" fill="{BOARD}"/>
  <path d="{d}" fill="{CHALK}" stroke="{CHALK}" stroke-width="10"
        stroke-linejoin="round" stroke-linecap="round"/>
</svg>
"""


def build_social(typesetter: Typesetter, code: str, title: str,
                 school: str, session: str) -> str:
    """Carte de partage 1200x630 (og:image / twitter:image).

    Les réseaux sociaux ne rendent pas les SVG : ce fichier n'est que la source
    du PNG du même nom, qui est la version réellement référencée par le site.
    """
    width, height = 1200, 630
    bx, by = 52, 52
    bw, bh = width - 104, height - 104
    cx, cy = bx + bw / 2, by + bh / 2

    # (texte, taille, ligne de base relative au bloc, couleur)
    rows = [(code, 190, 0, "#ffffff"),
            (title, 78, 118, CHALK),
            (school, 46, 190, "#cfe3d4"),
            (session, 40, 253, "#a9c9b4")]

    # Centre le bloc entier sur l'ardoise, d'après l'encre réelle.
    tops, bottoms = [], []
    for text, size, base, _ in rows:
        _, y0, _, y1 = typesetter.ink_box(text, size)
        tops.append(base - y1)
        bottoms.append(base - y0)
    shift = cy - (min(tops) + max(bottoms)) / 2

    paths = "\n".join(
        f'  <path d="{typesetter.path(text, size, cx, base + shift)}" fill="{fill}"/>'
        for text, size, base, fill in rows)

    # Craie : mêmes proportions que sur le logo, où elle repose sur le bord
    # inférieur de l'ardoise en le débordant légèrement.
    kx, ky = bw / 660, bh / 360
    cw, ch = 140 * ky, 28 * ky
    chx = (bx + bw) - 20 * kx - cw
    chy = (by + bh) + 3 * ky - ch

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <rect width="{width}" height="{height}" fill="{WOOD}"/>
  <rect x="34" y="34" width="{width - 68}" height="{height - 68}" rx="30" fill="{BORDER}"/>
  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="22" fill="{BOARD}"/>
{paths}
  <rect x="{chx:g}" y="{chy:g}" width="{cw:g}" height="{ch:g}" rx="{ch / 2:g}" fill="{CHALK}"/>
</svg>
"""


def svg_to_png(svg: Path, png: Path) -> str:
    """Convertit en PNG avec le premier outil disponible. Retourne son nom."""
    attempts = [
        ("rsvg-convert", lambda exe: [exe, "-o", str(png), str(svg)]),
        ("magick", lambda exe: [exe, "-background", "none", str(svg), "-flatten",
                                "-strip", str(png)]),
        ("convert", lambda exe: [exe, "-background", "none", str(svg), "-flatten",
                                 "-strip", str(png)]),
        ("inkscape", lambda exe: [exe, str(svg), "--export-type=png",
                                  f"--export-filename={png}"]),
    ]
    for name, argv in attempts:
        exe = shutil.which(name)
        if exe is None:
            continue
        try:
            subprocess.run(argv(exe), check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            continue
        if png.is_file() and png.stat().st_size > 1000:
            return name

    try:  # dernier recours
        import cairosvg
    except ImportError:
        sys.exit("Aucun convertisseur SVG -> PNG trouvé. Installez rsvg-convert, "
                 "ImageMagick, Inkscape, ou `pip install cairosvg`.")
    cairosvg.svg2png(url=str(svg), write_to=str(png))
    return "cairosvg"


def strip_png_metadata(png: Path) -> None:
    """Ne garde que IHDR/IDAT/IEND : aucun commentaire dans le PNG."""
    data = png.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return
    out, i = bytearray(data[:8]), 8
    while i < len(data):
        (length,) = struct.unpack(">I", data[i:i + 4])
        kind = data[i + 4:i + 8]
        if kind not in (b"tEXt", b"iTXt", b"zTXt", b"tIME"):
            out += data[i:i + 12 + length]
        i += 12 + length
    png.write_bytes(bytes(out))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère les logos et la carte de partage du site.")
    parser.add_argument("--code", default="5D1", help="code du cours (défaut : 5D1)")
    parser.add_argument("--title", default="Projet 3", help="titre du cours")
    parser.add_argument("--school", default="Collège de Maisonneuve",
                        help="établissement")
    parser.add_argument("--session", default="Automne 2026", help="session")
    parser.add_argument("--out-dir", default=Path("static/img"), type=Path,
                        help="dossier de sortie (défaut : static/img)")
    parser.add_argument("--logo-fill", default=LOGO_FILL, type=float,
                        help=f"part de la largeur de l'ardoise occupée par le code "
                             f"sur le logo (défaut : {LOGO_FILL})")
    parser.add_argument("--keep-svg", action="store_true",
                        help="conserver aussi le SVG source de la carte de partage")
    parser.add_argument("--font", help="chemin d'un PatrickHand-Regular.ttf local")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out: Path = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    typesetter = Typesetter(get_font(args.font))

    files = {
        out / f"{args.code}.svg": build_logo(typesetter, args.code, args.logo_fill),
        out / "logo-square.svg": build_square_logo(typesetter, args.code),
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")

    # La carte de partage n'est publiée qu'en PNG ; le SVG n'est qu'une étape
    # intermédiaire, écrite dans un fichier temporaire sauf si --keep-svg.
    social = build_social(typesetter, args.code, args.title, args.school, args.session)
    social_png = out / "social-card.png"
    if args.keep_svg:
        social_svg = out / "social-card.svg"
        social_svg.write_text(social, encoding="utf-8")
        tool = svg_to_png(social_svg, social_png)
        files[social_svg] = social
    else:
        with tempfile.TemporaryDirectory() as tmp:
            social_svg = Path(tmp) / "social-card.svg"
            social_svg.write_text(social, encoding="utf-8")
            tool = svg_to_png(social_svg, social_png)
    strip_png_metadata(social_png)

    for path in [*files, social_png]:
        print(f"  {path}  ({path.stat().st_size:,} octets)")
    print(f"\nPNG rasterisé avec : {tool}")
    print(f"Rappel : docusaurus.config.js référence img/{args.code}.svg (accueil), "
          f"img/logo-square.svg (favicon et barre de navigation) et "
          f"img/social-card.png.")


if __name__ == "__main__":
    main()

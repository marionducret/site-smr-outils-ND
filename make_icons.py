#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les icônes du portail (PNG + ICO) à partir du dessin de référence.

Usage :
    python3 make_icons.py

Le dessin est le même que src/assets/favicon-outils-smr-ducret.svg :
carré arrondi teal, trois barres blanches croissantes, point jaune.
Il est ici redessiné avec Pillow (aucun convertisseur SVG requis), en
supersampling ×8 pour un antialiasing propre.

Sorties dans src/assets/ :
    favicon-32.png        onglet (fallback PNG des vieux navigateurs)
    apple-touch-icon.png  180×180 — iOS « Sur l'écran d'accueil »
    icon-192.png          Android / Chrome desktop (manifest)
    icon-512.png          splash screen Android (manifest)
    favicon.ico           16/32/48 — fallback historique

⚠️ Si le SVG de référence change, mettre à jour SHAPES ci-dessous.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "src" / "assets"

TEAL = "#35706A"
WHITE = "#FFFFFF"
YELLOW = "#E9B833"

SS = 8          # facteur de supersampling
BASE = 64.0     # viewBox du SVG de référence

# (x, y, largeur, hauteur, rayon) dans le repère 64×64 du SVG
BARS = [
    (17, 36, 7, 10, 3.5),
    (28, 29, 7, 17, 3.5),
    (39, 22, 7, 24, 3.5),
]
DOT = (42.5, 13, 4)   # cx, cy, r
CORNER_RADIUS = 14


def draw_icon(size: int, padding: float = 0.0) -> Image.Image:
    """Dessine l'icône à `size` px. padding = marge en unités du repère 64."""
    canvas = size * SS
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # échelle : le dessin 64×64 occupe (64 - 2*padding) une fois la marge retirée
    inner = BASE - 2 * padding
    k = canvas / BASE

    def sx(v: float) -> float:
        return (padding + v * inner / BASE) * k

    def sl(v: float) -> float:  # longueur (pas d'offset de marge)
        return v * inner / BASE * k

    d.rounded_rectangle(
        [sx(0), sx(0), sx(BASE) - 1, sx(BASE) - 1],
        radius=sl(CORNER_RADIUS), fill=TEAL,
    )
    for x, y, w, h, r in BARS:
        d.rounded_rectangle(
            [sx(x), sx(y), sx(x + w), sx(y + h)], radius=sl(r), fill=WHITE,
        )
    cx, cy, r = DOT
    d.ellipse([sx(cx - r), sx(cy - r), sx(cx + r), sx(cy + r)], fill=YELLOW)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    # apple-touch-icon : iOS ne gère pas la transparence et rogne les coins lui-même.
    # On garde une petite marge pour que le dessin respire dans le masque iOS.
    outputs = {
        "favicon-32.png": (32, 0),
        "icon-192.png": (192, 0),
        "icon-512.png": (512, 0),
        "apple-touch-icon.png": (180, 2),
    }
    for name, (size, pad) in outputs.items():
        icon = draw_icon(size, pad)
        if name == "apple-touch-icon.png":
            bg = Image.new("RGB", icon.size, TEAL)
            bg.paste(icon, mask=icon.split()[3])
            icon = bg
        icon.save(ASSETS / name)
        print(f"  ✔ {name} ({size}×{size})")

    ico = draw_icon(64)
    ico.save(ASSETS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("  ✔ favicon.ico (16/32/48)")

    print(f"\nIcônes générées dans {ASSETS.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()

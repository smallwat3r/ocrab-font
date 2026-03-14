#!/usr/bin/env fontforge -lang=py
"""Build OCR A B - a hybrid of OCR-A and OCR-B.

Keeps A-Z, a-z, 0-9 from OCR-A. Replaces all other glyphs
(punctuation, symbols, brackets, operators, etc.) with their
OCR-B equivalents. Adds missing accented characters by
composing base letters with accent marks from OCR-B.
"""

from __future__ import annotations

import fontforge
import psMat
import unicodedata
from pathlib import Path
from typing import Any

# fontforge does not ship type stubs.
Font = Any
BBox = tuple[float, float, float, float]
Matrix = tuple[float, float, float, float, float, float]

SOURCES_DIR = Path(__file__).resolve().parent / "sources"
OCRA_PATH = SOURCES_DIR / "OCRA.otf"
OCRB_PATH = SOURCES_DIR / "OCRB.ttf"
OUTPUT_DIR = Path(__file__).resolve().parent / "fonts"
OUTPUTS = [
    OUTPUT_DIR / "ocrab.ttf",
    OUTPUT_DIR / "ocrab.otf",
    OUTPUT_DIR / "ocrab.woff",
    OUTPUT_DIR / "ocrab.woff2",
]

TARGET_WIDTH = 723

# Accent mark codepoints sourced from OCR-B.
_ACUTE = 0x00B4
_GRAVE = 0x0060
_CIRCUMFLEX = 0x02C6
_TILDE = 0x02DC
_DIAERESIS = 0x00A8
_CEDILLA = 0x00B8

# Accented characters to compose: (target, base, accent).
# Only includes characters absent from both OCR-A and OCR-B.
_COMPOSITIONS = [
    # grave
    (0xC0, ord("A"), _GRAVE),       # À
    (0xC8, ord("E"), _GRAVE),       # È
    (0xCC, ord("I"), _GRAVE),       # Ì
    (0xD2, ord("O"), _GRAVE),       # Ò
    (0xD9, ord("U"), _GRAVE),       # Ù
    (0xE0, ord("a"), _GRAVE),       # à
    (0xE8, ord("e"), _GRAVE),       # è
    (0xEC, ord("i"), _GRAVE),       # ì
    (0xF2, ord("o"), _GRAVE),       # ò
    (0xF9, ord("u"), _GRAVE),       # ù
    # acute
    (0xC1, ord("A"), _ACUTE),       # Á
    (0xC9, ord("E"), _ACUTE),       # É
    (0xCD, ord("I"), _ACUTE),       # Í
    (0xD3, ord("O"), _ACUTE),       # Ó
    (0xDA, ord("U"), _ACUTE),       # Ú
    (0xDD, ord("Y"), _ACUTE),       # Ý
    (0xE1, ord("a"), _ACUTE),       # á
    (0xE9, ord("e"), _ACUTE),       # é
    (0xED, ord("i"), _ACUTE),       # í
    (0xF3, ord("o"), _ACUTE),       # ó
    (0xFA, ord("u"), _ACUTE),       # ú
    (0xFD, ord("y"), _ACUTE),       # ý
    # circumflex
    (0xC2, ord("A"), _CIRCUMFLEX),  # Â
    (0xCA, ord("E"), _CIRCUMFLEX),  # Ê
    (0xCE, ord("I"), _CIRCUMFLEX),  # Î
    (0xD4, ord("O"), _CIRCUMFLEX),  # Ô
    (0xDB, ord("U"), _CIRCUMFLEX),  # Û
    (0xE2, ord("a"), _CIRCUMFLEX),  # â
    (0xEA, ord("e"), _CIRCUMFLEX),  # ê
    (0xEE, ord("i"), _CIRCUMFLEX),  # î
    (0xF4, ord("o"), _CIRCUMFLEX),  # ô
    (0xFB, ord("u"), _CIRCUMFLEX),  # û
    # tilde
    (0xC3, ord("A"), _TILDE),       # Ã
    (0xD5, ord("O"), _TILDE),       # Õ
    (0xE3, ord("a"), _TILDE),       # ã
    (0xF1, ord("n"), _TILDE),       # ñ
    (0xF5, ord("o"), _TILDE),       # õ
    # diaeresis
    (0xCB, ord("E"), _DIAERESIS),   # Ë
    (0xCF, ord("I"), _DIAERESIS),   # Ï
    (0xEB, ord("e"), _DIAERESIS),   # ë
    (0xEF, ord("i"), _DIAERESIS),   # ï
    (0xFF, ord("y"), _DIAERESIS),   # ÿ
    # cedilla
    (0xC7, ord("C"), _CEDILLA),     # Ç
    (0xE7, ord("c"), _CEDILLA),     # ç
]

# Max accent height before uniform scaling kicks in.
_MAX_ACCENT_H = 200
_MAX_CEDILLA_H = 250


def is_letter_or_digit(cp: int) -> bool:
    """Return True if codepoint is a letter or digit."""
    cat = unicodedata.category(chr(cp))
    return cat.startswith("L") or cat == "Nd"


def _glyph_exists(font: Font, cp: int) -> bool:
    """Return True if font has an outputtable glyph."""
    try:
        return font[cp].isWorthOutputting()
    except TypeError:
        return False


def build_ocrb_codepoints(ocrb: Font) -> set[int]:
    """Return the set of codepoints present in OCR-B."""
    return {
        g.unicode for g in ocrb.glyphs()
        if g.unicode >= 0
    }


def replace_symbols(
    ocra: Font,
    ocrb: Font,
    ocrb_codepoints: set[int],
) -> None:
    """Replace non-alphanumeric glyphs with OCR-B."""
    replaced = 0
    kept = 0

    for glyph in ocra.glyphs():
        cp = glyph.unicode
        if cp < 0:
            continue

        if is_letter_or_digit(cp):
            kept += 1
            continue

        if cp not in ocrb_codepoints:
            continue

        src = ocrb[cp]
        if not src.isWorthOutputting():
            continue

        glyph.clear()
        ocrb.selection.select(("unicode",), cp)
        ocrb.copy()
        ocra.selection.select(("unicode",), cp)
        ocra.paste()

        if glyph.references:
            glyph.unlinkRef()

        glyph.width = TARGET_WIDTH
        replaced += 1

    print(f"Kept {kept} OCR-A glyphs (letters/digits)")
    print(f"Replaced {replaced} glyphs with OCR-B")


def add_ocrb_extras(
    font: Font,
    ocrb: Font,
    ocrb_codepoints: set[int],
) -> None:
    """Add letters from OCR-B that are absent in OCR-A."""
    added = 0
    for cp in sorted(ocrb_codepoints):
        if cp < 0x80:
            continue
        if not is_letter_or_digit(cp):
            continue
        if _glyph_exists(font, cp):
            continue

        src = ocrb[cp]
        if not src.isWorthOutputting():
            continue

        font.createChar(cp)
        ocrb.selection.select(("unicode",), cp)
        ocrb.copy()
        font.selection.select(("unicode",), cp)
        font.paste()

        glyph = font[cp]
        if glyph.references:
            glyph.unlinkRef()
        glyph.width = TARGET_WIDTH
        added += 1

    print(f"Added {added} extra glyphs from OCR-B")


def _accent_matrix(
    base_bb: BBox,
    accent_bb: BBox,
    is_cedilla: bool,
) -> Matrix:
    """Build affine matrix to position an accent mark."""
    accent_w = accent_bb[2] - accent_bb[0]
    accent_h = accent_bb[3] - accent_bb[1]

    max_h = _MAX_CEDILLA_H if is_cedilla else _MAX_ACCENT_H
    scale = min(1.0, max_h / accent_h)

    base_cx = (base_bb[0] + base_bb[2]) / 2
    is_upper = base_bb[3] > 700
    gap = 30 if is_upper else 40

    scaled_w = accent_w * scale

    # Move accent bottom-left to origin, scale uniformly,
    # then translate to final position.
    tx = base_cx - scaled_w / 2
    if is_cedilla:
        ty = base_bb[1] - accent_h * scale
    else:
        ty = base_bb[3] + gap

    m = psMat.translate(-accent_bb[0], -accent_bb[1])
    m = psMat.compose(m, psMat.scale(scale))
    m = psMat.compose(m, psMat.translate(tx, ty))
    return m


def _remove_dot(glyph: Any) -> None:
    """Remove dot contour from a dotted letter (i, j).

    Keeps only body contours so the accent can replace
    the dot.
    """
    layer = glyph.foreground
    n = len(layer)
    if n < 2:
        return

    tops = [layer[i].boundingBox()[3] for i in range(n)]
    body_top = min(tops)
    keep = [
        layer[i].dup() for i in range(n)
        if tops[i] <= body_top + 10
    ]

    glyph.clear()
    layer = glyph.foreground
    for c in keep:
        layer += c
    glyph.foreground = layer


def compose_accented_glyphs(font: Font, ocrb: Font) -> None:
    """Compose accented characters from base + accent."""
    composed = 0
    for target_cp, base_cp, accent_cp in _COMPOSITIONS:
        if _glyph_exists(font, target_cp):
            continue

        # Copy base letter into target glyph slot.
        font.createChar(target_cp)
        font.selection.select(("unicode",), base_cp)
        font.copy()
        font.selection.select(("unicode",), target_cp)
        font.paste()

        target = font[target_cp]
        if target.references:
            target.unlinkRef()

        # For dotted letters, remove the dot since
        # the accent replaces it.
        if base_cp in (ord("i"), ord("j")):
            _remove_dot(target)

        # Compute placement from the target bounding box
        # (after dot removal when applicable).
        base_bb = target.boundingBox()
        accent_bb = ocrb[accent_cp].boundingBox()
        matrix = _accent_matrix(
            base_bb, accent_bb, accent_cp == _CEDILLA
        )

        # Add transformed accent contours, converting
        # from quadratic (OCR-B ttf) to cubic (OCR-A otf).
        layer = target.foreground
        accent_layer = ocrb[accent_cp].foreground
        for i in range(len(accent_layer)):
            c = accent_layer[i].dup()
            c.is_quadratic = False
            c.transform(matrix)
            layer += c
        target.foreground = layer

        target.width = TARGET_WIDTH
        composed += 1

    print(f"Composed {composed} accented glyphs")


def compose_guillemets(font: Font) -> None:
    """Compose « and » from doubled < and > glyphs."""
    pairs = [
        (0xAB, ord("<")),  # «
        (0xBB, ord(">")),  # »
    ]
    scale = 0.55
    gap = 20

    for target_cp, base_cp in pairs:
        if _glyph_exists(font, target_cp):
            continue

        base = font[base_cp]
        bb = base.boundingBox()
        base_w = bb[2] - bb[0]
        base_h = bb[3] - bb[1]
        base_cy = (bb[1] + bb[3]) / 2

        scaled_w = base_w * scale
        total_w = scaled_w * 2 + gap
        cell_cx = TARGET_WIDTH / 2
        left_x = cell_cx - total_w / 2

        font.createChar(target_cp)
        target = font[target_cp]
        target.clear()
        layer = target.foreground

        for copy_idx in range(2):
            tx = left_x + copy_idx * (scaled_w + gap)
            # Move to origin, scale, move to position.
            m = psMat.translate(-bb[0], -base_cy)
            m = psMat.compose(m, psMat.scale(scale))
            m = psMat.compose(
                m, psMat.translate(tx, base_cy)
            )

            src_layer = base.foreground
            for i in range(len(src_layer)):
                c = src_layer[i].dup()
                c.transform(m)
                layer += c

        target.foreground = layer
        target.width = TARGET_WIDTH

    print("Composed guillemets")


def add_dot_to_zero(font: Font) -> None:
    """Add a centered dot inside the zero glyph."""
    glyph = font[0x30]
    bb = glyph.boundingBox()
    cx = (bb[0] + bb[2]) / 2
    cy = (bb[1] + bb[3]) / 2
    r = (bb[3] - bb[1]) * 0.08

    k = 0.5522847498 * r
    c = fontforge.contour()
    c += fontforge.point(cx, cy + r, True)
    c += fontforge.point(cx + k, cy + r, False)
    c += fontforge.point(cx + r, cy + k, False)
    c += fontforge.point(cx + r, cy, True)
    c += fontforge.point(cx + r, cy - k, False)
    c += fontforge.point(cx + k, cy - r, False)
    c += fontforge.point(cx, cy - r, True)
    c += fontforge.point(cx - k, cy - r, False)
    c += fontforge.point(cx - r, cy - k, False)
    c += fontforge.point(cx - r, cy, True)
    c += fontforge.point(cx - r, cy + k, False)
    c += fontforge.point(cx - k, cy + r, False)
    c.closed = True
    c.is_quadratic = False

    layer = glyph.foreground
    layer += c
    glyph.foreground = layer
    glyph.correctDirection()


def set_metadata(font: Font) -> None:
    """Set font family and naming metadata."""
    font.fontname = "ocrab"
    font.familyname = "ocrab"
    font.fullname = "ocrab Regular"

    # Clear inherited name table entries from the
    # source font so only our names remain.
    for record in list(font.sfnt_names):
        font.appendSFNTName(str(record[0]), str(record[1]), "")

    names = {
        "Family": "ocrab",
        "Fullname": "ocrab Regular",
        "PostScriptName": "ocrab",
        "Preferred Family": "ocrab",
        "Preferred Styles": "Regular",
        "SubFamily": "Regular",
        "UniqueID": "ocrab",
    }
    for key, value in names.items():
        font.appendSFNTName("English (US)", key, value)


def main() -> None:
    print("Opening OCR-A ...")
    ocra = fontforge.open(str(OCRA_PATH))

    print("Opening OCR-B ...")
    ocrb = fontforge.open(str(OCRB_PATH))

    ocrb_codepoints = build_ocrb_codepoints(ocrb)
    replace_symbols(ocra, ocrb, ocrb_codepoints)
    add_ocrb_extras(ocra, ocrb, ocrb_codepoints)
    compose_accented_glyphs(ocra, ocrb)
    compose_guillemets(ocra)
    add_dot_to_zero(ocra)
    set_metadata(ocra)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for output in OUTPUTS:
        print(f"Generating {output} ...")
        ocra.generate(str(output))

    ocra.close()
    ocrb.close()
    print("Done.")


if __name__ == "__main__":
    main()

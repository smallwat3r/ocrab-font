#!/usr/bin/env fontforge -lang=py
"""Build OCR A B - a hybrid of OCR-A and OCR-B.

Keeps A-Z, a-z, 0-9 from OCR-A. Replaces all other glyphs
(punctuation, symbols, brackets, operators, etc.) with their
OCR-B equivalents.
"""

import fontforge
import unicodedata
from pathlib import Path

SOURCES_DIR = Path(__file__).resolve().parent / "sources"
OCRA_PATH = SOURCES_DIR / "OCRA.otf"
OCRB_PATH = SOURCES_DIR / "OCRB.ttf"
OUTPUT_DIR = Path(__file__).resolve().parent / "fonts"
OUTPUT = OUTPUT_DIR / "ocrab.ttf"

TARGET_WIDTH = 723


def is_letter_or_digit(cp):
    """Return True if codepoint is a letter or digit."""
    cat = unicodedata.category(chr(cp))
    return cat.startswith("L") or cat == "Nd"


def build_ocrb_codepoints(ocrb):
    """Return the set of codepoints present in OCR-B."""
    return {g.unicode for g in ocrb.glyphs() if g.unicode >= 0}


def replace_symbols(ocra, ocrb, ocrb_codepoints):
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


def add_dot_to_zero(font):
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


def set_metadata(font):
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


def main():
    print("Opening OCR-A ...")
    ocra = fontforge.open(str(OCRA_PATH))

    print("Opening OCR-B ...")
    ocrb = fontforge.open(str(OCRB_PATH))

    ocrb_codepoints = build_ocrb_codepoints(ocrb)
    replace_symbols(ocra, ocrb, ocrb_codepoints)
    add_dot_to_zero(ocra)
    set_metadata(ocra)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {OUTPUT} ...")
    ocra.generate(str(OUTPUT))

    ocra.close()
    ocrb.close()
    print("Done.")


if __name__ == "__main__":
    main()

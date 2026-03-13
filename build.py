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
    return {
        g.unicode for g in ocrb.glyphs() if g.unicode >= 0
    }


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


def set_metadata(font):
    """Set font family and naming metadata."""
    font.fontname = "ocrab"
    font.familyname = "ocrab"
    font.fullname = "ocrab Regular"

    # Clear inherited name table entries from the
    # source font so only our names remain.
    for record in list(font.sfnt_names):
        font.appendSFNTName(
            str(record[0]), str(record[1]), ""
        )

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
    set_metadata(ocra)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {OUTPUT} ...")
    ocra.generate(str(OUTPUT))

    ocra.close()
    ocrb.close()
    print("Done.")


if __name__ == "__main__":
    main()

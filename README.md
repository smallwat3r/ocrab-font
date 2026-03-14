# ocrab

A monospaced font that combines **OCR-A** letterforms
(letters and digits) with **OCR-B** symbols (punctuation,
operators, brackets, and other non-alphanumeric glyphs).

The result is a hybrid that pairs the distinctive, geometric
character of OCR-A with the more legible symbols of OCR-B.
The zero glyph has a centered dot to distinguish it from O.

Accented characters missing from OCR-A are either taken
directly from OCR-B (ä, ö, ü, ß, æ, ø, Œ, œ, etc.) or
composed by combining OCR-A base letters with OCR-B accent
marks (é, è, ê, ë, à, á, â, ã, ç, ñ, ì, í, î, ï, ò, ó,
ô, õ, ù, ú, û, ý, ÿ, and their uppercase equivalents).

## Preview

![Character set](images/chars.png)

![Code sample](images/code.png)

## Install

The font is available at `fonts/ocrab.ttf`. To install it
to the system font directory:

```sh
make
```

## Nerd Font

A patched variant with
[Nerd Font](https://www.nerdfonts.com/) icons is available
at `fonts/ocrab-nerd-font.ttf`. It is installed alongside
the base font when running `make`.

To rebuild the patched font from source (requires Docker):

```sh
make patch
```

## Credits

ocrab is a derivative work based on:

- **OCR-A** by Matthew Skala (2011-2021), based on code
  by Richard B. Wales (1988-89) and Tor Lillqvist.
  Public domain (Skala's contributions).
- **OCR-B** by Matthew Skala (2011-2021), based on code
  by Norbert Schwarz (1986, 2011).
  Public domain (Skala's contributions). Schwarz's
  original Metafont source is unrestricted.

Both source fonts are from the
[Tsukurimashou project](https://tsukurimashou.org/ocr.php.en).

## License

This font is licensed under the
[SIL Open Font License, Version 1.1](OFL.txt).

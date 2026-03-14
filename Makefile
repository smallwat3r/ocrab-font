UNAME := $(shell uname -s)
ifeq ($(UNAME),Darwin)
    FONT_DIR := ~/Library/Fonts
else ifeq ($(OS),Windows_NT)
    FONT_DIR := $(APPDATA)/Microsoft/Windows/Fonts
else
    FONT_DIR := ~/.local/share/fonts
endif

FONTFORGE  := fontforge
FONTIMAGE  := fontimage
SILICON    := silicon
TTF        := fonts/ocrab.ttf
OTF        := fonts/ocrab.otf
WOFF       := fonts/ocrab.woff
WOFF2      := fonts/ocrab.woff2
OUTPUTS    := $(TTF) $(OTF) $(WOFF) $(WOFF2)
NERD_TTF   := fonts/ocrab-nerd-font.ttf
NERD_OTF   := fonts/ocrab-nerd-font.otf
NERD_WOFF  := fonts/ocrab-nerd-font.woff
NERD_WOFF2 := fonts/ocrab-nerd-font.woff2
NERD_FONTS := $(NERD_TTF) $(NERD_OTF) $(NERD_WOFF) $(NERD_WOFF2)

.PHONY: install build patch images clean
.PHONY: images/chars.png images/code.png $(OUTPUTS)

install:
	mkdir -p $(FONT_DIR)
	cp $(OTF) $(FONT_DIR)/ocrab.otf
	@if [ -f $(NERD_OTF) ]; then \
		cp $(NERD_OTF) $(FONT_DIR)/ocrab-nerd-font.otf; \
	fi
ifeq ($(UNAME),Darwin)
else ifneq ($(OS),Windows_NT)
	fc-cache -f
endif

build: $(OUTPUTS)

$(OUTPUTS): build.py sources/OCRA.otf sources/OCRB.ttf
	$(FONTFORGE) -lang=py -script build.py

patch: $(NERD_FONTS)

$(NERD_TTF): $(TTF)
	docker run --rm --user $(shell id -u):$(shell id -g) \
		-v $(CURDIR)/$(TTF):/in/ocrab.ttf:ro \
		-v $(CURDIR)/fonts:/out \
		nerdfonts/patcher \
		--mono --complete --careful --no-progressbars
	mv fonts/OcrabNerdFontMono-Regular.ttf $@

$(NERD_OTF): $(OTF)
	docker run --rm --user $(shell id -u):$(shell id -g) \
		-v $(CURDIR)/$(OTF):/in/ocrab.otf:ro \
		-v $(CURDIR)/fonts:/out \
		nerdfonts/patcher \
		--mono --complete --careful --no-progressbars
	mv fonts/OcrabNerdFontMono-Regular.otf $@

$(NERD_WOFF): $(NERD_TTF)
	$(FONTFORGE) -c 'f = fontforge.open("$(NERD_TTF)"); \
		f.generate("$@"); f.close()'

$(NERD_WOFF2): $(NERD_TTF)
	$(FONTFORGE) -c 'f = fontforge.open("$(NERD_TTF)"); \
		f.generate("$@"); f.close()'

images: images/chars.png images/code.png

images/chars.png: $(TTF)
	$(FONTIMAGE) --pixelsize 40 \
		--text "ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
		--text "abcdefghijklmnopqrstuvwxyz" \
		--text "0123456789" \
		--text '\!@#$$%^&*()[]{}|;:'"'"'",./<>?~+-=_' \
		-o $@ $<

define SAMPLE_CODE
#include <stdlib.h>

void *memdup(const void *src, size_t len) {
    void *dst = malloc(len);
    if (dst) memcpy(dst, src, len);
    return dst;
}
endef
export SAMPLE_CODE

images/code.png: $(TTF)
	printf '%s\n' "$$SAMPLE_CODE" > /tmp/sample.c
	$(SILICON) /tmp/sample.c -o $@ \
		-f "ocrab" -l c --theme 1337 \
		--no-window-controls --no-line-number \
		--no-round-corner \
		--pad-horiz 40 --pad-vert 30 \
		--background "#111111"

clean:
	rm -f $(OUTPUTS) $(NERD_FONTS)

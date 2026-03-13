UNAME := $(shell uname -s)
ifeq ($(UNAME),Darwin)
    FONT_DIR := ~/Library/Fonts
else ifeq ($(OS),Windows_NT)
    FONT_DIR := $(APPDATA)/Microsoft/Windows/Fonts
else
    FONT_DIR := ~/.local/share/fonts
endif

FONTFORGE := fontforge
FONTIMAGE := fontimage
SILICON   := silicon
OUTPUT    := fonts/ocrab.ttf

.PHONY: install build images clean
.PHONY: images/chars.png images/code.png

install:
	mkdir -p $(FONT_DIR)
	cp fonts/ocrab.ttf $(FONT_DIR)/ocrab.ttf
ifeq ($(UNAME),Darwin)
else ifneq ($(OS),Windows_NT)
	fc-cache -f
endif

build: $(OUTPUT)

$(OUTPUT): build.py sources/OCRA.otf sources/OCRB.ttf
	$(FONTFORGE) -lang=py -script build.py

images: images/chars.png images/code.png

images/chars.png: $(OUTPUT)
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

images/code.png: $(OUTPUT)
	printf '%s\n' "$$SAMPLE_CODE" > /tmp/sample.c
	$(SILICON) /tmp/sample.c -o $@ \
		-f "ocrab" -l c --theme 1337 \
		--no-window-controls --no-line-number \
		--no-round-corner \
		--pad-horiz 40 --pad-vert 30 \
		--background "#111111"

clean:
	rm -f $(OUTPUT)

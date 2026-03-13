UNAME := $(shell uname -s)
ifeq ($(UNAME),Darwin)
    FONT_DIR := ~/Library/Fonts
else ifeq ($(OS),Windows_NT)
    FONT_DIR := $(APPDATA)/Microsoft/Windows/Fonts
else
    FONT_DIR := ~/.local/share/fonts
endif

FONTFORGE := fontforge
OUTPUT    := fonts/ocrab.ttf

.PHONY: install build clean

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

clean:
	rm -f $(OUTPUT)

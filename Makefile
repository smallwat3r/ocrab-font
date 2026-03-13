FONTFORGE := fontforge
OUTPUT    := fonts/ocrab.ttf

.PHONY: all clean install

all: $(OUTPUT)

$(OUTPUT): build.py
	$(FONTFORGE) -lang=py -script build.py

install: $(OUTPUT)
	mkdir -p ~/.local/share/fonts
	cp $(OUTPUT) ~/.local/share/fonts/ocrab.ttf
	fc-cache -f

clean:
	rm -f $(OUTPUT)

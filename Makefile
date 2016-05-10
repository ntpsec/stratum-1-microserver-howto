.SUFFIXES: .html .asc .txt .1

HOSTDIR = esr@login.ibiblio.org:/public/html/catb/esr/faqs/

all: index.html

SNIPPETS = $(shell ls *.py)
index.html: index.txt $(SNIPPETS)
	asciidoc index.txt

MANIFEST = index.html $(SNIPPETS)
manifest:
	@echo $(MANIFEST)

LANDING = $(HOSTDIR)/index
upload: index.html
	scp -q $(SNIPPETS) $(LANDING)
	scp -q index.html $(LANDING)/index.html

VERSION=$(shell sed <index.txt -n '/^version /s///p')
version:
	@echo $(VERSION)

tag:
	git tag $(VERSION) && git push && git push --tags

clean: 
	rm -f index.html

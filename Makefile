.SUFFIXES: .html .asc .txt .1

# If this changes, the corresponding clockmaker.py declarationm must as well.
HOSTDIR = esr@login.ibiblio.org:/public/html/catb/esr/faqs/stratum-1-microserver-howto

all: index.html

SNIPPETS = $(shell ls *.py)
index.html: index.txt $(SNIPPETS)
	asciidoc index.txt

MANIFEST = index.html $(SNIPPETS)
manifest:
	@echo $(MANIFEST)

LANDING = $(HOSTDIR)
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

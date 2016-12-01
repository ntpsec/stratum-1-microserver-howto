.SUFFIXES: .html .asc .txt .1

# If this changes, the corresponding clockmaker declaration and asciidoc macro
# must as well.
HOSTDIR = esr@www.ntpsec.org:/data/www/white-papers/stratum-1-microserver-howto

all: index.html

SNIPPETS = ddimage clockmaker pinup ntp.conf timeservice timeservice.service
index.html: index.txt $(SNIPPETS)
	asciidoc index.txt

MANIFEST = index.html $(SNIPPETS)
manifest:
	@echo $(MANIFEST)

LANDING = $(HOSTDIR)
upload: index.html
	scp -q $(SNIPPETS) *.jpg $(LANDING)
	scp -q index.html $(LANDING)/index.html

VERSION=$(shell sed <index.txt -n '/^version /s///p')
version:
	@echo $(VERSION)

tag:
	git tag $(VERSION) && git push && git push --tags

clean: 
	rm -f index.html

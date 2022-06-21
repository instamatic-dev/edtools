# Minimal makefile for Sphinx documentation
#
# You can set these variables from the command line.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXGEN     ?= sphinx-apidoc
SPHINXPROJ    = edtools
PYTHON        ?= python
PIP           ?= pip
SOURCEDIR     = .
BUILDDIR      = _build
TEMPLATESDIR  = _templates
STATICDIR     = _static

html: conf.py edtools.rst readme.rst
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

readme.rst: ../readme.md
	pandoc --from=markdown --to=rst --output=readme.rst ../readme.md

edtools.rst:
	$(SPHINXGEN) -eTf -t "$(TEMPLATESDIR)" -o "$(SOURCEDIR)" ../edtools

install.rst:
	touch install.rst

clean:
	rm -rvf "$(BUILDDIR)" "$(STATICDIR)/examples" edtools*.rst readme.rst

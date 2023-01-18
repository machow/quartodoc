README.md: README.qmd
	quarto render $<

examples/%/_site: examples/%/_quarto.yml
	quarto render $(dir $<)

docs/examples/%: examples/%/_site
	rm -rf docs/examples/$*
	cp -rv $< $@

docs-build: docs/examples/single-page docs/examples/pkgdown
	cd docs && quarto add --no-prompt ..
	cd docs && python -m quartodoc
	quarto render docs

requirements-dev.txt:
	pip-compile setup.cfg --extra dev -o $@

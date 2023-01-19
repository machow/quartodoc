README.md: README.qmd
	quarto render $<

examples/%/_site: examples/%/_quarto.yml
	python -m quartodoc $<
	quarto render $(dir $<)

docs/examples/%: examples/%/_site
	rm -rf docs/examples/$*
	cp -rv $< $@

docs-build-examples: docs/examples/single-page docs/examples/pkgdown

docs-build: docs-build-examples
	cd docs && quarto add --no-prompt ..
	cd docs && python -m quartodoc
	quarto render docs

requirements-dev.txt:
	pip-compile setup.cfg --extra dev -o $@

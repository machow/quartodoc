EXAMPLE_INTERLINKS=quartodoc/tests/example_interlinks

README.md: README.qmd
	quarto render $<


# These 2 rules are used to generate the example_interlinks folder,
# which contains a full example for the interlinks filter to be tested

$(EXAMPLE_INTERLINKS): scripts/filter-spec/generate_files.py
	python3 $<

$(EXAMPLE_INTERLINKS)/test.qmd: scripts/filter-spec/generate_test_qmd.py
	python3 $<

$(EXAMPLE_INTERLINKS)/test.md: $(EXAMPLE_INTERLINKS)/test.qmd _extensions/interlinks/interlinks.lua
	cd $(EXAMPLE_INTERLINKS) && quarto render test.qmd --to gfm


examples/%/_site: examples/%/_quarto.yml
	cd examples/$* \
		&& quarto add --no-prompt ../.. \
		&& quarto add --no-prompt quarto-ext/shinylive
	cd examples/$* && quartodoc build --config _quarto.yml --verbose
	cd examples/$* && quartodoc interlinks
	quarto render $(dir $<)


docs/examples/%: examples/%/_site
	rm -rf docs/examples/$*
	cp -rv $< $@

docs-build-examples: docs/examples/single-page docs/examples/pkgdown docs/examples/auto-package

docs-build: docs-build-examples
	cd docs && quarto add --no-prompt ..
	cd docs && quartodoc build
	cd docs && quartodoc interlinks
	quarto render docs

test-interlinks: quartodoc/tests/example_interlinks/test.md

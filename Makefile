README.md: README.qmd
	quarto render $<

docs-build:
	cd docs && quarto add --no-prompt ..
	quarto render docs

requirements-dev.txt:
	pip-compile setup.cfg --extra dev -o $@

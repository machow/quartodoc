README.md: README.qmd
	quarto render $<

docs-build:
	cd docs && quarto add --no-prompt ..
	cd docs && python -m quartodoc
	quarto render docs

requirements-dev.txt:
	pip-compile setup.cfg --extra dev -o $@

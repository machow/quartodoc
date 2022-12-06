README.md: README.qmd
	quarto render $<

docs-build:
	quarto render docs

# Overview


[![CI](https://github.com/machow/quartodoc/actions/workflows/ci.yml/badge.svg)](https://github.com/machow/quartodoc/actions/workflows/ci.yml)

**quartodoc** lets you quickly generate Python package API reference
documentation using Markdown and [Quarto](https://quarto.org). quartodoc
is designed as an alternative to
[Sphinx](https://www.sphinx-doc.org/en/master/).

Check out the below screencast for a walkthrough of creating a
documentation site, or read on for instructions.

<div style="position: relative; padding-bottom: 64.5933014354067%; height: 0;">

<iframe src="https://www.loom.com/embed/fb4eb736848e470b8409ba46b514e2ed?sid=31db7652-43c6-4474-bab3-19dea2170775" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">

</iframe>

</div>

<br>

## Installation

``` bash
python -m pip install quartodoc
```

or from GitHub

``` bash
python -m pip install git+https://github.com/machow/quartodoc.git
```

> [!IMPORTANT]
>
> ### Install Quarto
>
> If you haven’t already, you’ll need to [install
> Quarto](https://quarto.org/docs/get-started/) before you can use
> quartodoc.

## Basic use

Getting started with quartodoc takes two steps: configuring quartodoc,
then generating documentation pages for your library.

You can configure quartodoc alongside the rest of your Quarto site in
the
[`_quarto.yml`](https://quarto.org/docs/projects/quarto-projects.html)
file you are already using for Quarto. To [configure
quartodoc](https://machow.github.io/quartodoc/get-started/basic-docs.html#site-configuration),
you need to add a `quartodoc` section to the top level your
`_quarto.yml` file. Below is a minimal example of a configuration that
documents the `quartodoc` package:

<!-- Starter Template -->

``` yaml
project:
  type: website

# tell quarto to read the generated sidebar
metadata-files:
  - reference/_sidebar.yml

# tell quarto to read the generated styles
format:
  html:
    css:
      - reference/_styles-quartodoc.css

quartodoc:
  # the name used to import the package you want to create reference docs for
  package: quartodoc

  # write sidebar and style data
  sidebar: reference/_sidebar.yml
  css: reference/_styles-quartodoc.css

  sections:
    - title: Some functions
      desc: Functions to inspect docstrings.
      contents:
        # the functions being documented in the package.
        # you can refer to anything: class methods, modules, etc..
        - get_object
        - preview
```

Now that you have configured quartodoc, you can generate the reference
API docs with the following command:

``` bash
quartodoc build
```

This will create a `reference/` directory with an `index.qmd` and
documentation pages for listed functions, like `get_object` and
`preview`.

Finally, preview your website with quarto:

``` bash
quarto preview
```

## Rebuilding site

You can preview your `quartodoc` site using the following commands:

First, watch for changes to the library you are documenting so that your
docs will automatically re-generate:

``` bash
quartodoc build --watch
```

Second, preview your site:

``` bash
quarto preview
```

## Looking up objects

Generating API reference docs for Python objects involves two pieces of
configuration:

1.  the package name.
2.  a list of objects for content.

quartodoc can look up a wide variety of objects, including functions,
modules, classes, attributes, and methods:

``` yaml
quartodoc:
  package: quartodoc
  sections:
    - title: Some section
      desc: ""
      contents:
        - get_object        # function: quartodoc.get_object
        - ast.preview       # submodule func: quartodoc.ast.preview
        - MdRenderer        # class: quartodoc.MdRenderer
        - MdRenderer.render # method: quartodoc.MDRenderer.render
        - renderers         # module: quartodoc.renderers
```

The functions listed in `contents` are assumed to be imported from the
package.

## Learning more

Go [to the next
page](https://machow.github.io/quartodoc/get-started/basic-docs.html) to
learn how to configure quartodoc sites, or check out these handy pages:

- [Examples
  page](https://machow.github.io/quartodoc/examples/index.html): sites
  using quartodoc.
- [Tutorials
  page](https://machow.github.io/quartodoc/tutorials/index.html):
  screencasts of building a quartodoc site.
- [Docstring issues and
  examples](https://machow.github.io/quartodoc/get-started/docstring-examples.html):
  common issues when formatting docstrings.
- [Programming, the big
  picture](https://machow.github.io/quartodoc/get-started/dev-big-picture.html):
  the nitty gritty of how quartodoc works, and how to extend it.

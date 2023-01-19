import click
import contextlib
import os

from pathlib import Path

from .autosummary import Builder


@contextlib.contextmanager
def chdir(new_dir):
    prev = os.getcwd()
    os.chdir(new_dir)
    try:
        yield new_dir
    finally:
        os.chdir(prev)


@click.command()
@click.argument("config", default="_quarto.yml")
@click.option("--dry-run", is_flag=True, default=False)
def build(config, dry_run):
    builder = Builder.from_quarto_config(config)

    if dry_run:
        click.echo(builder.render_index())
    else:
        with chdir(Path(config).parent):
            builder.build()


if __name__ == "__main__":
    build()

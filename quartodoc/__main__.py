import click
import contextlib
import os
import sphobjinv as soi
import yaml

from pathlib import Path

from quartodoc import Builder, convert_inventory


@contextlib.contextmanager
def chdir(new_dir):
    prev = os.getcwd()
    os.chdir(new_dir)
    try:
        yield new_dir
    finally:
        os.chdir(prev)


@click.group()
def cli():
    pass


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


@click.command()
@click.argument("config", default="_quarto.yml")
@click.option("--dry-run", is_flag=True, default=False)
def interlinks(config, dry_run):
    cfg = yaml.safe_load(open(config))
    interlinks = cfg.get("interlinks", None)

    cache = cfg.get("cache", "_inv")

    p_root = Path(config).parent

    if interlinks is None:
        raise KeyError("No interlinks field found in your quarto config.")

    for k, v in interlinks["sources"].items():

        # TODO: user shouldn't need to include their own docs in interlinks
        if v["url"] == "/":
            continue

        url = v["url"] + v.get("inv", "objects.inv")
        inv = soi.Inventory(url=url)

        p_dst = p_root / cache / f"{k}_objects.json"
        p_dst.parent.mkdir(exist_ok=True, parents=True)

        convert_inventory(inv, p_dst)


cli.add_command(build)
cli.add_command(interlinks)


if __name__ == "__main__":
    cli()

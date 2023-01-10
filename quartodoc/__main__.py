import click

from .autosummary import Builder


@click.command()
@click.argument("config", default="_quarto.yml")
@click.option("--dry-run", is_flag=True, default=False)
def build(config, dry_run):
    builder = Builder.from_quarto_config(config)

    if dry_run:
        click.echo(builder.render_index())
    else:
        builder.build()


if __name__ == "__main__":
    build()

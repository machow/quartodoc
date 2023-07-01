import click
import contextlib
import os
import time
import sphobjinv as soi
import yaml
import importlib
from pathlib import Path
from watchdog.observers import Observer
from functools import partial
from watchdog.events import FileSystemEventHandler
from quartodoc import Builder, convert_inventory

def get_package_path(package_name):
    """
    Get the path to a package installed in the current environment.
    """
    try:
        lib = importlib.import_module(package_name)
        return lib.__path__[0]
    except ModuleNotFoundError:
        raise ModuleNotFoundError(f"Package {package_name} not found.  Please install it in your environment.")

class FileChangeHandler(FileSystemEventHandler):
    """
    A handler for file changes.
    """
    def __init__(self, callback):
        self.callback = callback
    
    @classmethod
    def print_event(cls, event):
        print(f'Rebuilding docs.  Detected: {event.event_type} path : {event.src_path}')

    def on_modified(self, event):
        self.print_event(event)
        self.callback()

    def on_created(self, event):
        self.print_event(event)
        self.callback()

def _enable_logs():
    import logging
    import sys

    root = logging.getLogger("quartodoc")
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


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





@click.command(help="This function builds a project based on the given configuration file (_quarto.yml by default).")
@click.argument("config", default="_quarto.yml")
@click.option("--filter", nargs=1, default="*", help="Specify the filter to select specific files. The default is '*' which selects all files.")
@click.option("--dry-run", is_flag=True, default=False, help="If set, prevents new documents from being generated.")
@click.option("--watch", is_flag=True, default=False, help="If set, the command will keep running and watch for changes in the package directory.")
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
def build(config, filter, dry_run, watch, verbose):
    """
    This function builds a project based on the given configuration file (_quarto.yml by default).
    """
    if verbose:
        _enable_logs()

    builder = Builder.from_quarto_config(config)
    doc_build = partial(builder.build, filter=filter)

    if dry_run:
        pass
    else:
        with chdir(Path(config).parent):
            if watch:
                pkg_path = get_package_path(builder.package)
                print(f"Watching {pkg_path} for changes...")
                event_handler = FileChangeHandler(callback=doc_build)
                observer = Observer()
                observer.schedule(event_handler, pkg_path, recursive=True)
                observer.start()
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    observer.stop()
                observer.join()
            else:   
                doc_build()

@click.command()
@click.argument("config", default="_quarto.yml")
@click.option("--dry-run", is_flag=True, default=False)
def interlinks(config, dry_run):
    cfg = yaml.safe_load(open(config))
    interlinks = cfg.get("interlinks", None)

    cache = cfg.get("cache", "_inv")

    p_root = Path(config).parent

    if interlinks is None:
        print("No interlinks field found in your quarto config. Quitting.")
        return

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

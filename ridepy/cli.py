import typer

from pathlib import Path
from typing import Optional

from ridepy.extras.io_utils import (
    update_filenames as _update_filenames,
    update_events_files as _update_events_files,
)

cli = typer.Typer()


@cli.command()
def update_filenames(
    directory: Optional[Path] = typer.Argument(
        None, dir_okay=True, file_okay=False, exists=True
    )
):
    """
    Update filenames and JSON structure to up-to-date simulation ids.

    This reads all `.json` files, tries to parse the possibly
    outdated format and generates a simulation id according
    to the current scheme. Afterwards, new JSON files are stored using the
    current format at `<new id>.json`.
    The simulation data files ending with `.jsonl` are not modified. Instead,
    symbolic links are created, pointing from `<new id>.jsonl` to `<old id>.jsonl`.
    """
    if directory is None:
        directory = Path.cwd()
    else:
        directory = Path(directory).expanduser()

    _update_filenames(directory)


@cli.command()
def update_events_files(
    directory: Optional[Path] = typer.Option(
        None, dir_okay=True, file_okay=False, exists=True
    ),
):
    """
    Update events files (*.jsonl) to current, flattened structure.
    """
    if directory is None:
        directory = Path.cwd()
    else:
        directory = Path(directory).expanduser()

    _update_events_files(directory)


@cli.callback()
def main():
    """ridepy command-line interface"""

    pass


if __name__ == "__main__":
    cli()

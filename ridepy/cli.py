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
    directory: Optional[Path] = typer.Option(
        None, dir_okay=True, file_okay=False, exists=True
    )
):
    """
    Update filenames to current simulation ids.
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
    Update events files (*.jsonl) to current, flattened structure
    """
    if directory is None:
        directory = Path.cwd()
    else:
        directory = Path(directory).expanduser()

    _update_events_files(directory)


@cli.callback()
def main():
    """ridepy command-line interface"""


if __name__ == "__main__":
    cli()

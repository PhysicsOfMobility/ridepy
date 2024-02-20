import typer
import gnupg
import os
import re
import subprocess
import tomli
import tomli_w
import packaging.version

try:
    # only relevant for dev mode
    import pygit2
except ImportError:
    pass

import pandas as pd

from copy import deepcopy
from pathlib import Path
from typing import Optional, List, Union, Annotated
from pygit2 import (
    GIT_STATUS_WT_MODIFIED,
    GIT_STATUS_INDEX_MODIFIED,
    GIT_MERGE_ANALYSIS_UP_TO_DATE,
)
from enum import Enum

from ridepy.extras.io import read_params_json
from ridepy.extras.io_utils import (
    update_filenames as _update_filenames,
    update_events_files as _update_events_files,
)

from ridepy.extras.simulation_set import (
    perform_single_simulation,
    perform_single_analysis,
)

app = typer.Typer()

hpc_app = typer.Typer()
app.add_typer(hpc_app, name="hpc")

dev_app = typer.Typer()
app.add_typer(dev_app, name="dev")


@app.command()
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


@app.command()
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


@hpc_app.command()
def simulate(
    input_directory: Path = typer.Argument(
        ...,
        help="Directory containing the parameter files for the simulation",
        dir_okay=True,
        file_okay=False,
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    output_directory: Path = typer.Argument(
        ...,
        help="Directory to store the simulation results in",
        dir_okay=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
    ),
    simulation_id: str = typer.Argument(..., help="ID of a single simulation."),
):
    """
    Perform a single simulation run reading the simulation
    parameters from a file and writing the output to disk.

    Which file the parameters are read from is determined by
    the SIMULATION_ID argument.

    The parameter files must be located in the INPUT_DIRECTORY,
    and be named like "<SIMULATION_ID>_params.json"
    """

    params_path = input_directory / f"{simulation_id}_params.json"

    params_json = read_params_json(params_path)
    perform_single_simulation(params=params_json, data_dir=output_directory)


@hpc_app.command()
def analyze(
    output_directory: Path = typer.Argument(
        ...,
        help="Directory to read the simulation results in",
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
        resolve_path=True,
    ),
    simulation_ids: List[str] = typer.Argument(..., help="One or many simulation IDs."),
    compute_system_quantities: bool = typer.Option(
        False, help="Compute system quantities"
    ),
):
    """
    Analyze a single simulation run. This reads the simulation data
    from the params and event files and writes the output to disk
    in the form of files in parquet format.

    Which file the simulation results and parameters are read from
    is determined by the SIMULATION_ID argument.

    The result and parameter files must be located in the OUTPUT_DIRECTORY,
    and be named like "<SIMULATION_ID>.jsonl" and "<SIMULATION_ID>_params.json",
    respectively.
    """

    tasks = {"stops", "requests", "vehicle_quantities"}
    if compute_system_quantities:
        tasks.add("system_quantities")

    system_quantities = []
    for simulation_id in simulation_ids:
        _, sys_quant = perform_single_analysis(
            sim_id=simulation_id,
            data_dir=output_directory,
            tasks_if_existent=tasks,
        )
        system_quantities.append(sys_quant)

    if compute_system_quantities:
        system_quantities_df = pd.DataFrame(system_quantities, index=simulation_ids)
        system_quantities_df.rename_axis("simulation_id", inplace=True)
        system_quantities_df.to_parquet(output_directory / "system_quantities.pq")


class VersionChoices(str, Enum):
    major = "major"
    minor = "minor"
    patch = "patch"
    post = "post"


@dev_app.command()
def publish_release(
    version_to_bump: Annotated[
        VersionChoices, typer.Argument(help="The version to bump", case_sensitive=False)
    ],
    version: Annotated[
        str,
        typer.Option(
            "--version",
            "-v",
            help="The version number to be published. Example: '1.1.2'",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            is_flag=True,
            help="If set, the release will not be published, only the command to do so will be printed.",
        ),
    ] = False,
):
    """
    Publish a new RidePy release on GitHub.

    Requirements

    - The current branch must be `master`.
    - There must be no uncommitted changes.
    - The version in `pyproject.toml` must match the latest git tag.
    - The new version must be greater than the current one.
    - The `gh` command must be available and authenticated.
    - Git push access to the upstream ridepy repository must be available using the SSH agent credentials.
    - A private PGP key must be available to sign the commit.

    """
    working_dir = os.getcwd()
    repository_path = Path(pygit2.discover_repository(working_dir)).parent
    repo = pygit2.Repository(repository_path)

    if not repo.head.shorthand == "master":
        raise ValueError("Not on master branch, aborting.")

    if repo.status():
        raise ValueError("Uncommitted changes, aborting.")

    repo.remotes["upstream"].fetch(
        callbacks=pygit2.RemoteCallbacks(credentials=pygit2.KeypairFromAgent("git")),
    )
    remote_master_id = repo.lookup_reference("refs/remotes/upstream/master").target
    merge_result, _ = repo.merge_analysis(remote_master_id)

    if not merge_result == GIT_MERGE_ANALYSIS_UP_TO_DATE:
        raise ValueError(
            "Local master branch is not up-to-date with upstream, aborting."
        )

    pyproject_path = repository_path / "pyproject.toml"
    print(f"Discovered pyproject.toml at {pyproject_path}")

    with pyproject_path.open("rb") as fp:
        pyproject = tomli.load(fp)

    current_version_pyproject = packaging.version.parse(pyproject["project"]["version"])
    regex = re.compile(r"^refs/tags/v(.+)$")
    git_versions = []
    for r in repo.references:
        match = regex.match(r)
        if match is not None:
            git_versions.append(packaging.version.parse(match.groups()[0]))

    current_version_git = sorted(git_versions)[-1]

    if current_version_git != current_version_pyproject:
        raise ValueError(
            f"Version mismatch between pyproject.toml and git tags: "
            f"{current_version_pyproject} != {current_version_git}"
        )

    if version is None:
        if version_to_bump == "major":
            version = f"{current_version_git.major + 1}.0"
        if version_to_bump == "minor":
            version = f"{current_version_git.major}.{current_version_git.minor + 1}"
        if version_to_bump == "patch":
            version = (
                f"{current_version_git.major}.{current_version_git.minor}"
                f".{current_version_git.micro + 1}"
            )
        if version_to_bump == "post":
            version = (
                f"{current_version_git.major}.{current_version_git.minor}"
                f".{current_version_git.micro}"
                f".post{(current_version_git.post or 0) + 1}"
            )

    version = packaging.version.parse(version)

    print(f"New version is {version}")

    if current_version_git >= version:
        raise ValueError(
            f"New version ({version}) must be greater then "
            f"the current one ({current_version_git})."
        )
    else:
        print(f"Determined current version at {current_version_git}, continuing...")

    version = str(version)

    pyproject["project"]["version"] = version

    if not dry_run:
        with pyproject_path.open("wb") as fp:
            tomli_w.dump(pyproject, fp, multiline_strings=True)
            print("Updated pyproject.toml")
    else:
        print("Would update pyproject.toml, instead here comes the printout:\n")
        print(tomli_w.dumps(pyproject, multiline_strings=True))

    assert repo.status() == {
        "pyproject.toml": GIT_STATUS_WT_MODIFIED
    }, "pyproject.toml not modified. Aborting."

    repo.index.add("pyproject.toml")
    repo.index.write()

    assert repo.status() == {
        "pyproject.toml": GIT_STATUS_INDEX_MODIFIED
    }, "pyproject.toml not staged. Aborting."

    commit_string = repo.create_commit_string(
        repo.default_signature,  # author
        repo.default_signature,  # committer
        f"ridepy {version}",  # message
        repo.index.write_tree(),  # tree
        [repo.head.target],  # parents
    )

    gpg = gnupg.GPG()
    signed_commit = gpg.sign(commit_string, detach=True)
    commit = repo.create_commit_with_signature(
        commit_string, signed_commit.data.decode("utf-8")
    )
    repo.head.set_target(commit)

    print("Created signed commit.")

    assert not repo.status(), "Uncommitted changes after commit. Aborting."

    repo.remotes["upstream"].push(
        ["refs/heads/master"],
        callbacks=pygit2.RemoteCallbacks(credentials=pygit2.KeypairFromAgent("git")),
    )

    print("Pushed to upstream/master.")

    gh_cmd = [
        "gh",
        "release",
        "create",
        f"v{version}",
        "--generate-notes",
        "-t",
        f"ridepy {version}",
    ]
    if not dry_run:
        subprocess.run(gh_cmd)
    else:
        print("Would execute: " + " ".join(gh_cmd))

    print("Created release tag and GitHub release.")
    print("Done.")


@app.callback()
def main():
    """ridepy command-line interface"""

    pass


if __name__ == "__main__":
    app()

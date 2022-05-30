import pandas as pd
import typer

from pathlib import Path
from typing import Optional, List, Union

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

    system_quantities = []
    for simulation_id in simulation_ids:
        _, sys_quant = perform_single_analysis(
            sim_id=simulation_id,
            data_dir=output_directory,
            update_existing=False,
            compute_system_quantities=compute_system_quantities,
            compute_vehicle_quantities=True,
        )
        system_quantities.append(sys_quant)

    if compute_system_quantities:
        system_quantities_df = pd.DataFrame(system_quantities, index=simulation_ids)
        system_quantities_df.rename_axis("simulation_id", inplace=True)
        system_quantities_df.to_parquet(output_directory / "system_quantities.pq")


@app.callback()
def main():
    """ridepy command-line interface"""

    pass


if __name__ == "__main__":
    app()

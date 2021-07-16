import os
import json
import shutil
import warnings
import subprocess

import functools as ft
import operator as op

from pathlib import Path

from ridepy.extras.io import read_params_json, create_params_json, ParamsJSONDecoder
from ridepy.extras.simulation_set import SimulationSet, make_file_path
from ridepy.util import make_sim_id


def update_filenames(target_directory_path: Path):
    """
    With a directory containing simulation output (JSONL events files and params JSON files),
    this will try to update the simulation ids/base names to the id scheme of the current version of ridepy.

    The process is non-invasive in that it either creates symlinks or creates new files. The existing
    files are neither renamed nor is their content modified.

    Parameters
    ----------
    target_directory_path
        Directory to operate in.
    """
    get_params_path = ft.partial(
        make_file_path, directory=target_directory_path, suffix="_params.json"
    )
    get_events_path = ft.partial(
        make_file_path, directory=target_directory_path, suffix=".jsonl"
    )

    old_ids = {
        str(p).split("/")[-1].split(".")[0].split("_")[0]
        for p in target_directory_path.glob("*.json")
        if not os.path.islink(p)
    }

    new_default_base_params = SimulationSet(data_dir=Path()).default_base_params

    for old_id in old_ids:
        old_params_path = get_params_path(old_id)
        old_events_path = get_events_path(old_id)

        if not old_params_path:
            warnings.warn(
                f"parameter file for simulation id {old_id} missing, skipping"
            )
            continue

        old_params_json = old_params_path.read_text(encoding="U8")

        params_json = old_params_json.replace("thesimulator", "ridepy")

        params = json.loads(params_json, cls=ParamsJSONDecoder)
        for outer_key, default_inner_dict in new_default_base_params.items():
            params[outer_key] = params.get(outer_key, default_inner_dict)
            for inner_key, inner_value in default_inner_dict.items():
                params[outer_key][inner_key] = params[outer_key].get(
                    inner_key, default_inner_dict.get(inner_key)
                )

        new_params_json = create_params_json(params=params)
        new_id = make_sim_id(new_params_json)
        new_params_path = get_params_path(new_id)
        new_events_path = get_events_path(new_id)

        if new_params_json == old_params_json:
            try:
                os.symlink(old_params_path, new_params_path)
            except FileExistsError:
                warnings.warn(
                    f"parameter file for simulation id {old_id} already up to date, skipping"
                )
        else:
            new_params_path.write_text(new_params_json)

        if not old_events_path:
            warnings.warn(f"{old_events_path} missing, skipping")
            continue
        else:
            try:
                os.symlink(old_events_path, new_events_path)
            except FileExistsError:
                warnings.warn(
                    f"events file for simulation id {old_id} already up to date, skipping"
                )


def update_events_files(target_directory_path: Path, remove_old: bool = False):
    sim_ids = (
        events_path.stem
        for events_path in target_directory_path.glob("*.jsonl")
        if "_old" not in str(events_path)
    )

    get_events_path = ft.partial(
        make_file_path, directory=target_directory_path, suffix=".jsonl"
    )
    get_old_events_path = ft.partial(
        make_file_path, directory=target_directory_path, suffix="_old.jsonl"
    )

    jq_options = ["-r", "-c"]
    jq_expr = "{event_type:keys[0]}+.[keys[0]]"

    for sim_id in sim_ids:
        events_path = get_events_path(sim_id)
        old_events_path = get_old_events_path(sim_id)

        shutil.move(events_path, old_events_path)

        print(f"Reformatting {sim_id}...", end="", flush=True)
        try:
            assert subprocess.run(
                ["jq", *jq_options, jq_expr, str(old_events_path)],
                stdout=events_path.open("w"),
            )
            print("done.")
        except:
            shutil.move(old_events_path, events_path)
        else:
            if remove_old:
                old_events_path.unlink()

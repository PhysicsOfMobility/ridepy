import logging
import os
import warnings

import loky
from time import time

import operator as op
import functools as ft
import itertools as it
import pandas as pd

from collections import defaultdict
from copy import deepcopy
from typing import (
    Iterator,
    Any,
    Optional,
    Iterable,
    Union,
    Sequence,
    Callable,
    Mapping,
)
from pathlib import Path

from ridepy.util import make_sim_id
from ridepy.util.analytics import (
    get_system_quantities,
    get_vehicle_quantities,
    get_stops_and_requests_from_events_dataframe,
)
from ridepy.util.dispatchers import BruteForceTotalTravelTimeMinimizingDispatcher
from ridepy.util.dispatchers_cython import (
    BruteForceTotalTravelTimeMinimizingDispatcher as CyBruteForceTotalTravelTimeMinimizingDispatcher,
)
from ridepy.util.spaces import Euclidean2D
from ridepy.util.spaces_cython import Euclidean2D as CyEuclidean2D
from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.data_structures import (
    TransportationRequest,
)
from ridepy.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
)
from ridepy.vehicle_state import VehicleState
from ridepy.vehicle_state_cython import VehicleState as CyVehicleState
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.extras.io import (
    create_params_json,
    save_events_json,
    read_params_json,
)

logger = logging.getLogger(__name__)


def make_file_path(sim_id: str, directory: Path, suffix: str) -> Path:
    return directory / f"{sim_id}{suffix}"


def get_params(
    directory: Path, sim_id: str, param_path_suffix: str = "_params.json"
) -> dict:
    return read_params_json(make_file_path(sim_id, directory, param_path_suffix))


def perform_single_analysis(
    sim_id: str,
    data_dir: Path,
    tasks_if_not_existent: Optional[Iterable[str]] = None,
    tasks_if_existent: Optional[Iterable[str]] = None,
    param_path_suffix: str = "_params.json",
    event_path_suffix: str = ".jsonl",
    stops_path_suffix: str = "_stops.pq",
    requests_path_suffix: str = "_requests.pq",
    vehicle_quantities_path_suffix: str = "_vehicle_quantities.pq",
) -> tuple[str, dict[str, Any]]:
    """
    Compute stops, requests, vehicle quantities, and system quantities from
    simulation events.

    Parameters
    ----------
    sim_id
        Simulation ID
    data_dir
        Directory from which to read the events and to which to write the resulting
        parquet output files
    tasks_if_not_existent
        Collection of tasks to perform if the respective output files do not exist.
        Valid entries are 'stops', 'requests', 'vehicle_quantities', and
        'system_quantities'. If None, everything is computed if not existent.
    tasks_if_existent
        Collection of tasks to perform even if the respective output files do exist,
        i.e. tasks to recompute. Valid entries are 'stops', 'requests',
        'vehicle_quantities', and 'system_quantities'. If None, nothing is recomputed.
    param_path_suffix
        Appending this suffix to the simulation ID yields the path to the JSON parameter
        file.
    event_path_suffix
        Appending this suffix to the simulation ID yields the path to the JSONL
        event file.
    stops_path_suffix
        Appending this suffix to the simulation ID yields the path to the parquet
        stops file.
    requests_path_suffix
        Appending this suffix to the simulation ID yields the path to the parquet
        requests file.
    vehicle_quantities_path_suffix
        Appending this suffix to the simulation ID yields the path to the \
        parquet vehicle quantities file.

    Returns
    -------
    sim_id
        Simulation ID
    system_quantities
        Dictionary containing the computed system quantities as entries
    """
    stops_path = make_file_path(sim_id, data_dir, stops_path_suffix)
    requests_path = make_file_path(sim_id, data_dir, requests_path_suffix)
    vehicle_quantities_path = make_file_path(
        sim_id, data_dir, vehicle_quantities_path_suffix
    )

    tasks = set()

    tasks_if_not_existent = tasks_if_not_existent or {
        "stops",
        "requests",
        "vehicle_quantities",
        "system_quantities",
    }
    tasks_if_existent = tasks_if_existent or set()

    if "stops" in tasks_if_not_existent and not stops_path.exists():
        tasks.add("stops")
    if "requests" in tasks_if_not_existent and not requests_path.exists():
        tasks.add("requests")
    if (
        "vehicle_quantities" in tasks_if_not_existent
        and not vehicle_quantities_path.exists()
    ):
        tasks.add("vehicle_quantities")
    if "system_quantities" in tasks_if_not_existent:
        tasks.add("system_quantities")

    tasks |= tasks_if_existent

    system_quantities = {}
    if tasks:
        params = get_params(data_dir, sim_id, param_path_suffix=param_path_suffix)
        space = params["general"]["space"]

        if "stops" in tasks or "requests" in tasks:
            stops, requests = get_stops_and_requests_from_events_dataframe(
                events_df=pd.read_json(
                    make_file_path(sim_id, data_dir, event_path_suffix), lines=True
                ),
                space=space,
            )
        else:
            stops = pd.read_parquet(stops_path)
            requests = pd.read_parquet(requests_path)

        if "vehicle_quantities" in tasks:
            vehicle_quantities = get_vehicle_quantities(stops, requests)
            vehicle_quantities.to_parquet(vehicle_quantities_path)

        if "system_quantities" in tasks:
            system_quantities = get_system_quantities(stops, requests, params)

        if "stops" in tasks:
            if space.n_dim > 1:
                stops["location"] = stops[~stops["location"].isna()]["location"].map(
                    list
                )
            stops.to_parquet(stops_path)

        if "requests" in tasks:
            if space.n_dim > 1:
                if ("submitted", "origin") in requests:
                    requests["submitted", "origin"] = requests[
                        ~requests["submitted", "origin"].isna()
                    ]["submitted", "origin"].map(list)

                if ("accepted", "origin") in requests:
                    requests["accepted", "origin"] = requests[
                        ~requests["accepted", "origin"].isna()
                    ]["accepted", "origin"].map(list)

                if ("submitted", "destination") in requests:
                    requests["submitted", "destination"] = requests[
                        ~requests["submitted", "destination"].isna()
                    ]["submitted", "destination"].map(list)

                if ("accepted", "destination") in requests:
                    requests["accepted", "destination"] = requests[
                        ~requests["accepted", "destination"].isna()
                    ]["accepted", "destination"].map(list)

            requests.to_parquet(requests_path)

    return sim_id, system_quantities


def perform_single_simulation(
    params: dict[str, dict[str, Any]],
    *,
    data_dir: Path,
    jsonl_chunksize: int = 1000,
    debug: bool = False,
    param_path_suffix: str = "_params.json",
    event_path_suffix: str = ".jsonl",
    dry_run: bool = False,
) -> str:
    """
    Execute a single simulation run based on a parameter dictionary
    and save parameters and result events to disk.

    Parameters
    ----------
    params
        Parameter dictionary to base the simulation on. Must contain the following keys:

        - ``general``
            - either ``n_reqs``  or ``t_cutoff``
            - ``seat_capacity``
            - (``initial_location`` and ``n_vehicles``) or ``initial_locations``
            - ``space``
            - ``transportation_request_cls``
            - ``vehicle_state_cls``
            - ``fleet_state_cls``
        - ``request_generator``
            - ``request_generator_cls``
        - ``dispatcher``
            - ``dispatcher_cls``
            - ...
    data_dir
        Existing directory in which to store parameters and events.
    jsonl_chunksize
        Number of simulation events to keep in memory before writing them to disk at once.
    debug
        Print debug info to stdout.
    param_path_suffix
        Parameters will be stored under "data_dir/<simulation_id><suffix>"
    event_path_suffix
        Simulation events will be stored under "data_dir/<simulation_id><event_path_suffix>"
    dry_run
        If True, do not actually simulate. Just pretend to and return the corresponding ID.

    Returns
    -------
    simulation ID
    """
    # we need a pseudorandom id that does not change if this function is called with the same params
    # the following does not guarantee a lack of collisions, and will fail if non-ascii characters are involved.
    tick = time()
    params_json = create_params_json(params=params)
    sim_id = make_sim_id(params_json)
    event_path = data_dir / f"{sim_id}{event_path_suffix}"
    param_path = data_dir / f"{sim_id}{param_path_suffix}"

    if (
        param_path.exists()
        and (params_json_ := param_path.read_text())
        and params_json_[-1] == "}"
    ):
        # assume that a previous simulation run already exists. this works because we write
        # to param_path *after* a successful simulation run.
        logger.info(
            f"Pre-existing param json exists for {params_json=} at {param_path=}, skipping simulation"
        )
        return sim_id
    else:
        logger.info(
            f"No pre-existing param json exists for {params_json=} at {param_path=}, running simulation"
        )
        if event_path.exists():
            logger.info(
                f"Potentially incomplete simulation data exists at {event_path=}, this will be overwritten"
            )
            event_path.unlink()

    space = params["general"]["space"]
    request_generator_cls = params["request_generator"].pop("request_generator_cls")
    rg = request_generator_cls(
        space=space,
        request_class=params["general"]["transportation_request_cls"],
        **params["request_generator"],
    )

    dispatcher = params["dispatcher"].pop("dispatcher_cls")
    if (
        params["general"].get("n_vehicles") is not None
        and params["general"].get("initial_location") is not None
        and params["general"].get("initial_locations") is None
    ):
        initial_locations = {
            vehicle_id: params["general"]["initial_location"]
            for vehicle_id in range(params["general"]["n_vehicles"])
        }
    elif (
        params["general"].get("n_vehicles") is None
        and params["general"].get("initial_location") is None
        and params["general"].get("initial_locations") is not None
    ):
        initial_locations = params["general"]["initial_locations"]
    else:
        raise ValueError(
            "Must *either* specify `n_vehicles` *and* `initial_location` *or* `initial_locations`"
        )

    fs = params["general"]["fleet_state_cls"](
        initial_locations=initial_locations,
        space=space,
        dispatcher=dispatcher(loc_type=space.loc_type, **params["dispatcher"]),
        seat_capacities=params["general"]["seat_capacity"],
        vehicle_state_class=params["general"]["vehicle_state_cls"],
    )

    # NOTE: this string is matched for testing
    if debug:
        print(f"Simulating run on process {os.getpid()} @ \n{params!r}\n")

    if not dry_run:
        if (
            params["general"]["n_reqs"] is not None
            and params["general"]["t_cutoff"] is None
        ):
            simulation = fs.simulate(it.islice(rg, params["general"]["n_reqs"]))
        elif (
            params["general"]["n_reqs"] is None
            and params["general"]["t_cutoff"] is not None
        ):
            simulation = fs.simulate(rg, t_cutoff=params["general"]["t_cutoff"])
        else:
            raise ValueError("Must *either* specify `n_reqs` *or* `t_cutoff`")

        while chunk := list(it.islice(simulation, jsonl_chunksize)):
            save_events_json(jsonl_path=event_path, events=chunk)

        with open(str(param_path), "w") as f:
            f.write(params_json)
    tock = time()
    if debug:
        print(f"Simulation run on process {os.getpid()} took {tock-tick} seconds\n")
    return sim_id


def simulate_parameter_combinations(
    *,
    param_combinations: Iterator[dict[str, dict[str, Sequence[Any]]]],
    data_dir: Union[str, Path],
    debug: bool = False,
    max_workers: Optional[int] = None,
    process_chunksize: int = 1,
    jsonl_chunksize: int = 1000,
    event_path_suffix: str = ".jsonl",
    param_path_suffix: str = "_params.json",
    dry_run: bool = False,
):
    """
    Run simulations for different parameter combinations using multiprocessing.

    Parameters
    ----------
    param_combinations
        An iterable of parameter configurations. For more detail see :ref:`Executing Simulations`
    data_dir
        Directory in which to store the parameters and events.
    debug
        Print debug info.
    max_workers
        Maximum number of multiprocessing workers. Defaults to number of processors
        on the machine if `None` or not given.
    process_chunksize
        Number of simulations to submit to each multiprocessing worker at a time.
    jsonl_chunksize
        Maximum number of events to keep in memory before saving to disk
    param_path_suffix
        Parameters will be stored under "data_dir/<simulation_id><suffix>"
    event_path_suffix
        Simulation events will be stored under "data_dir/<simulation_id><event_path_suffix>"
    dry_run
        If True, do not actually simulate. Just pretend to and return the corresponding IDs.

    Returns
    -------
        List of simulation IDs. See the docstring of `.SimulationSet` for more detail.
    """
    with loky.get_reusable_executor(max_workers=max_workers) as executor:
        sim_ids = list(
            executor.map(
                ft.partial(
                    perform_single_simulation,
                    debug=debug,
                    jsonl_chunksize=jsonl_chunksize,
                    data_dir=data_dir,
                    param_path_suffix=param_path_suffix,
                    event_path_suffix=event_path_suffix,
                    dry_run=dry_run,
                ),
                param_combinations,
                chunksize=process_chunksize,
            )
        )
    return sim_ids


class SimulationSet:
    """
    A set of simulations. The parameter space is defined through constant `base_params`,
    zipped `zip_params` and cartesian product `product_params`. A set of a single simulation
    is also allowed. Through `SimulationSet.run`, configurable multiprocessing is implemented,
    allowing for parallelization of simulation runs at different parameters.
    """

    @staticmethod
    def _two_level_dict_update(
        base_dict: dict[str, dict[str, Any]], update_dict: dict[str, dict[str, Any]]
    ) -> dict:
        """
        Update two-level nested dictionary with deepcopying,
        where `update_dict` overwrites entries in `base_dict`.

        Example
        -------

        .. code-block:: python

            SimulationSet._two_level_dict_update(
                {"a": {"b": 5, 6: 8}}, {"a": {6: "fooo", 8: "baaar"}, "baz": {"6": 6}}
            )

        yields

        .. code-block:: python

            {"a": {"b": 5, 6: "fooo", 8: "baaar"}, "baz": {"6": 6}}


        Parameters
        ----------
        base_dict
            two-level nested dict to update
        update_dict
            two-level nested dict which overwrites entries in base_dict

        Returns
        -------
        updated deepcopy of base_dict

        """
        d = deepcopy(base_dict)
        # This sorted is needed otherwise detection of pre existing simulation run does not work.
        for outer_key in sorted(set(base_dict) | set(update_dict)):
            d[outer_key] = base_dict.get(outer_key, {}) | update_dict.get(outer_key, {})
        return d

    @staticmethod
    def _zip_params_equal_length(
        zip_params: dict[str, dict[str, Sequence[Any]]]
    ) -> bool:
        """
        Evaluate whether the sequences in the inner dict are of equal length.

        Parameters
        ----------
        zip_params

        Returns
        -------
        True if sequences are of equal length, False otherwise

        """

        if zip_params:
            g = it.groupby(
                len(inner_value)
                for inner_dict in zip_params.values()
                for inner_value in inner_dict.values()
            )
            return next(g, True) and not next(g, False)
        else:
            return True

    @property
    def data_dir(self) -> Path:
        """
        Get directory in which to store the parameters and events.
        """
        return self._data_dir

    @data_dir.setter
    def data_dir(self, data_dir: Union[str, Path]) -> None:
        """
        Set directory in which to store the parameters and events.
        Will be created if not existent.
        """
        data_dir = Path(data_dir)
        data_dir.mkdir(exist_ok=True, parents=True)
        self._data_dir = data_dir

    def __init__(
        self,
        *,
        data_dir: Union[str, Path],
        base_params: Optional[dict[str, dict[str, Any]]] = None,
        zip_params: Optional[dict[str, dict[str, Sequence[Any]]]] = None,
        product_params: Optional[dict[str, dict[str, Sequence[Any]]]] = None,
        cython: bool = True,
        debug: bool = False,
        max_workers: Optional[int] = None,
        process_chunksize: int = 1,
        jsonl_chunksize: int = 1000,
        event_path_suffix: str = ".jsonl",
        param_path_suffix: str = "_params.json",
        validate: bool = True,
    ) -> None:
        """

        Parameters
        ----------
        data_dir
            Directory in which to store the parameters and events.
        base_params
            Dictionary setting parameters that are kept constant throughout the simulation set, optional.
        zip_params
            Dictionary setting parameters that are varied together throughout the simulation set, optional.
            The values for each inner dict should be lists that all match in lengths.
        product_params
            Dictionary setting parameters of which the cartesian product (i.e. all possible
            combinations of the supplied parameters) is created and varied throughout
            the simulation set, optional.
        cython
            Use cython.
        debug
            Print debug info.
        max_workers
            Maximum number of multiprocessing workers. Defaults to number of processors
            on the machine if `None` or not given.
        process_chunksize
            Number of simulations to submit to each multiprocessing worker at a time.
        jsonl_chunksize
            Maximum number of events to keep in memory before saving to disk
        param_path_suffix
            Parameters will be stored under "data_dir/<simulation_id><suffix>"
        event_path_suffix
            Simulation events will be stored under "data_dir/<simulation_id><event_path_suffix>"
        validate
            Check validity of the supplied dictionary (unknown outer and inner keys, equal length for ``zip_params``)
        """

        self.debug = debug
        self.max_workers = max_workers
        self.process_chunksize = process_chunksize
        self.jsonl_chunksize = jsonl_chunksize
        self.data_dir = Path(data_dir)

        self._event_path_suffix = event_path_suffix
        self._param_path_suffix = param_path_suffix

        if cython:
            space_obj = CyEuclidean2D()
            dispatcher = CyBruteForceTotalTravelTimeMinimizingDispatcher
            transportation_request_cls = CyTransportationRequest
            vehicle_state_cls = CyVehicleState
        else:
            space_obj = Euclidean2D()
            dispatcher = BruteForceTotalTravelTimeMinimizingDispatcher
            transportation_request_cls = TransportationRequest
            vehicle_state_cls = VehicleState

        self.default_base_params = dict(
            general=dict(
                n_reqs=100,
                t_cutoff=None,
                space=space_obj,
                n_vehicles=10,
                initial_location=(0, 0),
                initial_locations=None,
                seat_capacity=8,
                transportation_request_cls=transportation_request_cls,
                vehicle_state_cls=vehicle_state_cls,
                fleet_state_cls=SlowSimpleFleetState,
            ),
            dispatcher=dict(dispatcher_cls=dispatcher),
            request_generator=dict(
                request_generator_cls=RandomRequestGenerator,
                rate=1,
            ),
        )

        base_params = base_params if base_params is not None else {}
        zip_params = zip_params if zip_params is not None else {}
        product_params = product_params if product_params is not None else {}

        if validate:
            # assert no unknown outer keys
            assert not (set(base_params) | set(zip_params) | set(product_params)) - set(
                self.default_base_params
            ), "invalid outer key"

            # assert no unknown inner keys
            for outer_key in set(self.default_base_params) - {
                "request_generator",
                "dispatcher",
            }:
                assert not (
                    set(base_params.get(outer_key, {}))
                    | set(zip_params.get(outer_key, {}))
                    | set(product_params.get(outer_key, {}))
                ) - set(
                    self.default_base_params[outer_key]
                ), f"invalid inner key for {outer_key=}"

            # assert equal length of zipped parameters
            assert self._zip_params_equal_length(
                zip_params
            ), "zipped parameters must be of equal length"

        self._base_params = self._two_level_dict_update(
            self.default_base_params, base_params
        )
        self._zip_params = zip_params
        self._product_params = product_params

        self._simulation_ids = None

        self._system_quantities_path = None

    @property
    def simulation_ids(self) -> list[str]:
        """
        Get simulation IDs.
        """
        # protect simulation ids
        return self._simulation_ids if self._simulation_ids is not None else []

    @property
    def param_paths(self) -> list[Path]:
        """
        Get list of JSON parameter files.
        """
        return [
            self.data_dir / f"{simulation_id}{self._param_path_suffix}"
            for simulation_id in self.simulation_ids
        ]

    @property
    def event_paths(self) -> list[Path]:
        """
        Get list of resulting output event JSON Lines file paths.
        """
        return [
            self.data_dir / f"{simulation_id}{self._event_path_suffix}"
            for simulation_id in self.simulation_ids
        ]

    @staticmethod
    def _make_joined_key_pairs_values(
        *, params: dict[str, dict[str, Sequence[Any]]], join_fn: Callable
    ) -> tuple[Iterable[tuple[str, str]], Iterable[Iterable[Any]]]:
        """

        Parameters
        ----------
        params
            Parameter dictionary containing sequences as inner values.
        join_fn
            e.g. `zip` or `itertools.product`

        Returns
        -------
        joined_key_pairs, joined_values_iter
        """
        if params:
            joined_values_iter = join_fn(
                *(
                    params[outer_key][inner_key]
                    for outer_key in params.keys()
                    for inner_key in params[outer_key].keys()
                )
            )
            joined_key_pairs = [
                (outer_key, inner_key)
                for outer_key in params.keys()
                for inner_key in params[outer_key].keys()
            ]
        else:
            joined_values_iter = joined_key_pairs = [tuple()]

        return joined_key_pairs, joined_values_iter

    def __iter__(self):
        zipped_key_pairs, zipped_values_iter = self._make_joined_key_pairs_values(
            params=self._zip_params, join_fn=zip
        )

        (
            multiplied_key_pairs,
            multiplied_values_iter,
        ) = self._make_joined_key_pairs_values(
            params=self._product_params, join_fn=it.product
        )

        def param_combinations() -> Iterator[dict[str, dict[str, Any]]]:
            """
            Generator yielding complete parameter sets which can be
            supplied to `perform_single_simulation`.
            """
            for zipped_params, multiplied_params in it.product(
                zipped_values_iter, multiplied_values_iter
            ):
                d = defaultdict(dict)

                for (outer_key, inner_key), value in zip(
                    zipped_key_pairs, zipped_params
                ):
                    d[outer_key][inner_key] = value

                for (outer_key, inner_key), value in zip(
                    multiplied_key_pairs, multiplied_params
                ):
                    d[outer_key][inner_key] = value

                yield self._two_level_dict_update(self._base_params, d)

        self._param_combinations = param_combinations()
        return self

    def __next__(self):
        return next(self._param_combinations)

    def run(self, dry_run=False):
        """
        Run the simulations configured through `base_params`, `zip_params` and `product_params` using
        multiprocessing. The parameters and resulting output events are written to disk
        in JSON/JSON Lines format. For more detail see :ref:`Executing Simulations`.

        Access simulations results
            - by id: `SimulationSet.simulation_ids`
            - by parameter file `SimulationSet.param_paths`
            - by event file `SimulationSet.event_paths`

        Parameters
        ----------
        dry_run
            If True, do not actually simulate.
        """

        self._simulation_ids = simulate_parameter_combinations(
            param_combinations=iter(self),
            data_dir=self.data_dir,
            debug=self.debug,
            max_workers=self.max_workers,
            process_chunksize=self.process_chunksize,
            jsonl_chunksize=self.jsonl_chunksize,
            event_path_suffix=self._event_path_suffix,
            param_path_suffix=self._param_path_suffix,
            dry_run=dry_run,
        )

    def __len__(self) -> int:
        """
        Number of simulations performed when calling `SimulationSet.run`.
        """
        len_ = 1
        if self._zip_params:
            len_ *= len(next(iter(next(iter(self._zip_params.values())).values())))
        if self._product_params:
            len_ *= ft.reduce(
                op.mul,
                (
                    len(inner_value)
                    for inner_dict in self._product_params.values()
                    for inner_value in inner_dict.values()
                ),
            )
        if not (self._zip_params or self._product_params):
            len_ = 0

        return len_

    def run_analytics(
        self,
        only_stops_and_requests: bool = False,
        update_existing: Union[bool, list[str]] = False,
        check_for_changes: bool = True,
        stops_path_suffix: str = "_stops.pq",
        requests_path_suffix: str = "_requests.pq",
        vehicle_quantities_path_suffix: str = "_vehicle_quantities.pq",
        system_quantities_filename: str = "system_quantities.pq",
    ) -> None:
        """
        Compute analytics from simulation events and store them to disk
        in parquet format.

        Parameters
        ----------
        only_stops_and_requests
            Only compute stops and requests, not vehicle and system quantities.
        update_existing
            Recompute existing outputs. If a list is given, only recompute
            the list entries. Valid list items are 'system_quantities',
            'vehicle_quantities', 'stops', and 'requests'.
        check_for_changes
            If True, only update system quantities if simulation ids have changed.
            If False, do update system quantities in any case.
        stops_path_suffix
            Appending this suffix to the simulation ID yields the path to the parquet
            stops file.
        requests_path_suffix
            Appending this suffix to the simulation ID yields the path to the parquet
            requests file.
        vehicle_quantities_path_suffix
            Appending this suffix to the simulation ID yields the path to the parquet
            vehicle quantities file.
        system_quantities_filename
            Filename of the parquet file to store the system quantities in.
        """
        self._system_quantities_path = self.data_dir / system_quantities_filename

        if not self.simulation_ids:
            warnings.warn(
                "no simulations have been run (simulation_ids empty)", UserWarning
            )
        else:

            # In any case, stops and requests have to be computed if they don't exist
            tasks_if_not_existent = {"stops", "requests"}

            if not only_stops_and_requests:
                # Additionally, we are computing vehicle and system quantities, now,
                # if they don't exist
                tasks_if_not_existent |= {"vehicle_quantities", "system_quantities"}

            if isinstance(update_existing, Iterable):
                # If we have been handed a list of tasks to update, we only update these,
                # not recomputing tasks that should not have be computed in the first place
                tasks_if_existent = set(update_existing) & tasks_if_not_existent
            elif update_existing == True:
                tasks_if_existent = tasks_if_not_existent
            elif update_existing == False:
                tasks_if_existent = set()
            else:
                raise ValueError(f"Got invalid value for {update_existing=}")

            if self._system_quantities_path.exists():
                tasks_if_not_existent -= {"system_quantities"}
                if check_for_changes:
                    # Currently, we only check for changes in the sense that new
                    # simulations with new ids have been performed and are thus missing from
                    # the system quantities output. For vehicle quantities, stops, and requests,
                    # check_for_changes does not apply, as we compute these in any case, should
                    # they be missing.
                    sqdf = pd.read_parquet(self._system_quantities_path)
                    if set(sqdf.index) == set(self.simulation_ids):
                        tasks_if_existent -= {"system_quantities"}
                    del sqdf

            with loky.get_reusable_executor(max_workers=self.max_workers) as executor:
                sim_ids, system_quantities = zip(
                    *list(
                        executor.map(
                            ft.partial(
                                perform_single_analysis,
                                data_dir=self.data_dir,
                                tasks_if_not_existent=tasks_if_not_existent,
                                tasks_if_existent=tasks_if_existent,
                                param_path_suffix=self._param_path_suffix,
                                event_path_suffix=self._event_path_suffix,
                                stops_path_suffix=stops_path_suffix,
                                requests_path_suffix=requests_path_suffix,
                                vehicle_quantities_path_suffix=vehicle_quantities_path_suffix,
                            ),
                            self.simulation_ids,
                            chunksize=self.process_chunksize,
                        )
                    )
                )

            if list(sim_ids) != self.simulation_ids:
                warnings.warn(
                    "Simulation IDs and IDs analytics were computed for do not match. Something's not right.",
                    UserWarning,
                )

            if "system_quantities" in tasks_if_not_existent | tasks_if_existent:
                system_quantities_df = pd.DataFrame(system_quantities, index=sim_ids)
                system_quantities_df.rename_axis("simulation_id", inplace=True)
                system_quantities_df.to_parquet(self._system_quantities_path)

    @property
    def param_path_suffix(self) -> str:
        """
        Get the parameter file suffix.
        """
        return self._param_path_suffix

    @property
    def event_path_suffix(self) -> str:
        """
        Get the event file suffix.
        """
        return self._event_path_suffix

    @property
    def system_quantities_path(self) -> Path:
        """
        Get path to the parquet file containing the system quantities.

        Returns
        -------
        system_quantities_path
        """
        if self._system_quantities_path is not None:
            return self._system_quantities_path
        else:
            raise AttributeError("No system quantities path set.")

    def get_system_quantities(
        self, extra_params: Optional[Mapping] = None
    ) -> pd.DataFrame:
        """
        Return the system quantities, if computed already using `run_analytics`.

        Optionally, join the system quantities dataframe with additional arbitrary
        parameters used in the simulation.

        Parameters
        ----------
        extra_params:
            Dictionary specifying the desired parameters. The keys are the resulting column
            names in the returned dataframe, the values are the (nested) keys in the
            `SimulationSet` params dictionary, joined by ``.``.

            Example:

            .. code-block:: python

                extra_params = {"n": "general.n_reqs"}

        Returns
        -------
        system_quantities
            DataFrame containing the system quantities and optional extra parameters

        """

        try:
            sqdf = pd.read_parquet(self.system_quantities_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"System properties file {self.system_quantities_path} not found."
            )

        if extra_params:
            for sim_id in sqdf.index:
                params = get_params(
                    self.data_dir, sim_id, param_path_suffix=self.param_path_suffix
                )
                for param_col, param_key in extra_params.items():
                    sqdf.loc[sim_id, param_col] = ft.reduce(
                        op.getitem, param_key.split("."), params
                    )

        return sqdf

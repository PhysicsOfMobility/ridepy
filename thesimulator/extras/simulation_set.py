import logging
import sys
import os
import hashlib

import concurrent.futures

import operator as op
import functools as ft
import itertools as it

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
)
from pathlib import Path

from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.spaces import Euclidean2D
from thesimulator.util.spaces_cython import Euclidean2D as CyEuclidean2D
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.data_structures import (
    TransportationRequest,
)
from thesimulator.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
)
from thesimulator.vehicle_state import VehicleState
from thesimulator.vehicle_state_cython import VehicleState as CyVehicleState
from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.extras.io import (
    create_params_json,
    save_events_json,
)

logger = logging.getLogger(__name__)


def perform_single_simulation(
    params: dict[str, dict[str, Any]],
    *,
    data_dir: Path,
    jsonl_chunksize: int = 1000,
    debug: bool = False,
    param_path_suffix: str = "_params.json",
    result_path_suffix: str = ".jsonl",
) -> str:
    """
    Execute a single simulation run based on a parameter dictionary
    and save parameters and result events to disk.

    Parameters
    ----------
    params
        Parameter dictionary to base the simulation on. Must contain the following keys:

        - ``general``
            - ``n_reqs``
            - ``n_vehicles``
            - ``seat_capacity``
            - ``initial_location``
            - ``space``
            - ``dispatcher``
            - ``TransportationRequestCls``
            - ``VehicleStateCls``
            - ``FleetStateCls``
        - ``request_generator``
            - ``RequestGeneratorCls``
    data_dir
        Existing directory in which to store parameters and results.
    jsonl_chunksize
        Number of simulation events to keep in memory before writing them to disk at once.
    debug
        Print debug info to stdout.
    param_path_suffix
        Parameters will be stored under "data_dir/<simulation_id><param_path_suffix>"
    result_path_suffix
        Simulation results will be stored under "data_dir/<simulation_id><result_path_suffix>"

    Returns
    -------

    """
    # we need a pseudorandom id that does not change if this function is called with the same params
    # the following does not guarantee a lack of collisions, and will fail if non-ascii characters are involved.

    params_json = create_params_json(params=params)
    sim_id = hashlib.sha224(params_json.encode("ascii", errors="strict")).hexdigest()
    result_path = data_dir / f"{sim_id}{result_path_suffix}"
    param_path = data_dir / f"{sim_id}{param_path_suffix}"

    if param_path.exists():
        # assume that a previous simulation run already exists. this works because we write
        # to param_path *after* a successful simulation run.
        logger.info(
            f"Pre-existing param json exists for {params=} at {param_path=}, skipping simulation"
        )
        return sim_id
    else:
        logger.info(
            f"No pre-existing param json exists for {params=} at {param_path=}, running simulation"
        )
        if result_path.exists():
            logger.info(
                f"Potentially incomplete simulation data exists at {result_path=}, this will be overwritten"
            )
            result_path.unlink()

    space = params["general"]["space"]
    RequestGeneratorCls = params["request_generator"].pop("RequestGeneratorCls")
    rg = RequestGeneratorCls(
        space=space,
        request_class=params["general"]["TransportationRequestCls"],
        **params["request_generator"],
    )

    fs = params["general"]["FleetStateCls"](
        initial_locations={
            vehicle_id: params["general"]["initial_location"]
            for vehicle_id in range(params["general"]["n_vehicles"])
        },
        space=space,
        dispatcher=params["general"]["dispatcher"],
        seat_capacities=params["general"]["seat_capacity"],
        vehicle_state_class=params["general"]["VehicleStateCls"],
    )

    # NOTE: this string is matched for testing
    if debug:
        print(f"Simulating run on process {os.getpid()} @ \n{params!r}\n")

    simulation = fs.simulate(it.islice(rg, params["general"]["n_reqs"]))

    while chunk := list(it.islice(simulation, jsonl_chunksize)):
        save_events_json(jsonl_path=result_path, events=chunk)

    with open(str(param_path), "w") as f:
        f.write(params_json)
    return sim_id


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

            >>> SimulationSet._two_level_dict_update(
            ...     {"a": {"b": 5, 6: 8}}, {"a": {6: "fooo", 8: "baaar"}, "baz": {"6": 6}}
            ... )
            {'a': {'b': 5, 6: 'fooo', 8: 'baaar'}, 'baz': {'6': 6}}


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
        for outer_key in set(base_dict) | set(update_dict):
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
        if zip_params and next(iter(next(iter(zip_params.values())).values())):
            return ft.reduce(
                op.__eq__,
                (
                    len(inner_value)
                    for inner_dict in zip_params.values()
                    for inner_value in inner_dict.values()
                ),
            )
        else:
            return True

    @property
    def data_dir(self) -> Path:
        """
        Get directory in which to store the parameters and results.
        """
        return self._data_dir

    @data_dir.setter
    def data_dir(self, data_dir: Union[str, Path]) -> None:
        """
        Set directory in which to store the parameters and results.
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
        mpi: bool = False,
        debug: bool = False,
        max_workers: Optional[int] = None,
        process_chunksize: int = 1,
        jsonl_chunksize: int = 1000,
        result_path_suffix: str = ".jsonl",
        param_path_suffix: str = "_params.json",
        validate: bool = True,
    ) -> None:
        """

        Parameters
        ----------
        data_dir
            Directory in which to store the parameters and results.
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
        mpi
            Use MPIFuturesFleetState.
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
            Parameters will be stored under "data_dir/<simulation_id><param_path_suffix>"
        result_path_suffix
            Simulation results will be stored under "data_dir/<simulation_id><result_path_suffix>"
        validate
            Check validity of the supplied dictionary (unknown outer and inner keys, equal length for ``zip_params``)
        """

        self.debug = debug
        self.max_workers = max_workers
        self.process_chunksize = process_chunksize
        self.jsonl_chunksize = jsonl_chunksize
        self.data_dir = data_dir

        self._result_path_suffix = result_path_suffix
        self._param_path_suffix = param_path_suffix

        if cython:
            SpaceObj = CyEuclidean2D()
            dispatcher = cy_brute_force_total_traveltime_minimizing_dispatcher
            TransportationRequestCls = CyTransportationRequest
            VehicleStateCls = CyVehicleState
        else:
            SpaceObj = Euclidean2D()
            dispatcher = brute_force_total_traveltime_minimizing_dispatcher
            TransportationRequestCls = TransportationRequest
            VehicleStateCls = VehicleState

        if mpi:
            FleetStateCls = MPIFuturesFleetState
        else:
            FleetStateCls = SlowSimpleFleetState

        RequestGeneratorCls = RandomRequestGenerator

        self.default_base_params = dict(
            general=dict(
                n_reqs=100,
                space=SpaceObj,
                n_vehicles=10,
                initial_location=(0, 0),
                seat_capacity=8,
                dispatcher=dispatcher,
                TransportationRequestCls=TransportationRequestCls,
                VehicleStateCls=VehicleStateCls,
                FleetStateCls=FleetStateCls,
            ),
            request_generator=dict(
                RequestGeneratorCls=RequestGeneratorCls,
                rate=10,
                max_pickup_delay=3,
                max_delivery_delay_rel=1.9,
                seed=42,
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
            for outer_key in self.default_base_params:
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

        self._result_ids = None

    @property
    def result_ids(self) -> list[str]:
        """
        Get simulation result IDs.
        """
        # protect result ids
        return self._result_ids if self._result_ids is not None else []

    @property
    def param_paths(self) -> list[Path]:
        """
        Get list of JSON parameter files.
        """
        return [
            self.data_dir / f"{result_id}{self._param_path_suffix}"
            for result_id in self.result_ids
        ]

    @property
    def result_paths(self) -> list[Path]:
        """
        Get list of resulting output event JSON Lines file paths.
        """
        return [
            self.data_dir / f"{result_id}{self._result_path_suffix}"
            for result_id in self.result_ids
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

    def run(self):
        """
        Run the simulations configured through `base_params`, `zip_params` and `product_params` using
        multiprocessing. The parameters and resulting output events are written to disk
        in JSON/JSON Lines format. For more detail see :ref:`Executing Simulations`.

        Access simulations results
            - by id: `SimulationSet.result_ids`
            - by parameter file `SimulationSet.param_paths`
            - by result file `SimulationSet.result_paths`
        """

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            self._result_ids = list(
                executor.map(
                    ft.partial(
                        perform_single_simulation,
                        debug=self.debug,
                        jsonl_chunksize=self.jsonl_chunksize,
                        data_dir=self.data_dir,
                        param_path_suffix=self._param_path_suffix,
                        result_path_suffix=self._result_path_suffix,
                    ),
                    iter(self),
                    chunksize=self.process_chunksize,
                )
            )

    def __len__(self) -> int:
        """
        Number of simulations performed when calling `SimulationSet.run`.
        """
        if self._zip_params:
            zip_part = len(next(iter(next(iter(self._zip_params.values())).values())))
        else:
            zip_part = 1
        product_part = ft.reduce(
            op.mul,
            (
                len(inner_value)
                for inner_dict in self._product_params.values()
                for inner_value in inner_dict.values()
            ),
        )
        return zip_part * product_part


def simulate_parameter_combinations(
    *,
    param_combinations: Iterator[dict[str, dict[str, Sequence[Any]]]],
    data_dir: Union[str, Path],
    debug: bool = False,
    max_workers: Optional[int] = None,
    process_chunksize: int = 1,
    jsonl_chunksize: int = 1000,
    result_path_suffix: str = ".jsonl",
    param_path_suffix: str = "_params.json",
):
    """
    Run simulations for different parameter combinations using multiprocessing.

    Parameters
    ----------
    param_combinations
        An iterable of parameter configurations. For more detail see :ref:`Executing Simulations`
    data_dir
        Directory in which to store the parameters and results.
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
        Parameters will be stored under "data_dir/<simulation_id><param_path_suffix>"
    result_path_suffix
        Simulation results will be stored under "data_dir/<simulation_id><result_path_suffix>"

    Returns
    -------
        List of simulation IDs. See the docstring of `.SimulationSet` for more detail.
    """
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        sim_ids = list(
            executor.map(
                ft.partial(
                    perform_single_simulation,
                    debug=debug,
                    jsonl_chunksize=jsonl_chunksize,
                    data_dir=data_dir,
                    param_path_suffix=param_path_suffix,
                    result_path_suffix=result_path_suffix,
                ),
                param_combinations,
                chunksize=process_chunksize,
            )
        )
    return sim_ids

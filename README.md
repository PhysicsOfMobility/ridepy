[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# theSimulator
Simulates a dispatching algorithm serving exogeneous transportation requests with a fleet of vehicles. Does not simulate the universe, unlike MATSIM.

## Instructions
### Prerequisites
* Python 3.8
* git

You should probably use an environment. For example, using [conda](https://www.anaconda.com/):
```sh
conda create -n the_simulator python=3.8
conda activate the_simulator
```

### Installation
```sh
git clone git@github.com:PhysicsOfMobility/theSimulator.git
cd theSimulator
pip install poetry
poetry install
pre-commit install
pytest
```
## Contributing
Generally branch from `master`, implement stuff® and file a pull request back to
`master`. Feel free to do the latter at an early stage, prefixing the pull request with
"WIP:".
- `master` should always improve. Incomplete functionality is welcome.
- `production` should always be usable and, if possible, not break things.

## Principles
### Jargon
- **estimated arrival time**, also Cached Predicted Arrival Time CPAT
- **time window min**, also Earliest Allowed Service Time EAST
- **time window max**, also Latest Allowed Service Time LAST
- **stoplist**, a sequence of scheduled stops that a transporter must *service*, 
  i.e. perform the action defined in the respective stop's `Stop.action`
- dummy stop **current position element CPE** always must be the first entry of each stoplist,
  denoting the current location of the transporter.
- transporter, vehicle, bus, car

### General Things
- The dispatcher is responsible for keeping the state of the stoplists valid.
 This means e.g. recomputing the estimated arrival times and making sure that
  the order of the stops in the stoplist follows the order of the estimated 
  arrival times. It also includes managing the CPE.
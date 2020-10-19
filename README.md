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
- `master` should always improve. Uncomplete functionality is welcome.
- `production` should always be usable and, if possible, not break things.

import subprocess
import shutil
import jupytext

from pathlib import Path

from .simulate_script import simulate_on_r2


def test_simulate_script():
    simulate_on_r2(num_vehicles=10, rate=10, num_requests=1000, seat_capacities=4)


def test_notebooks(tmp_path):
    tmp_py_path = tmp_path / "notebook.py"
    tmp_ipy_path = tmp_path / "notebook.ipy"

    for fpath in Path("notebooks").glob("*.py"):
        print(fpath)

        # This stunt is necessary to deal with magic commands
        # Constraints:
        # - Magics must not be in the py light script files, because black will complain.
        #   Also jupytext doesn't do this on default. This can be changed by modifying the
        #   notebooks' metadata, but this is obviously not practical to do for every new notebook.
        # - Magics must be there for the test to work, as e.g. `%time result = my_expensive_computation()`
        #   will leave `result` undefined if the line is commented by jupytext
        # - ipython will understand magics, but only accept them in files ending with `.ipy`
        # - jupytext will not store anything to files ending with `.ipy`
        # - we only want to keep `.py` files in the notebooks directory (apart from `.ipynb` files, locally)
        # this leaves us with the this garbage.
        jupytext.write(
            jupytext.read(fpath, fmt="py"),
            tmp_py_path,
            fmt={"extension": "py", "comment_magics": False},
        )

        assert tmp_py_path.exists()
        shutil.copy(tmp_py_path, tmp_ipy_path)
        assert tmp_ipy_path.exists()

        # TODO: substitute this with something along these lines
        # IPython.get_ipython().safe_execfile(fname, shell_futures=False, raise_exceptions=True)
        res = subprocess.run(["ipython", str(tmp_ipy_path)], capture_output=True)

        stdout = res.stdout.decode()
        stderr = res.stderr.decode()
        assert not "WARNING" in stderr
        assert not "Error" in stdout

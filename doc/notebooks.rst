Tutorial
========

To get started with RidePy, following this tutorial is a good option. The tutorials are based on jupyter notebooks. Because of this, you can either view them here as part of the documentation or run them on your machine to get hands-on experience.

.. toctree::
    :maxdepth: 1
    :caption: Available tutorials

    1 | Basics <notebooks/introduction>
    2 | Cython <notebooks/introduction_cython>
    3 | Graphs <notebooks/introduction_cython_graph>
    4 | Parallelization <notebooks/introduction_simulation_set>

.. _running notebooks:

Executing the tutorial notebooks yourself
-----------------------------------------

To run these notebooks locally, you'll need to install RidePy first. Then, either clone the git repository:

.. code:: sh

    git clone --recurse-submodules https://github.com/PhysicsOfMobility/ridepy.git
    cd ridepy

or download the repository as a ZIP archive `here <https://github.com/PhysicsOfMobility/ridepy/archive/refs/heads/master.zip>`_.

To run the notebooks, you will either need `JupyterLab <https://jupyter.org/install#jupyterlab>`_ (recommended) or `Jupyter Notebook <https://jupyter.org/install#jupyter-notebook>`_.

In addition, Jupytext is required to use the MyST-Markdown format in which the notebooks are kept in the repository for easier version control:

.. code:: sh

    pip install -U jupytext

With Jupytext installed, run ``jupyter lab`` or ``jupyter notebook``. Open any of the introductory notebooks in ``doc/notebooks``, either just by clicking on it (in Jupyter Notebook) or by right-clicking and choosing *Open With > Notebook* (in JupyterLab). Now you can run the notebook step-by-step and play around :)

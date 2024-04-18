Releasing a new version of RidePy
===============================

Note that this document is intended for project maintainers.

Prerequisites
-------------

- The ``master`` branch must be checked out.
- There must be no uncommitted changes.
- The version in ``pyproject.toml`` must match the latest git tag (this should be the case by default).
- The new version must be greater than the current one (only important if the new version is chosen explicitly).
- The ``gh`` (github CLI client) command must be available and authenticated.
- Git push access to the upstream RidePy repository including the protected ``master`` branch must be available using the SSH agent credentials.
- A private PGP key must be available to sign the commit.

Steps
-----

Automatic versioning works like this:

.. code:: bash

   ridepy dev publish-release <version to bump>

Here, ``version to bump`` is the semantiv versions part to bump: ``major``, ``minor``, or ``patch``.

Alternatively, the new version may be specified manually:

.. code:: bash

   ridepy dev publish-release --version <new version>

This will update the version in the ``pyproject.toml`` file, create a release commit and a corresponding git tag, push it to the upstream repository, and create a corresponding release on GitHub.

Finally, the command also sports a ``--dry-run`` flag for testing.

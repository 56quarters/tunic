Tunic
=====

.. image:: https://travis-ci.org/tshlabs/tunic.png?branch=master
    :target: https://travis-ci.org/tshlabs/tunic

.. image:: https://img.shields.io/pypi/v/tunic.svg
    :target: https://pypi.python.org/pypi/tunic


A Python library for deploying code on remote servers.

Tunic is designed so that you can make use of as much or as little of
its functionality as you'd like, the choice is yours.

It only requires the Fabric library as a dependency and can be installed
from the Python Package Index (PyPI) using the pip tool like so.

.. code-block:: bash

    $ pip install tunic

You could then make use of it in your deploy process like so.

.. code-block:: python

    from fabric.api import task
    from tunic.api import get_release_id, ReleaseManager, VirtualEnvInstallation

    APP_BASE = '/srv/www/myapp'

    @task
    def deploy():
        stop_my_app()
        release = get_release_id()

        installer = VirtualEnvInstaller(APP_BASE, ['myapp'])
        release_manager = ReleaseManager(APP_BASE)

        installer.install(release)
        release_manager.set_current_release(release)

        start_my_app()

The above snippet is just the start, take a look around the code base
for more methods that can save you work in your deploy process.

Documentation
-------------

The latest documentation is available at http://tunic.readthedocs.io/en/latest/

Source
------

The source is available at https://github.com/tshlabs/tunic

Download
--------

Python packages are available at https://pypi.python.org/pypi/tunic

Changes
-------

The change log is available at http://tunic.readthedocs.io/en/latest/changes.html

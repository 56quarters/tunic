.. Tunic documentation master file, created by
   sphinx-quickstart on Mon Sep 22 21:26:34 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. NOTE: Copied from README.rst, keep in sync.
   Copied because github won't execute include directives so
   having the README.rst just include some common text file
   isn't an option.

Tunic
=====

Tunic is a library built on Fabric for performing common tasks related
to deploying a code base on multiple remote servers.

It's designed so that you can make use of as much or as little of
its functionality as you'd like, the choice is yours.

It only requires the Fabric library as a dependency and can be installed
from the Python Package Index (PyPI) using the pip tool like so. ::

    pip install tunic

You could then make use of it in your deploy process like so. ::

    from fabric.api import task
    from tunic.api import get_release_id, ReleaseManager

    @task
    def deploy():
        stop_my_app()
        release = get_release_id()
        install_my_app(release)
        rm = ReleaseManager('/srv/www/mysite')
        rm.set_current_release(release)
        start_my_app()

The above snippet is just the start, take a look around the code base
for more methods that can save you work in your deploy process.

Contents
========

.. toctree::
    :maxdepth: 2

    design
    api
    examples
    contributing
    changes

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


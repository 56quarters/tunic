Usage
=====

Tunic tries to reduce the amount of code you need to write for your deploy
process. The major components of Tunic are designed so that they can be used
together -- or not. If you find a component doesn't fit well with your deploy
process, don't use it!

This guide will go over each of the distinct components of the Tunic library
and how to use them individually. Then we'll look at how to use them all
together as part of the same deploy process.

get_releases_path and get_current_path
--------------------------------------

These are the most basic parts of the Tunic library. Given a path to the base
directory of your project, they'll give you paths to components of the directory
structure that the rest of the Tunic library expects. They are code to enforce
assumptions made by the library.

An example of using the :func:`tunic.api.get_releases_path` method to find all
releases of a particular project.

.. code-block:: python

    from fabric.api import run
    from tunic.api import get_releases_path

    APP_BASE = '/srv/www/myapp'

    def get_myapp_releases():
        """Get all releases of the MyApp project as a list."""
        release_path = get_releases_path(APP_BASE)
        releases = run('ls -1r ' + releases_path)
        return releases.split()

An example of using the :func:`tunic.api.get_current_path` method to find the
deployment that is being actively served.

.. code-block:: python

    from fabric.api import run
    from tunic.api import get_current_path

    APP_BASE = '/srv/www/myapp'

    def get_myapp_current():
        """Get the active deployment of MyApp."""
        current_path = get_current_path(APP_BASE)
        current = run('readlink ' + current_path)
        return current

get_release_id
--------------

The :func:`tunic.api.get_release_id` method is responsible for generating a
unique name for each deployment of a project. It generates a timestamp based
name, with an optional version component. The timestamp component is built with
the largest period of time first (the current year), followed by each smaller
component down to the second (similar to `ISO 8601`_ dates).

The purpose of generating a name for a deployment in this manor is to allow us
to keep track of when each deployment was made. Thus we are able to easily figure
out which deployments are the oldest, which particular deployment came before the
'current' one, etc.

An example of using the :func:`tunic.api.get_release_id` method to set up a new
deployment.

.. code-block:: python

    import os.path
    from fabric.api import run
    from tunic.api import get_release_id

    APP_BASE = '/srv/www/myapp'

    def create_new_release(version):
        """Create a new release virtualenv and return the path."""
        releases = os.path.join(APP_BASE, 'releases')    # '/srv/www/myapp/releases'
        release_id = get_release_id(version)             # '20140928223929-1.4.1'
        new_release = os.path.join(releases, release_id) # '/srv/www/myapp/releases/20140928223929-1.4.1'
        run('virtualenv ' + new_release)
        return new_release


.. _`ISO 8601`: http://en.wikipedia.org/wiki/ISO_8601

ReleaseManager
--------------


ProjectSetup
------------


VirtualEnvInstallation
----------------------


Putting it all together
-----------------------

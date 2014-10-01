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

Below is an example of using the :func:`tunic.api.get_releases_path` method to find
all releases of a particular project.

.. code-block:: python

    from fabric.api import run
    from tunic.api import get_releases_path

    APP_BASE = '/srv/www/myapp'

    def get_myapp_releases():
        """Get all releases of the MyApp project as a list."""
        release_path = get_releases_path(APP_BASE)
        releases = run('ls -1r ' + releases_path)
        return releases.split()

Below is an example of using the :func:`tunic.api.get_current_path` method to
find the deployment that is being actively served.

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

Below is an example of using the :func:`tunic.api.get_release_id` method to set up
a new deployment.

.. _`ISO 8601`: http://en.wikipedia.org/wiki/ISO_8601

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


ReleaseManager
--------------

The :class:`tunic.api.ReleaseManager` class is responsible for inspecting and
manipulating previous deployments and the current deployment on a remote server.

In order manipulate deployments like this, the ReleaseManager requires that they
are organized as described in :doc:`design`.

Below is an example of getting all available deployments (current and past) from
a server.

.. code-block:: python

    from tunic.api import ReleaseManager

    APP_BASE = '/srv/www/myapp'

    def get_all_releases():
        release_manager = ReleaseManager(APP_BASE)
        return release_manager.get_releases()


Below is an example of creating a "rollback" task in Fabric for switching to the
previous deployment of your project that uses the  :meth:`tunic.api.ReleaseManager.get_previous_release`
and :meth:`tunic.api.ReleaseManager.set_current_release` methods.

.. code-block:: python

    from fabric.api import task, warn
    from tunic.api import ReleaseManager

    APP_BASE = '/srv/www/myapp'

    @task
    def rollback():
        release_manager = ReleaseManager(APP_BASE)
        previous = release_manager.get_previous_release()

        if previous is None:
            warn("No previous release, can't rollback!")
            return

        release_manager.set_current_release(previous)

The ReleaseManager can also remove old deployments. To do this, you must
have named the deployments with a timestamp based prefix. If you've used
:func:`tunic.api.get_release_id` to name your deployments, this is handled
for you.

.. code-block:: python

    from fabric.api import task
    from tunic.api import ReleaseManager

    APP_BASE = '/srv/www/myapp'

    @task
    def cleanup(deployments_to_keep=5):
        release_manager = ReleaseManager(APP_BASE)
        release_manager.cleanup(keep=deployments_to_keep)

ProjectSetup
------------

The :class:`tunic.api.ProjectSetup` class is responsible for creating the
required directory structure for a project and ensuring that permissions
and ownership is consistent before and after a deploy.

The ProjectSetup class will create directories that are organized as described
in :doc:`design`.

The ProjectSetup class typically uses sudo for creation of the directory
structure and changing of ownership and permissions of the project deploys.
If the user doing the deploy will not have sudo permissions, the methods
can be passed the ``use_sudo=False`` keyword argument to instruct them not
to use sudo, but instead use the Fabric ``run`` command. When using the ``run``
command, the :meth:`tunic.api.ProjectSetup.set_permissions` method will not
attempt to change the owner of the project deploys, only the permissions.

As with most parts of the Tunic library, use of this class for project deploy
process is optional. For example, if you use a configuration management system
(such as Puppet, Chef, Ansible, etc.) to ensure the correct directories exist
and have correct permissions on any server you deploy to, using the ProjectSetup
class may not be needed.

An example of creating the required directory structure and ensuring permissions
before and after a deploy, assuming the user doing the deploy has sudo permissions.

.. code-block:: python

    from fabric.api import task
    from tunic.api import ProjectSetup
    from .myapp import install_project

    APP_BASE = '/srv/www/myapp'

    @task
    def deploy():
        setup = ProjectSetup(APP_BASE)
        setup.setup_directories()
        setup.set_permissions('root:www')

        install_project()

        setup.set_permissions('root:www')


VirtualEnvInstallation
----------------------

The :class:`tunic.api.VirtualEnvInstallation` class is used to install one
or multiple packages into a Python `virtual environment`_. The virtual
environment is typically a particular deployment of your project.

The ``VirtualEnvInstallation`` assumes that directories for a project are
setup as described in :doc:`design`.

Usage of this installer requires that the ``virtualenv`` tool is installed
on the remote server and is on the ``PATH`` of the user performing the deploy
or the location of the ``virtualenv`` tool is provided to the ``VirtualEnvInstallation``
class when instantiated.

Below is an example of using the ``VirtualEnvInstallation`` to install a
project and WSGI server from the default Python Package Index (PyPI).

.. code-block:: python

    from fabric.api import task
    from tunic.api import VirtualEnvInstallation

    APP_BASE = '/srv/www/myapp'

    @task
    def install():
        installation = VirtualEnvInstallation(APP_BASE, ['myapp', 'gunicorn'])
        installation.install('20141002111442-1.4.1')

The example above is simple, but not ideal. If you want a robust deploy
process you probably don't want to rely on PyPI being available and you
probably don't want to install whatever happens to be the latest version
of a dependency. An example that installs only packages from a directory
on the filesystem of the remote server is below. Presumably the packages
in this directory have been created by some part of your build process or
copied there by a different step in your deploy process.

.. code-block:: python

    from fabric.api import task
    from tunic.api import VirtualEnvInstallation

    APP_BASE = '/srv/www/myapp'

    LOCAL_PACKAGES = '/tmp/build/myapp'

    @task
    def install():
        installation = VirtualEnvInstallation(
            APP_BASE, ['myapp', 'gunicorn'], sources=[LOCAL_PACKAGES])
        installation.install('20141002111442-1.4.1')

Better still, you may want to run your own local build artifact repository.
In this case you'd simply include a URLs to index pages on the repository as
sources. An example is below.

.. code-block:: python

    from fabric.api import task
    from tunic.api import VirtualEnvInstallation

    APP_BASE = '/srv/www/myapp'

    MY_PACKAGES = 'https://artifacts.example.com/myapp/1.4.1/'

    THIRD_PARTY = 'https://artifacts.example.com/3rd-party/1.4.1/'

    @task
    def install():
        installation = VirtualEnvInstallation(
            APP_BASE, ['myapp', 'gunicorn'], sources=[MY_PACKAGES, THIRD_PARTY])
        installation.install('20141002111442-1.4.1')

.. _`virtual environment`: http://virtualenv.readthedocs.org/

Putting it all together
-----------------------

Alright, you've seen how each individual component can be used. How
does it all work together in a real deploy process? Take a look at the
example below!

.. code-block:: python

    from fabic.api import hide, task, warn
    from tunic.api import (
        get_current_path,
        get_releases_path,
        get_release_id,
        ProjectSetup,
        ReleaseManager,
        VirtualEnvInstallation)

    APP_BASE = '/srv/www/myapp'

    DEPLOY_OWNER = 'root:www'

    # URLs do download artifacts from. Notice that we don't
    # include version numbers in these URls. We'll use the
    # version specified as part of the deploy to build source
    # URLs below specific to our version.
    MY_PACKAGES = 'https://artifacts.example.com/myapp/'
    THIRD_PARTY = 'https://artifacts.example.com/3rd-party/'

    @task
    def deploy(version):
        # Ensure that the correct directory structure exists on
        # the remote server and attempt to set the permissions of
        # it do something reasonable.
        setup = ProjectSetup(APP_BASE)
        setup.setup_directories()
        setup.set_permissions(DEPLOY_OWNER)

        # Come up with a new release ID and build source URLs that
        # include the particular version of our project that we want
        # to deploy.
        release_id = get_release_id(version)
        versioned_package_sources = MY_PACKAGES + version
        versioned_third_party_sources = THIRD_PARTY + version

        # Install the 'myapp' and 'gunicorn' packages into a new
        # virtualenv on a remote server using our own custom internal
        # artifact sources, ignoring the default Python Package Index.
        installation = VirtualEnvInstallation(
            APP_BASE, ['myapp', 'gunicorn'],
            sources=[versioned_package_sources,
                versioned_third_party_sources])

        with hide('stdout'):
            # Installation output can be quite verbose, so we suppress
            # it here.
            installation.install(release_id)

        # Use the release manager to mark the just installed release as
        # the 'current' release and remove all but the N newest releases.
        release_manager = ReleaseManager(APP_BASE)
        release_manager.set_current_release(release_id)
        release_manager.cleanup()

        # Ensure that permissions and ownership of the deploys are
        # correct after the new deploy before exiting.
        setup.set_permissions(DEPLOY_OWNER)

    @task
    def rollback():
        release_manager = ReleaseManager(APP_BASE)
        previous = release_manager.get_previous_release()

        # If the previous version couldn't be determined for some reason,
        # we can rollback so we just given up now. This can happen when
        # there's only a single deployment, when the 'current' symlink
        # doesn't exist, when deploys aren't named correct, etc.
        if previous is None:
            warn("No previous release, can't rollback!")
            return

        # Atomically swap the 'current' symlink to another release.
        release_manager.set_current_release(previous)

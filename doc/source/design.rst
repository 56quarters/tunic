Design
======

This section will go over some assumptions made by the Tunic library,
the general design of the library, and some things to keep in mind when
using it.

Purpose
-------

Tunic is meant to supplement your existing Fabric based deploy process,
not to replace it or the Fabric library / tool. Tunic is **not** an abstraction
layer for Fabric. It's merely meant to let you avoid writing the same thing
over and over again.

Directory structure
-------------------

Tunic doesn't care about where on your server you deploy to. However, it
expects that deployments are organized in a particular way and that each
deployment of your project is named in a particular way. The following
are **required** for Tunic functionality to work correctly.

For this example, let's assume you're deploying your project to ``/srv/www/myapp``.

* This base directory for your project should be writable as the user or group
  that deploys are being performed by.

* The directory structure under ``/srv/www/myapp`` must organized as follows. ::

    /srv/www/myapp
        /releases
        /current

* The ``releases`` directory must be under your project base directory and be
  writeable by the user or group that deploys are being performed by.

* ``current`` must be a symlink to the active deployment in the ``releases``
  directory. This symlink will be created for you automatically if you use the
  :meth:`tunic.api.ReleaseManager.set_current_release` method as part of your
  deploy process.

Dependence on Fabric
--------------------

Since Tunic is built on Fabric, it inherits the following behavior.

* Output from commands run by methods in :mod:`tunic.api` ends up being displayed
  just like output from commands run by Fabric. This can be changed through the
  use of Fabric `context managers`_.

* Since Tunic requires Fabric and Fabric doesn't support Python 3 (yet), Tunic
  cannot be used under Python 3.

.. _context managers: http://docs.fabfile.org/en/latest/api/core/context_managers.html


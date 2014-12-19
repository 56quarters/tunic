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

    /
    +-- srv
        +-- www
            +-- myapp
                |-- releases
                |   +-- 20141105123145-0.2.0
                |   +-- 20141002231442-0.1.0
                +-- current

* The ``releases`` directory must be under your project base directory and be
  writeable by the user or group that deploys are being performed by.

* Each deploy under the ``releases`` directory must be named starting with a
  timestamp corresponding to when the deploy was done. The timestamp component
  should built with the largest period of time first (the current year), followed
  by each smaller component down to the second. The timezone used to generate this
  timestamp component doesn't matter as long as you always use the same one.

  The name for each deploy will be generated for you if you use the
  :func:`tunic.core.get_release_id` function. This is required to ensure that we
  can determine the time deploys were done relative to each other.

* ``current`` must be a symlink to the active deployment in the ``releases``
  directory. This symlink will be created for you automatically if you use the
  :meth:`tunic.core.ReleaseManager.set_current_release` method as part of your
  deploy process.

Dependence on Fabric
--------------------

Since Tunic is built on Fabric, it inherits the following behavior.

* Output from commands run by methods in :mod:`tunic.api` ends up being displayed
  just like output from commands run by Fabric. This can be changed through the
  use of Fabric `context managers`_.

* Since Tunic requires Fabric and Fabric doesn't support Python 3 (yet), Tunic
  won't work with Python 3 at this time.

* Since Tunic makes heavy use of Fabric and Fabric is not `thread safe`_, Tunic
  is also not thread safe.

.. _context managers: http://docs.fabfile.org/en/latest/api/core/context_managers.html

.. _thread safe: http://www.fabfile.org/faq.html#is-fabric-thread-safe


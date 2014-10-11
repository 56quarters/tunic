Change Log
==========

0.5.0 - 2014-10-11
------------------
* **Breaking change**: Change behavior of :class:`tunic.install.LocalArtifactTransfer`
  to yield the final destination path on the remote server (a combination of the
  remote path and right-most component of the local path). This new value will
  be the only path removed on the remote server when the context manager exits.
* **Breaking change**: Trailing slashes on ``local_path`` and ``remote_path``
  constructor arguments to :class:`tunic.install.LocalArtifactTransfer` are now removed
  before being used.
* Add :class:`tunic.install.StaticFileInstallation` class for installation of static
  files into a release on a remote server.

0.4.0 - 2014-10-02
------------------
* Allow override of the ``virtualenv`` script location on the remote
  server when using the :class:`tunic.install.VirtualEnvInstallation` class.
* Add :doc:`usage` section to the documentation that explains how to use
  each part of the library at a higher level than just the :doc:`api` section.
* Add :class:`tunic.install.LocalArtifactTransfer` class for transferring locally
  built artifacts to a remote server and cleaning them up after deployment
  has completed.

0.3.0 - 2014-09-28
------------------
* Test coverage improvements
* :class:`tunic.core.ReleaseManager` and :class:`tunic.core.ProjectSetup`
  now throw :class:`ValueError` for invalid ``base`` values in their
  ``__init__`` methods.
* Fix bug where we attempted to split command output by ``\n\r`` instead
  of ``\r\n``.
* Add :class:`tunic.install.VirtualEnvInstallation` class for performing remote
  virtualenv installations.

0.2.0 - 2014-09-26
------------------
* Add initial documentation for Tunic API
* Add design decision documentation for library
* Change behavior of :meth:`tunic.core.ProjectSetup.set_permissions` to not
  attempt to change the ownership of the code deploy unless it is using the
  ``sudo`` function

0.1.0 - 2014-09-22
------------------
* Initial release
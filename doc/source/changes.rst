Change Log
==========

0.3.0 - 2014-09-28
------------------
* Test coverage improvements
* :class:`tunic.api.ReleaseManager` and :class:`tunic.api.ProjectSetup`
  now throw :class:`ValueError` for invalid ``base`` values in their
  ``__init__`` methods.
* Fix bug where we attempted to split command output by ``\n\r`` instead
  of ``\r\n``.
* Add :class:`tunic.api.VirtualEnvInstallation` class for performing remote
  virtualenv installations.

0.2.0 - 2014-09-26
------------------
* Add initial documentation for Tunic API
* Add design decision documentation for library
* Change behavior of :meth:`tunic.api.ProjectSetup.set_permissions` to not
  attempt to change the ownership of the code deploy unless it is using the
  ``sudo`` function

0.1.0 - 2014-09-22
------------------
* Initial release
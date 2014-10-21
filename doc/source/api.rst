API
===

The public API of the Tunic library is maintained in the :mod:`tunic.api`
module. This is done for the purposes of clearly identifying which parts of
the library are public and which parts are internal.

Functionality in the :mod:`tunic.core` and :mod:`tunic.install` modules is
included in this module under a single, flat namespace. This allows a simple
and consistent way to interact with the library.

.. automodule:: tunic.core
    :special-members: __init__,__call__,__enter__,__exit__
    :members:
    :exclude-members: split_by_line, FabRunner, ProjectBaseMixin
    :undoc-members:

.. automodule:: tunic.install
    :special-members: __init__,__call__,__enter__,__exit__
    :members:
    :undoc-members:

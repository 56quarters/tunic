Tunic
=====

**WARNING** - This is pre-alpha software and subject to changes and/or bugs.

Tunic is a library built on Fabric for performing common tasks related
to deploying a code base on multiple remote servers.

It's designed so that you can make use of as much or as little of
its functionality as you'd like, the choice is yours.

It only requires the Fabric library as a dependency and can be installed
from the Python Package Index (PyPI) using the pip tool like so. ::

    pip install tunic

You could then make use of it in your deploy process like so. ::

    from tunic.api import ReleaseManager

    stop_my_app()
    rm = ReleaseManager('/srv/www/mysite')
    rm.set_current_release('20141002231442')
    start_my_app()

The above snippet is just the start, take a look around the code base
for more methods that can save you work in your deploy process.

The source is available at https://github.com/tshlabs/tunic

Enjoy!

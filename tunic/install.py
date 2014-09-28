# -*- coding: utf-8 -*-
#
# Tunic
#
# Copyright 2014 TSH Labs <projects@tshlabs.org>
#
# Available under the MIT license. See LICENSE for details.
#

"""
tunic.install
~~~~~~~~~~~~~

Installation on remote machines.
"""

import os.path

from .core import FabRunner, ProjectBaseMixin


def _is_iterable(val):
    """Ensure that a value is iterable and not some sort of string"""
    try:
        iter(val)
    except (ValueError, TypeError):
        return False
    else:
        return not isinstance(val, basestring)


class VirtualEnvInstallation(ProjectBaseMixin):
    """Install one or multiple packages into a remote virtual environment.

    If the remote virtual environment does not already exist, it will be
    created during the install process.

    The installation can use the standard package index (PyPI) to download
    dependencies, or it can use one or multiple alternative installation
    sources (such as a local PyPI instance, Artifactory, the local file system,
    etc.) and ignore the default index. These two modes are mutually exclusive.

    See :doc:`design` for more information about the expected directory
    structure for deployments.
    """

    def __init__(self, base, packages, sources=None, runner=None):
        """Set the project base directory, packages to install, and optionally
        alternative sources from which to download dependencies.

        :param str base: Absolute path to the root of the code deploy
        :param list packages: A collection of package names to install into
            a remote virtual environment.
        :param list sources: A collection of alternative sources from which
            to install dependencies. These sources should be strings that are
            either URLs or file paths. E.g. 'http://pypi.example.com/simple/'
            or '/tmp/build/mypackages'. Paths and URLs may be mixed in the same
            list of sources.
        :param FabRunner runner: Optional runner to use for executing
            remote commands to manage releases.
        :raises ValueError: If no packages are given, packages is not an iterable
            collection or some kind, or if sources is specified by not an iterable
            collection of some kind.
        """
        super(VirtualEnvInstallation, self).__init__(base)

        if not packages:
            raise ValueError(
                "You must specify at least one package to install")

        if not _is_iterable(packages):
            raise ValueError("Packages must be an iterable")

        if sources is not None and not _is_iterable(sources):
            raise ValueError("Sources must be an iterable")

        self._packages = list(packages)
        self._sources = list(sources) if sources is not None else []
        self._runner = runner if runner is not None else FabRunner()

    def _get_install_sources(self):
        """Construct arguments to use alternative package indexes if
        there were sources supplied, empty string if there were not.
        """
        if not self._sources:
            return ''
        parts = ['--no-index']
        for source in self._sources:
            parts.append("--find-links '{0}'".format(source))
        return ' '.join(parts)

    def install(self, release_id, upgrade=False):
        """Install target packages into a virtual environment.

        If the virtual environment for the given release ID does not
        exist on the remote system, it will be created. The virtual
        environment will be created according to the standard Tunic
        directory structure (see :doc:`design`).

        If ``update=True`` is passed, packages will be updated to the
        most recent version if they are already installed in the virtual
        environment.

        :param str release_id: Timestamp-based identifier for this
            deployment. If this ID corresponds to a virtual environment
            that already exists, packages will be installed into this
            environment.
        :param bool upgrade: Should packages be updated if they are
            already installed in the virtual environment.
        :return: The results of running the installation command using
            Fabric. Note that this return value is a decorated version
            of a string that contains additional meta data about the
            result of the command, in addition to the output generated.
        :rtype: str
        """
        release_path = os.path.join(self._releases, release_id)
        if not self._runner.exists(release_path):
            self._runner.run("virtualenv '%s'" % release_path)

        cmd = [os.path.join(release_path, 'bin', 'pip'), 'install']
        if upgrade:
            cmd.append('--upgrade')

        sources = self._get_install_sources()
        if sources:
            cmd.append(sources)

        cmd.extend("'{0}'".format(package) for package in self._packages)
        return self._runner.run(' '.join(cmd))
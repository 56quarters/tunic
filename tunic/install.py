# -*- coding: utf-8 -*-
#
# Tunic
#
# Copyright 2014-2015 TSH Labs <projects@tshlabs.org>
#
# Available under the MIT license. See LICENSE for details.
#

"""
tunic.install
~~~~~~~~~~~~~

Perform installations on remote machines.
"""

from urlparse import urlparse

import os.path
from .core import try_repeatedly, FabRunner, ProjectBaseMixin


def _is_iterable(val):
    """Ensure that a value is iterable and not some sort of string"""
    try:
        iter(val)
    except (ValueError, TypeError):
        return False
    else:
        return not isinstance(val, basestring)


class VirtualEnvInstallation(ProjectBaseMixin):
    """Install one or multiple packages into a remote Python virtual environment.

    If the remote virtual environment does not already exist, it will be
    created during the install process.

    The installation can use the standard package index (PyPI) to download
    dependencies, or it can use one or multiple alternative installation
    sources (such as a local PyPI instance, Artifactory, the local file system,
    etc.) and ignore the default index. These two modes are mutually exclusive.

    See :doc:`design` for more information about the expected directory
    structure for deployments.

    .. versionadded:: 0.3.0
    """

    # pylint: disable=too-many-arguments
    def __init__(self, base, packages, sources=None, venv_path=None, runner=None):
        """Set the project base directory, packages to install, and optionally
        alternative sources from which to download dependencies and path to the
        virtualenv tool.

        :param str base: Absolute path to the root of the code deploy on
            the remote server
        :param list packages: A collection of package names to install into
            a remote virtual environment.
        :param list sources: A collection of alternative sources from which
            to install dependencies. These sources should be strings that are
            either URLs or file paths. E.g. 'http://pypi.example.com/simple/'
            or '/tmp/build/mypackages'. Paths and URLs may be mixed in the same
            list of sources.
        :param str venv_path: Optional absolute path to the virtualenv tool on
            the remote server. Required if the virtualenv tool is not in the
            PATH on the remote server.
        :param FabRunner runner: Optional runner to use for executing
            remote and local commands to perform the installation.
        :raises ValueError:  If the base directory isn't specified, if no packages
            are given, packages is not an iterable collection of some kind, or if
            sources is specified but not an iterable collection of some kind.

        .. versionchanged:: 0.4.0
            Allow the path to the ``virtualenv`` script on the remote server to be
            specified.
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
        self._venv_path = venv_path if venv_path is not None else 'virtualenv'
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

        If ``upgrade=True`` is passed, packages will be updated to the
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
            self._runner.run("{0} '{1}'".format(self._venv_path, release_path))

        cmd = [os.path.join(release_path, 'bin', 'pip'), 'install']
        if upgrade:
            cmd.append('--upgrade')

        sources = self._get_install_sources()
        if sources:
            cmd.append(sources)

        cmd.extend("'{0}'".format(package) for package in self._packages)
        return self._runner.run(' '.join(cmd))


class StaticFileInstallation(ProjectBaseMixin):
    """Install the contents of a local directory into a remote release
    directory.

    If the remote release directory does not already exist, it will be
    created during the install process.

    See :doc:`design` for more information about the expected directory
    structure for deployments.

    .. versionadded:: 0.5.0
    """

    def __init__(self, base, local_path, runner=None):
        """Set the project base directory on the remote server and path to a
        directory of static content to be installed into a remote release
        directory.

        :param str base: Absolute path to the root of the code deploy on
            the remote server
        :param str local_path: Absolute or relative path to a local directory
            whose contents will be copied to a remote release directory.
        :param FabRunner runner: Optional runner to use for executing
            remote and local commands to perform the installation.
        :raises ValueError: If the base directory or local path isn't
            specified.
        """
        super(StaticFileInstallation, self).__init__(base)

        if not local_path:
            raise ValueError("You must specify a local path")

        self._local_path = local_path
        self._runner = runner if runner is not None else FabRunner()

    def install(self, release_id):
        """Install the contents of the local directory into a release directory.

        If the directory for the given release ID does not exist on the remote
        system, it will be created. The directory will be created according to
        the standard Tunic directory structure (see :doc:`design`).

        Note that the name and path of the local directory is irrelevant, only
        the contents of the specified directory will be transferred to the remote
        server. The contents will end up as children of the release directory on
        the remote server.

        :param str release_id: Timestamp-based identifier for this
            deployment. If this ID corresponds to a directory that already
            exists, contents of the local directory will be copied into
            this directory.
        :return: The results of the ``put`` command using Fabric. This return
            value is an iterable of the paths of all files uploaded on the remote
            server.
        """
        release_path = os.path.join(self._releases, release_id)
        if not self._runner.exists(release_path):
            self._runner.run("mkdir -p '{0}'".format(release_path))

        # Make sure to remove any user supplied globs or trailing slashes
        # so that we can ensure exactly the glob behavior we want from the
        # put command.
        local_path = self._local_path.strip('*').strip(os.path.sep)
        return self._runner.put(os.path.join(local_path, '*'), release_path)


class LocalArtifactInstallation(ProjectBaseMixin):
    """Install a single local file into a remote release directory.

    This can be useful for installing applications that are typically bundled
    as a single file, e.g. Go binaries or Java JAR files, etc.. The artifact
    can optionally be renamed as part of the installation process.

    If the remote release directory does not already exist, it will be
    created during the install process.

    See :doc:`design` for more information about the expected directory
    structure for deployments.

    .. versionadded:: 1.1.0
    """

    def __init__(self, base, local_file, remote_name=None, runner=None):
        """Set the project base directory on the remote server, local artifact (a
        single file) that should be installed remotely, and optional file name
        to rename the artifact to on the remote server.

        :param str base: Absolute path to the root of the code deploy on
            the remote server
        :param str local_file: Relative or absolute path to the local artifact
            to be installed on the remote server.
        :param str remote_name: Optional file name for the artifact after it has
            been installed on the remote server. For example, if the artifact should
            always be called 'application.jar' on the remote server but might
            be named differently ('application-1.2.3.jar') locally, you would
            specify ``remote_name='application.jar'`` for this parameter.
        :param FabRunner runner: Optional runner to use for executing
            remote and local commands to perform the installation.
        :raises ValueError: If the base directory or local file isn't
            specified.
        """
        super(LocalArtifactInstallation, self).__init__(base)

        if not local_file:
            raise ValueError("You must specify a local file path")

        self._local_file = local_file
        self._remote_name = remote_name
        self._runner = runner if runner is not None else FabRunner()

    def install(self, release_id):
        """Install the local artifact into the remote release directory, optionally
        with a different name than the artifact had locally.

        If the directory for the given release ID does not exist on the remote
        system, it will be created. The directory will be created according to
        the standard Tunic directory structure (see :doc:`design`).

        :param str release_id: Timestamp-based identifier for this deployment.
        :return: The results of the ``put`` command using Fabric. This return
            value is an iterable of the paths of all files uploaded on the remote
            server.
        """
        release_path = os.path.join(self._releases, release_id)
        if not self._runner.exists(release_path):
            self._runner.run("mkdir -p '{0}'".format(release_path))

        # The artifact can optionally be renamed when being uploaded to
        # remote server. Useful for when we need a consistent name for
        # each deploy on the remote server but the local artifact includes
        # version numbers or something.
        if self._remote_name is not None:
            destination = os.path.join(release_path, self._remote_name)
        else:
            destination = release_path

        return self._runner.put(self._local_file, destination, mirror_local_mode=True)


def download_url(url, destination, runner=None):
    """Download the given URL with wget to the provided path. The command is
    run via Fabric on the current remote machine. Therefore, the destination
    path should be for the remote machine.

    :param str url: URL to download onto the remote machine
    :param str destination: Path to download the URL to on the remote
        machine
    :param FabRunner runner: Optional runner to use for executing commands.
    :return: The results of the wget call
    """
    runner = runner if runner is not None else FabRunner()
    return try_repeatedly(
        lambda: runner.run("wget --quiet --output-document '{0}' '{1}'".format(destination, url)))


class HttpArtifactInstallation(ProjectBaseMixin):
    """Download and install a single file into a remote release directory.

    This is useful for installing an application that is typically bundled as a
    single file, e.g. Go binaries or Java JAR files, after downloading it from
    some sort of artifact repository (such as a company-wide file server or artifact
    store like Artifactory).

    Downloads are performed over HTTP or HTTPS using a call to ``wget`` on the remote
    machine by default. An alternate download method may be specified when creating a
    new instance of this installer by providing an alternate implementation. The
    download method is expected to conform to the following interface.

    >>> def download(url, destination):
    ...     pass

    Where ``url`` is a URL to the artifact that should be downloaded and ``destination``
    is the absolute path on the remote machine that the artifact should be downloaded
    to. The function should return the result of the Fabric command run
    (e.g. calling 'curl' or 'wget' with :func:`fabric.api.run`).

    If the remote release directory does not already exist, it will be
    created during the install process.

    See :doc:`design` for more information about the expected directory
    structure for deployments.

    .. versionadded:: 1.2.0
    """

    def __init__(self, base, artifact_url, remote_name=None, downloader=None, runner=None):
        """Set the project base directory on the remote server, URL to the artifact
        that should be installed remotely, and optional file name to rename the artifact
        to on the remote server.

        :param str base: Absolute path to the root of the code deploy on
            the remote server
        :param str artifact_url: URL to the artifact to be downloaded and installed on
            the remote server.
        :param str remote_name: Optional file name for the artifact after it has
            been installed on the remote server. For example, if the artifact should
            always be called 'application.jar' on the remote server but might
            be named differently ('application-1.2.3.jar') locally, you would
            specify ``remote_name='application.jar'`` for this parameter.
        :param callable downloader: Function to download the artifact with the
            interface specified above. This is primarily for unit testing but
            may be useful for users that need to be able to customize how the
            artifact HTTP store is accessed.
        :param FabRunner runner: Optional runner to use for executing
            remote and local commands to perform the installation.
        :raises ValueError: If the base directory or artifact URL isn't
            specified.
        """
        super(HttpArtifactInstallation, self).__init__(base)

        if not artifact_url:
            raise ValueError("You must specify a URL")

        self._artifact_url = artifact_url
        self._remote_name = remote_name
        self._downloader = downloader if downloader is not None else download_url
        self._runner = runner if runner is not None else FabRunner()

    @staticmethod
    def _get_file_from_url(url):
        """Get the filename part of the path component from a URL."""
        path = urlparse(url).path
        if not path:
            raise ValueError("Could not extract path from URL '{0}'".format(url))
        name = os.path.basename(path)
        if not name:
            raise ValueError("Could not extract file name from path '{0}'".format(path))
        return name

    def install(self, release_id):
        """Download and install an artifact into the remote release directory,
        optionally with a different name the the artifact had.

        If the directory for the given release ID does not exist on the remote
        system, it will be created. The directory will be created according to
        the standard Tunic directory structure (see :doc:`design`).

        :param str release_id: Timestamp-based identifier for this deployment.
        :return: The results of the download function being run. This return value
            should be the result of running a command with Fabric. By default
            this will be the result of running ``wget``.
        """
        release_path = os.path.join(self._releases, release_id)
        if not self._runner.exists(release_path):
            self._runner.run("mkdir -p '{0}'".format(release_path))

        # The artifact can optionally be renamed to something specific when
        # downloaded on the remote server. In that case use the provided name
        # in the download path. Otherwise, just use the last component of
        # of the URL we're downloading.
        if self._remote_name is not None:
            destination = os.path.join(release_path, self._remote_name)
        else:
            destination = os.path.join(release_path, self._get_file_from_url(self._artifact_url))

        # Note that although the default implementation of a download method
        # accepts a FabRunner instance, we aren't passing our instance here.
        # The reason being, that's only needed for testing the download_url
        # method. If we were testing class, we'd mock out the download method
        # anyway. So, it's not part of the public API of the download interface
        # and we don't deal with it here.
        return self._downloader(self._artifact_url, destination)


# pylint: disable=too-few-public-methods
class LocalArtifactTransfer(object):
    """Transfer a local artifact or directory of artifacts to a remote
    server when entering a context manager and clean the transferred files
    up on the remote server after leaving the block.

    The value yielded when entering the context manager will be the
    full path to the transferred file or directory on the remote
    server. The value yielded will be made up of ``remote_path``
    combined with the right most component of ``local_path``.

    For example, if ``/tmp/myapp`` is a local directory that contains
    several files, the example below will have the following effect.

    >>> transfer = LocalArtifactTransfer('/tmp/myapp', '/tmp/artifacts')
    >>> with transfer as remote_dest:
    ...     pass

    The directory ``myapp`` and its contents would be copied to ``/tmp/artifacts/myapp``
    on the remote machine within the scope of the context manager and
    the value of ``remote_dest`` would be ``/tmp/artifacts/myapp``. After
    the context manager exits ``/tmp/artifacts/myapp`` on the remote machine
    will be removed.

    If ``/tmp/myartifact.zip`` is a single local file, the example below
    will have the following effect.

    >>> transfer = LocalArtifactTransfer('/tmp/myartifact.zip', '/tmp/artifacts')
    >>> with transfer as remote_dest:
    ...     pass

    The file ``myartifact.zip`` would be copied to ``/tmp/artifacts/myartifact.zip``
    on the remote machine within the scope of the context manager and the
    value of ``remote_dest`` would be ``/tmp/artifacts/myartifact.zip``. After
    the context manager exits ``/tmp/artifacts/myartifact.zip`` on the remote
    machine will be removed.

    The destination of the artifacts must be a directory that is writable
    by the user running the deploy or that the user has permission to create.

    The path yielded by the context  will be removed when the context
    manager exits. The local artifacts are not modified or removed on
    exit.

    .. versionadded:: 0.4.0
    """

    def __init__(self, local_path, remote_path, runner=None):
        """Set the local directory that contains the artifacts and
        the remote directory that they should be transferred to.

        Both the local and remote paths should not contain trailing
        slashes. Any trailing slashes will be removed.

        :param str local_path: Directory path on the local machine that
            contains the build artifacts to be transferred (without a
            trailing slash) or the path on the local machine of a single
            file.
        :param str remote_path: Directory on the remote machine that
            the build artifacts should be transferred to (without a
            tailing slash).
        :param FabRunner runner: Optional runner to use for executing
            commands to transfer artifacts.

        .. versionchanged:: 0.5.0
            Trailing slashes are now removed from ``local_path`` and
            ``remote_path``.
        """
        self._local_path = local_path.rstrip(os.path.sep)
        self._remote_path = remote_path.rstrip(os.path.sep)
        self._remote_dest = os.path.join(
            self._remote_path, os.path.basename(self._local_path))
        self._runner = runner if runner is not None else FabRunner()

    def __enter__(self):
        """Transfer the local artifacts to the appropriate place on
        the remote server (ensuring the path exists first) and return
        the remote destination path.

        The remote destination path is the remote path joined with the
        right-most component of the local path.

        :return: The path artifacts were transferred to on the remote
            server
        :rtype: str
        """
        self._runner.run("mkdir -p '{0}'".format(self._remote_path))
        self._runner.put(self._local_path, self._remote_path)
        return self._remote_dest

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove the directory containing the build artifacts on the
        remote server.
        """
        self._runner.run("rm -rf '{0}'".format(self._remote_dest))
        return False

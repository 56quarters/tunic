# -*- coding: utf-8 -*-
#
# Tunic
#
# Copyright 2014-2015 TSH Labs <projects@tshlabs.org>
#
# Available under the MIT license. See LICENSE for details.
#

"""
tunic.core
~~~~~~~~~~

Core Tunic functionality.
"""

import time
import uuid
from datetime import datetime
import os.path

try:
    # Fabric isn't available when our modules are imported during
    # documentation build on readthedocs.org so ignore the error
    # here if we are, in fact, on rtd.
    from fabric.api import (
        put,
        run,
        settings,
        sudo)
    from fabric.contrib.files import exists
except ImportError as e:
    if os.getenv('READTHEDOCS', None) != 'True':
        raise
    put = None
    run = None
    settings = None
    sudo = None
    exists = None

try:
    # Older versions of Fabric didn't have a warn_only context manager
    # so we add the definition here when using an older version.
    from fabric.api import warn_only
except ImportError:
    if settings is not None:
        # If settings is not None, we're not running on readthedocs.org and
        # should provide an implementation of warn_only
        warn_only = lambda: settings(warn_only=True)
    else:
        # Settings is None, we must be on readthedocs.org so just declare
        # warn_only as None similar to how all the other Fabric stuff above
        # is declared.
        warn_only = None


PERMS_FILE_DEFAULT = 'u+rw,g+rw,o+r'
PERMS_DIR_DEFAULT = 'u+rwx,g+rws,o+rx'
RELEASE_DATE_FMT = '%Y%m%d%H%M%S'


def _strip_all(parts):
    return [part.strip() for part in parts]


def split_by_line(content):
    """Split the given content into a list of items by newline.

    Both \r\n and \n are supported. This is done since it seems
    that TTY devices on POSIX systems use \r\n for newlines in
    some instances.

    If the given content is an empty string or a string of only
    whitespace, an empty list will be returned. If the given
    content does not contain any newlines, it will be returned
    as the only element in a single item list.

    Leading and trailing whitespace is remove from all elements
    returned.

    :param str content: Content to split by newlines
    :return: List of items that were separated by newlines.
    :rtype: list
    """
    # Make sure we don't end up splitting a string with
    # just a single trailing \n or \r\n into multiple parts.
    stripped = content.strip()

    if not stripped:
        return []
    if '\r\n' in stripped:
        return _strip_all(stripped.split('\r\n'))
    if '\n' in stripped:
        return _strip_all(stripped.split('\n'))
    return _strip_all([stripped])


def get_current_path(base):
    """Construct the path to the 'current release' symlink based on
    the given project base path.

    Note that this function does not ensure that the 'current' symlink
    exists or points to a valid release, it only returns the full path
    that it should be at based on the given project base directory.

    See :doc:`design` for more information about the expected directory
    structure for deployments.

    .. versionchanged:: 1.1.0
        :class:`ValueError` is now raised for empty ``base`` values.

    :param str base: Project base directory (absolute path)
    :raises ValueError: If the base directory isn't specified
    :return: Path to the 'current' symlink
    :rtype: str
    """
    if not base:
        raise ValueError("You must specify a project base directory")
    return os.path.join(base, 'current')


def get_releases_path(base):
    """Construct the path to the directory that contains all releases
    based on the given project base path.

    Note that this function does not ensure that the releases directory
    exists, it only returns the full path that it should be at based on
    the given project base directory.

    See :doc:`design` for more information about the expected directory
    structure for deployments.

    .. versionchanged:: 1.1.0
        :class:`ValueError` is now raised for empty ``base`` values.

    :param str base: Project base directory (absolute path)
    :raises ValueError: If the base directory isn't specified
    :return: Path to the releases directory
    :rtype: str
    """
    if not base:
        raise ValueError("You must specify a project base directory")
    return os.path.join(base, 'releases')


def get_release_id(version=None):
    """Get a unique, time-based identifier for a deployment
    that optionally, also includes some sort of version number
    or release.

    If a version is supplied, the release ID will be of the form
    '$timestamp-$version'. For example:

    >>> get_release_id(version='1.4.1')
    '20140214231159-1.4.1'

    If the version is not supplied the release ID will be of the
    form '$timestamp'. For example:

    >>> get_release_id()
    '20140214231159'

    The timestamp component of this release ID will be generated
    using the current time in UTC.

    :param str version: Version to include in the release ID
    :return: Unique name for this particular deployment
    :rtype: str
    """
    ts = datetime.utcnow().strftime(RELEASE_DATE_FMT)

    if version is None:
        return ts
    return '{0}-{1}'.format(ts, version)


class FabRunner(object):
    """Wrapper for executing Fabric commands that allows us
    to globally disable use of shell wrappers and allow for
    easy testing.

    Note that if ``shell=True`` is not explicitly passed to
    methods in this class, use of a shell will be disabled.
    This is largely done in order to make sure that commands
    executed using ``sudo`` match any previously set grants
    (where as wrapping them with /bin/bash -c 'cmd' would
    break grants).
    """

    @staticmethod
    def run(*args, **kwargs):
        """Execute the Fabric :func:`run` function with the given args."""
        if 'shell' not in kwargs:
            kwargs['shell'] = False
        return run(*args, **kwargs)

    @staticmethod
    def sudo(*args, **kwargs):
        """Execute the Fabric :func:`sudo` function with the given args."""
        if 'shell' not in kwargs:
            kwargs['shell'] = False
        return sudo(*args, **kwargs)

    @staticmethod
    def exists(*args, **kwargs):
        """Execute the Fabric :func:`fabric.contrib.files.exists` function
        with the given args.
        """
        return exists(*args, **kwargs)

    @staticmethod
    def put(*args, **kwargs):
        """Execute the Fabric :func:`put` function with the given args."""
        return put(*args, **kwargs)


def try_repeatedly(method, max_retries=1, delay=0):
    """Execute the given Fabric call, retrying up to a certain number of times.

    The method is expected to be wrapper around a Fabric :func:`run` or :func:`sudo`
    call that returns the results of that call. The call will be executed at least
    once, and up to :code:`max_retries` additional times until the call executes with
    out failing.

    Optionally, a delay in seconds can be specified in between successive calls.

    :param callable method: Wrapped Fabric method to execute
    :param int max_retries: Max number of times to retry execution after a failed call
    :param float delay: Number of seconds between successive calls of :code:`method`
    :return: The results of running :code:`method`
    """
    tries = 0

    with warn_only():
        while tries < max_retries:
            res = method()
            if not res.failed:
                return res

            tries += 1
            time.sleep(delay)
    # final try outside the warn_only block so that if it
    # fails it'll just blow up or do whatever it was going to
    # do anyway.
    return method()


# pylint: disable=too-few-public-methods
class ProjectBaseMixin(object):
    """Base for setting project directories from a given
    project root directory.

    :ivar str _base: Project root directory
    :ivar str _current: "current release" symlink
    :ivar str _release: Directory of all releases
    """

    def __init__(self, base):
        """Set the project directories based on a given root.

        :param str base: Project root directories.
        :raises ValueError: If ``base`` is None or empty
        """
        if not base:
            raise ValueError("You must specify a project base directory")

        self._base = base
        self._current = get_current_path(base)
        self._releases = get_releases_path(base)


class ReleaseManager(ProjectBaseMixin):
    """Functionality for manipulation of multiple releases of a project
    deployed on a remote server.

    Note that functionality for managing releases relies on them being
    named with a timestamp based prefix that allows them to be naturally
    sorted -- such as with the :func:`get_release_id` function.

    See :doc:`design` for more information about the expected directory
    structure for deployments.
    """

    def __init__(self, base, runner=None):
        """Set the base path to the project that we will be managing
        releases of and an optional :class:`FabRunner` implementation
        to use for running commands.

        :param str base: Absolute path to the root of the code deploy
        :param FabRunner runner: Optional runner to use for executing
            remote commands to manage releases.
        :raises ValueError: If the base directory isn't specified

        .. versionchanged:: 0.3.0
            :class:`ValueError` is now raised for empty ``base`` values.
        """
        super(ReleaseManager, self).__init__(base)
        self._runner = runner if runner is not None else FabRunner()

    def get_current_release(self):
        """Get the release ID of the "current" deployment, None if
        there is no current deployment.

        This method performs one network operation.

        :return: Get the current release ID
        :rtype: str
        """
        current = self._runner.run("readlink '{0}'".format(self._current))
        if current.failed:
            return None
        return os.path.basename(current.strip())

    def get_releases(self):
        """Get a list of all previous deployments, newest first.

        This method performs one network operation.

        :return: Get an ordered list of all previous deployments
        :rtype: list
        """
        return split_by_line(
            self._runner.run("ls -1r '{0}'".format(self._releases)))

    def get_previous_release(self):
        """Get the release ID of the deployment immediately
        before the "current" deployment, ``None`` if no previous
        release could be determined.

        This method performs two network operations.

        :return: The release ID of the release previous to the
            "current" release.
        :rtype: str
        """
        releases = self.get_releases()
        if not releases:
            return None

        current = self.get_current_release()
        if not current:
            return None

        try:
            current_idx = releases.index(current)
        except ValueError:
            return None

        try:
            return releases[current_idx + 1]
        except IndexError:
            return None

    def set_current_release(self, release_id):
        """Change the 'current' symlink to point to the given
        release ID.

        The 'current' symlink will be updated in a way that ensures
        the switch is done atomically.

        This method performs two network operations.

        :param str release_id: Release ID to mark as the current
            release
        """
        self._set_current_release(release_id, str(uuid.uuid4()))

    # pylint: disable=missing-docstring
    def _set_current_release(self, release_id, rand):
        # Set the current release with a specific random file
        # name. Useful for unit testing when we need to check
        # for the exact arguments passed to the runner mock
        tmp_path = os.path.join(self._base, rand)
        target = os.path.join(self._releases, release_id)

        # First create a link with a random name to point to the
        # newly created release, then rename it to 'current' such
        # that the symlink is updated atomically [1].
        # [1] - http://rcrowley.org/2010/01/06/things-unix-can-do-atomically
        self._runner.run("ln -s '{0}' '{1}'".format(target, tmp_path))
        self._runner.run("mv -T '{0}' '{1}'".format(tmp_path, self._current))

    def cleanup(self, keep=5):
        """Remove all but the ``keep`` most recent releases.

        If any of the candidates for deletion are pointed to by the
        'current' symlink, they will not be deleted.

        This method performs N + 2 network operations where N is the
        number of old releases that are cleaned up.

        :param int keep: Number of old releases to keep around
        """
        releases = self.get_releases()
        current_version = self.get_current_release()
        to_delete = [version for version in releases[keep:] if version != current_version]

        for release in to_delete:
            self._runner.run("rm -rf '{0}'".format(os.path.join(self._releases, release)))


class ProjectSetup(ProjectBaseMixin):
    """Functionality for performing the initial creation of project
    directories and making sure their permissions are reasonable on
    a remote server.

    Note that by default methods in this class rely on being able to
    execute commands with the Fabric ``sudo`` function. This can be
    disabled by passing the ``use_sudo=False`` flag to methods that
    accept it.

    See :doc:`design` for more information about the expected directory
    structure for deployments.
    """

    def __init__(self, base, runner=None):
        """Set the base path to the project that will be setup and an
        optional :class:`FabRunner` implementation to use for running
        commands.

        :param str base: Absolute path to the root of the code deploy
        :param FabRunner runner: Optional runner to use for executing
            remote commands to set up the deploy.
        :raises ValueError: If the base directory isn't specified

        .. versionchanged:: 0.3.0
            :class:`ValueError` is now raised for empty ``base`` values.
        """
        super(ProjectSetup, self).__init__(base)
        self._runner = runner if runner is not None else FabRunner()

    def setup_directories(self, use_sudo=True):
        """Create the minimal required directories for deploying multiple
        releases of a project.

        By default, creation of directories is done with the Fabric
        ``sudo`` function but can optionally use the ``run`` function.

        This method performs one network operation.

        :param bool use_sudo: If ``True``, use ``sudo()`` to create required
            directories. If ``False`` try to create directories using the
            ``run()`` command.
        """
        runner = self._runner.sudo if use_sudo else self._runner.run
        runner("mkdir -p '{0}'".format(self._releases))

    def set_permissions(
            self, owner, file_perms=PERMS_FILE_DEFAULT,
            dir_perms=PERMS_DIR_DEFAULT, use_sudo=True):
        """Set the owner and permissions of the code deploy.

        The owner will be set recursively for the entire code deploy.

        The directory permissions will be set on only the base of the
        code deploy and the releases directory. The file permissions
        will be set recursively for the entire code deploy.

        If not specified default values will be used for file or directory
        permissions.

        By default the Fabric ``sudo`` function will be used for changing
        the owner and permissions of the code deploy. Optionally, you can
        pass the ``use_sudo=False`` argument to skip trying to change the
        owner of the code deploy and to use the ``run`` function to change
        permissions.

        This method performs between three and four network operations
        depending on if ``use_sudo`` is false or true, respectively.

        :param str owner: User and group in the form 'owner:group' to
            set for the code deploy.
        :param str file_perms: Permissions to set for all files in the
            code deploy in the form 'u+perms,g+perms,o+perms'. Default
            is ``u+rw,g+rw,o+r``.
        :param str dir_perms: Permissions to set for the base and releases
            directories in the form 'u+perms,g+perms,o+perms'. Default
            is ``u+rwx,g+rws,o+rx``.
        :param bool use_sudo: If ``True``, use ``sudo()`` to change ownership
            and permissions of the code deploy. If ``False`` try to change
            permissions using the ``run()`` command, do not change ownership.

        .. versionchanged:: 0.2.0
            ``use_sudo=False`` will no longer attempt to change ownership of
            the code deploy since this will just be a no-op or fail.

        """
        runner = self._runner.sudo if use_sudo else self._runner.run

        if use_sudo:
            runner("chown -R '{0}' '{1}'".format(owner, self._base))

        for path in (self._base, self._releases):
            runner("chmod '{0}' '{1}'".format(dir_perms, path))

        runner("chmod -R '{0}' '{1}'".format(file_perms, self._base))

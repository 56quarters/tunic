# -*- coding: utf-8 -*-

"""
tshfab.core
~~~~~~~~~~~

Core TSH Fab functionality.

:copyright: (c) 2014 TSH Labs
:license: MIT, see LICENSE for more details.
"""

import uuid
from datetime import datetime

import os.path
from fabric.api import (
    run,
    sudo)


PERMS_FILE_DEFAULT = 'u+rw,g+rw,o+r'
PERMS_DIR_DEFAULT = 'u+rwx,g+rws,o+rx'
RELEASE_DATE_FMT = '%Y%m%d%H%M%S'

_strip_all = lambda parts: [part.strip() for part in parts]


def split_by_line(content):
    """Split the given content into a list of items by newline.

    Both \n\r and \n are supported. This is done since it seems
    that TTY devices on POSIX systems use \n\r for newlines in
    some instances.

    If the given content does not contain any newlines, it will
    be returned as the only element in a single item list.

    Leading and trailing whitespace is remove from all elements
    returned.

    :param str content: Content to split by newlines
    :return: List of items that were separated by newlines.
    :rtype: list
    """
    # Make sure we don't end up splitting a string with
    # just a single trailing \n or \n\r into multiple parts.
    stripped = content.strip()

    if '\n\r' in stripped:
        return _strip_all(stripped.split('\n\r'))
    if '\n' in stripped:
        return _strip_all(stripped.split('\n'))
    return _strip_all([stripped])


def get_current_path(base):
    """Construct the path to the 'current release' symlink based on
    the given project base path.

    :param str base: Project base directory (absolute path)
    :return: Path to the 'current' symlink
    :rtype: str
    """
    return os.path.join(base, 'current')


def get_releases_path(base):
    """Construct the path to the directory that contains all releases
    based on the given project base path.

    :param str base: Project base directory (absolute path)
    :return: Path to the releases directory
    :rtype: str
    """
    return os.path.join(base, 'releases')


def get_release_id(version=None):
    """Get a unique, time-based identifier for a deployment
    that optionally, also includes some sort of version number
    or release.

    :param str version: Version to include in the release ID
    :return: Unique name for this particular deployment
    :rtype: str
    """
    ts = datetime.utcnow().strftime(RELEASE_DATE_FMT)

    if version is None:
        return ts
    return '%s-%s' % (ts, version)


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
        """
        self._base = base
        self._current = get_current_path(base)
        self._releases = get_releases_path(base)


class ReleaseManager(ProjectBaseMixin):
    """Functionality for manipulation of multiple releases of a project
    deployed on a remote server.

    Note that functionality for managing releases relies on them being
    named with a timestamp based prefix that allows them to be naturally
    sorted -- such as with the :func:`get_release_id` function.
    """

    def __init__(self, base, runner=None):
        """Set the base path to the project that we will be managing
        releases of and an optional :class:`FabRunner` implementation
        to use for running commands.

        :param str base: Absolute path to the root of the code deploy
        :param FabRunner runner: Optional runner to use for executing
            remote commands to manage releases.
        """
        super(ReleaseManager, self).__init__(base)
        self._runner = runner if runner is not None else FabRunner()

    def get_current_release(self):
        """Get the release ID of the "current" deployment, None if
        there is no current deployment.

        :return: Get the current release ID
        :rtype: str
        """
        current = self._runner.run('readlink %s' % self._current)
        if current.failed:
            return None
        return os.path.basename(current.strip())

    def get_releases(self):
        """Get a list of all previous deployments, newest first.

        :return: Get an ordered list of all previous deployments
        :rtype: list
        """
        return split_by_line(
            self._runner.run('ls -1r %s' % self._releases))

    def get_previous_release(self):
        """Get the release ID of the deployment immediately
        before the "current" deployment, ``None`` if no previous
        release could be determined.

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

        :param str release_id: Release ID to mark as the current
            release
        """
        tmp_path = os.path.join(self._base, str(uuid.uuid4()))
        target = os.path.join(self._releases, release_id)

        # First create a link with a random name to point to the
        # newly created release, then rename it to 'current' such
        # that the symlink is updated atomically [1].
        # [1] - http://rcrowley.org/2010/01/06/things-unix-can-do-atomically
        self._runner.run("ln -s %s %s" % (target, tmp_path))
        self._runner.run("mv -T %s %s" % (tmp_path, self._current))

    def cleanup(self, keep=5):
        """Remove all but the ``keep`` most recent releases.

        If any of the candidates for deletion are pointed to by the
        'current' symlink, they will not be deleted.

        :param int keep: Number of old releases to keep around
        """
        releases = self.get_releases()
        current_version = self.get_current_release()
        to_delete = [version for version in releases[keep:] if version != current_version]

        for release in to_delete:
            self._runner.run("rm -rf %s" % os.path.join(self._releases, release))


class ProjectSetup(ProjectBaseMixin):
    """Functionality for performing the initial creation of project
    directories and making sure their permissions are reasonable on
    a remote server.

    Note that by default methods in this class rely on being able to
    execute commands with the Fabric ``sudo`` function. This can be
    disabled by passing the ``use_sudo=False`` flag to methods that
    accept it.
    """

    def __init__(self, base, runner=None):
        """Set the base path to the project that will be setup and an
        optional :class:`FabRunner` implementation to use for running
        commands.

        :param str base: Absolute path to the root of the code deploy
        :param FabRunner runner: Optional runner to use for executing
            remote commands to set up the deploy.
        """
        super(ProjectSetup, self).__init__(base)
        self._runner = runner if runner is not None else FabRunner()

    def setup_directories(self, use_sudo=True):
        """Create the minimal required directories for deploying multiple
        releases of a project.

        By default, creation of directories is done with the Fabric
        ``sudo`` function but can optionally use the ``run`` function.

        :param bool use_sudo: If ``True``, use ``sudo()`` to create required
            directories. If ``False`` try to create directories using the
            ``run()`` command.
        """
        runner = self._runner.sudo if use_sudo else self._runner.run
        for path in (self._base, self._releases):
            runner('mkdir -p %s' % path)

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
        the owner and permissions of the code deploy. Optionally, the Fabric
        ``run`` function may be used instead. If sudo is not used and the code
        deploy is not already owned by the user running the command it will
        fail.

        :param str owner: User and group in the form 'owner:group' to
            set for the code deploy.
        :param str file_perms: Permissions to set for all files in the
            code deploy in the form 'u+perms,g+perms,o+perms'. Default
            is ``u+rw,g+rw,o+r``.
        :param str dir_perms: Permissions to set for the base and releases
            directories in the form 'u+perms,g+perms,o+perms'. Default
            is ``u+rwx,g+rws,o+rx``.
        :param bool use_sudo: If ``True``, use ``sudo()`` to change ownership
            and permissions of the code deploy. If ``False`` try to
            change ownership using the ``run()`` command.
        """
        runner = self._runner.sudo if use_sudo else self._runner.run
        runner('chown -R %s %s' % (owner, self._base))

        for path in (self._base, self._releases):
            runner('chmod %s %s' % (dir_perms, path))

        runner('chmod -R %s %s' % (file_perms, self._base))

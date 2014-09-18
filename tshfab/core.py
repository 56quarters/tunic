# -*- coding: utf-8 -*-


import uuid

import os.path
from fabric.api import (
    run,
    sudo)


class FabRunner(object):
    @staticmethod
    def run(*args, **kwargs):
        if 'use_shell' not in kwargs:
            kwargs['use_shell'] = False
        return run(*args, **kwargs)

    @staticmethod
    def sudo(*args, **kwargs):
        if 'use_shell' not in kwargs:
            kwargs['use_shell'] = False
        return sudo(*args, **kwargs)


class ProjectBaseMixin(object):
    def __init__(self, base):
        self._base = base
        self._current = os.path.join(base, 'current')
        self._releases = os.path.join(base, 'releases')


class ReleaseManager(ProjectBaseMixin):
    """

    """

    def __init__(self, base, runner=None):
        """



        :param base:
        :param runner:
        :return:
        """
        super(ReleaseManager, self).__init__(base)
        self._runner = runner if runner is not None else FabRunner()

    def get_current_release(self):
        """



        :return:
        :rtype: str
        """
        current = self._runner.run('readlink %s' % self._current)
        if not current:
            return None
        return current.strip()

    def get_releases(self):
        """



        :return:
        :rtype: list
        """
        return [item.strip() for item in
                self._runner.run('ls -1r %s' % self._releases).split()]

    def get_previous_release(self):
        """



        :return:
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
        """


        :param str release_id:
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
        """


        :param int keep:
        """
        releases = self.get_releases()
        current_version = self.get_current_release()
        to_delete = [version for version in releases[keep:] if version != current_version]

        for release in to_delete:
            self._runner.run("rm -rf %s" % os.path.join(self._releases, release))


class ProjectSetup(ProjectBaseMixin):
    """



    """

    def __init__(self, base, runner=None):
        """



        :param base:
        :param runner:
        :return:
        """
        super(ProjectSetup, self).__init__(base)
        self._runner = runner if runner is not None else FabRunner()

    def setup_directories(self, use_sudo=True):
        """



        :param use_sudo:
        :return:
        """
        runner = self._runner.sudo if use_sudo else self._runner.run
        for path in (self._base, self._releases):
            runner('mkdir -p %s' % path)

    def set_permissions(
            self, owner, file_perms='u+rw,g+rw,o+r',
            dir_perms='u+rwx,g+rws,o+rx', use_sudo=True):
        """



        :param owner:
        :param file_perms:
        :param dir_perms:
        :param use_sudo:
        :return:
        """
        runner = self._runner.sudo if use_sudo else self._runner.run
        runner('chown -R %s %s' % (owner, self._base))

        for path in (self._base, self._releases):
            runner('chmod %s %s' % (dir_perms, path))

        runner('chmod -R %s %s' % (file_perms, self._base))

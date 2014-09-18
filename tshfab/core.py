# -*- coding: utf-8 -*-


import uuid

import os.path
from fabric.api import (
    run,
    sudo)


class FabRunner(object):
    @staticmethod
    def run(*args, **kwargs):
        return run(*args, **kwargs)

    @staticmethod
    def sudo(*args, **kwargs):
        return sudo(*args, **kwargs)


class ProjectBaseMixin(object):
    def __init__(self, base):
        self._base = base
        self._current = os.path.join(base, 'current')
        self._releases = os.path.join(base, 'releases')


class ReleaseManager(ProjectBaseMixin):
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
        """
        current = self._runner.run('readlink %s' % self._current)
        if not current:
            return None
        return current.strip()

    def get_releases(self):
        """



        :return:
        """
        return [item.strip() for item in
                self._runner.run('ls -1r %s' % self._releases).split()]

    def get_previous_release(self):
        """



        :return:
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


        :param release_id:
        :return:
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


        :param keep:
        :return:
        """
        releases = self.get_releases()
        current_version = self.get_current_release()
        to_delete = [version for version in releases[keep:] if version != current_version]

        for release in to_delete:
            self._runner.run("rm -rf %s" % os.path.join(self._releases, release))


class ProjectSetup(ProjectBaseMixin):
    def setup_directories(self):
        pass

    def set_permissions(self):
        pass
# -*- coding: utf-8 -*-

import mock
import pytest

import tunic.core
import tunic.install


class TestVirtualEnvInstallation(object):
    def setup(self):
        self.runner = mock.Mock(spec=tunic.core.FabRunner)

    def test_missing_packages(self):
        with pytest.raises(ValueError):
            tunic.install.VirtualEnvInstallation(
                '/tmp/test', [], runner=self.runner)

    def test_non_iterable_packages(self):
        with pytest.raises(ValueError):
            tunic.install.VirtualEnvInstallation(
                '/tmp/test', 'foo', runner=self.runner)

    def test_non_iterable_string_sources(self):
        with pytest.raises(ValueError):
            tunic.install.VirtualEnvInstallation(
                '/tmp/test', ['foo'], '/tmp/wheelhouse', runner=self.runner)

    def test_non_iterable_int_sources(self):
        with pytest.raises(ValueError):
            tunic.install.VirtualEnvInstallation(
                '/tmp/test', ['foo'], 42, runner=self.runner)

    def test_get_install_sources_no_sources(self):
        installer = tunic.install.VirtualEnvInstallation(
            '/tmp/test', ['foo'], runner=self.runner)
        assert '' == installer._get_install_sources()

    def test_get_install_sources_one_source(self):
        installer = tunic.install.VirtualEnvInstallation(
            '/tmp/test', ['foo'], ['/tmp/wheelhouse'], runner=self.runner)
        sources = installer._get_install_sources()
        assert '--no-index' in sources
        assert '--find-links' in sources
        assert '/tmp/wheelhouse' in sources

    def test_get_install_sources_many_sources(self):
        installer = tunic.install.VirtualEnvInstallation(
            '/tmp/test', ['foo'], ['/tmp/wheelhouse1', '/tmp/wheelhouse2'], runner=self.runner)
        sources = installer._get_install_sources()
        assert '--no-index' in sources
        assert 2 == sources.count('--find-links')
        assert '/tmp/wheelhouse1' in sources
        assert '/tmp/wheelhouse2' in sources

    def test_install_no_existing_virtual_env(self):
        installer = tunic.install.VirtualEnvInstallation(
            '/tmp/test', ['foo'], runner=self.runner)

        self.runner.exists.return_value = False

        installer.install('19970829021442')

        self.runner.run.assert_any_call(
            "virtualenv '/tmp/test/releases/19970829021442'")

    def test_install_no_existing_virtual_env_custom_location(self):
        installer = tunic.install.VirtualEnvInstallation(
            '/tmp/test', ['foo'], venv_path='/opt/python/bin/virtualenv',
            runner=self.runner)

        self.runner.exists.return_value = False

        installer.install('19970829021442')

        self.runner.run.assert_any_call(
            "/opt/python/bin/virtualenv '/tmp/test/releases/19970829021442'")

    def test_install_with_upgrade(self):
        installer = tunic.install.VirtualEnvInstallation(
            '/tmp/test', ['foo', 'bar'], runner=self.runner)

        self.runner.exists.return_value = True

        installer.install('19970829021442', upgrade=True)
        self.runner.run.assert_any_call(
            "/tmp/test/releases/19970829021442/bin/pip install --upgrade 'foo' 'bar'")

    def test_install_no_upgrade(self):
        installer = tunic.install.VirtualEnvInstallation(
            '/tmp/test', ['foo', 'bar'], runner=self.runner)

        self.runner.exists.return_value = True

        installer.install('19970829021442', upgrade=False)
        self.runner.run.assert_any_call(
            "/tmp/test/releases/19970829021442/bin/pip install 'foo' 'bar'")

    def test_install_with_source(self):
        installer = tunic.install.VirtualEnvInstallation(
            '/tmp/test', ['foo'], ['/tmp/wheelhouse'], runner=self.runner)

        self.runner.exists.return_value = True

        installer.install('19970829021442', upgrade=False)
        self.runner.run.assert_any_call(
            "/tmp/test/releases/19970829021442/bin/pip install "
            "--no-index --find-links '/tmp/wheelhouse' 'foo'")


class TestLocalArtifactTransfer(object):
    def setup(self):
        self.runner = mock.Mock(spec=tunic.core.FabRunner)

    def test_as_context_manager(self):
        local_path = '/tmp/build'
        remote_path = '/tmp/artifacts'

        transfer = tunic.install.LocalArtifactTransfer(
            local_path, remote_path, runner=self.runner)

        with transfer as remote:
            assert remote == remote_path

        self.runner.run.assert_any_call(
            "mkdir -p '/tmp/artifacts'")

        assert self.runner.put.called

        self.runner.run.assert_any_call(
            "rm -rf '/tmp/artifacts'")

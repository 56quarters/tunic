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


class TestStaticFileInstallation(object):
    def setup(self):
        self.runner = mock.Mock(spec=tunic.core.FabRunner)

    def test_missing_base(self):
        with pytest.raises(ValueError):
            tunic.install.StaticFileInstallation(None, 'foo')

    def test_missing_local_path(self):
        with pytest.raises(ValueError):
            tunic.install.StaticFileInstallation('foo', None)

    def test_install_directory_does_not_exist(self):
        self.runner.exists.return_value = False

        installer = tunic.install.StaticFileInstallation(
            '/srv/www/myapp', 'mystaticsite', runner=self.runner)
        installer.install('20141011145205')

        self.runner.run.assert_called_once_with(
            "mkdir -p '/srv/www/myapp/releases/20141011145205'")
        self.runner.put.assert_called_once_with(
            'mystaticsite/*', '/srv/www/myapp/releases/20141011145205')

    def test_install_directory_exists_local_path_has_glob(self):
        self.runner.exists.return_value = True

        installer = tunic.install.StaticFileInstallation(
            '/srv/www/myapp', 'mystaticsite*', runner=self.runner)
        installer.install('20141011145205')

        self.runner.put.assert_called_once_with(
            'mystaticsite/*', '/srv/www/myapp/releases/20141011145205')

    def test_install_directory_exists_local_path_trailing_slash(self):
        self.runner.exists.return_value = True

        installer = tunic.install.StaticFileInstallation(
            '/srv/www/myapp', 'mystaticsite/', runner=self.runner)
        installer.install('20141011145205')

        self.runner.put.assert_called_once_with(
            'mystaticsite/*', '/srv/www/myapp/releases/20141011145205')


class TestLocalArtifactInstallation(object):
    def setup(self):
        self.runner = mock.Mock(spec=tunic.core.FabRunner)

    def test_missing_base(self):
        with pytest.raises(ValueError):
            tunic.install.LocalArtifactInstallation(None, 'foo')

    def test_missing_local_path(self):
        with pytest.raises(ValueError):
            tunic.install.LocalArtifactInstallation('foo', None)

    def test_install_directory_does_not_exist(self):
        self.runner.exists.return_value = False

        installer = tunic.install.LocalArtifactInstallation(
            '/srv/www/myapp', '/tmp/someapp-1.2.3.jar', runner=self.runner)
        installer.install('20141011145205')

        self.runner.run.assert_called_once_with(
            "mkdir -p '/srv/www/myapp/releases/20141011145205'")
        self.runner.put.assert_called_once_with(
            '/tmp/someapp-1.2.3.jar',
            '/srv/www/myapp/releases/20141011145205',
            mirror_local_mode=True
        )

    def test_install_rename_artifact(self):
        self.runner.exists.return_value = True

        installer = tunic.install.LocalArtifactInstallation(
            '/srv/www/myapp', '/tmp/someapp-1.2.3.jar',
            remote_name='someapp.jar', runner=self.runner)
        installer.install('20141011145205')

        self.runner.put.assert_called_once_with(
            '/tmp/someapp-1.2.3.jar',
            '/srv/www/myapp/releases/20141011145205/someapp.jar',
            mirror_local_mode=True
        )

    def test_install_do_not_rename(self):
        self.runner.exists.return_value = True

        installer = tunic.install.LocalArtifactInstallation(
            '/srv/www/myapp', '/tmp/someapp-1.2.3.jar',
            runner=self.runner)
        installer.install('20141011145205')

        self.runner.put.assert_called_once_with(
            '/tmp/someapp-1.2.3.jar',
            '/srv/www/myapp/releases/20141011145205',
            mirror_local_mode=True
        )


class TestHttpArtifactInstallation(object):
    def setup(self):
        self.runner = mock.Mock(spec=tunic.core.FabRunner)
        self.downloader = mock.Mock()

    def test_get_file_from_url_no_path(self):
        url = 'https://www.example.com'
        with pytest.raises(ValueError):
            tunic.install.HttpArtifactInstallation._get_file_from_url(url)

    def test_get_file_from_url_no_file(self):
        url = 'https://www.example.com/'
        with pytest.raises(ValueError):
            tunic.install.HttpArtifactInstallation._get_file_from_url(url)

    def test_get_file_from_url_1(self):
        url = 'https://www.example.com/some/file.jar?dl=1'
        assert 'file.jar' == tunic.install.HttpArtifactInstallation._get_file_from_url(url)

    def test_get_file_from_url_2(self):
        url = 'https://www.example.com/app.pex'
        assert 'app.pex' == tunic.install.HttpArtifactInstallation._get_file_from_url(url)

    def test_missing_base(self):
        with pytest.raises(ValueError):
            tunic.install.HttpArtifactInstallation('', 'http://www.example.com/foo.jar')

    def test_missing_url(self):
        with pytest.raises(ValueError):
            tunic.install.HttpArtifactInstallation('/some/path', '')

    def test_install_directory_does_not_exist(self):
        self.runner.exists.return_value = False
        installer = tunic.install.HttpArtifactInstallation(
            '/srv/www/myapp', 'http://localhost/app-1.2.3.jar',
            downloader=self.downloader, runner=self.runner)

        installer.install('20160206111401')

        self.runner.run.assert_called_once_with(
            "mkdir -p '/srv/www/myapp/releases/20160206111401'")
        self.downloader.assert_called_once_with(
            'http://localhost/app-1.2.3.jar',
            '/srv/www/myapp/releases/20160206111401/app-1.2.3.jar')

    def test_install_rename_artifact(self):
        self.runner.exists.return_value = True
        installer = tunic.install.HttpArtifactInstallation(
            '/srv/www/myapp', 'http://localhost/app-1.2.3.jar',
            remote_name='app.jar', downloader=self.downloader, runner=self.runner)

        installer.install('20160206111401')

        self.downloader.assert_called_once_with(
            'http://localhost/app-1.2.3.jar',
            '/srv/www/myapp/releases/20160206111401/app.jar')


class TestLocalArtifactTransfer(object):
    def setup(self):
        self.runner = mock.Mock(spec=tunic.core.FabRunner)

    def test_as_context_manager_with_local_directory(self):
        local_path = '/tmp/myapp'
        remote_path = '/tmp/build'

        transfer = tunic.install.LocalArtifactTransfer(
            local_path, remote_path, runner=self.runner)

        with transfer as remote:
            assert remote == '/tmp/build/myapp'

        self.runner.run.assert_any_call(
            "mkdir -p '/tmp/build'")

        assert self.runner.put.called

        self.runner.run.assert_any_call(
            "rm -rf '/tmp/build/myapp'")

    def test_as_context_manager_with_local_file(self):
        local_path = '/tmp/myapp.zip'
        remote_path = '/tmp/build'

        transfer = tunic.install.LocalArtifactTransfer(
            local_path, remote_path, runner=self.runner)

        with transfer as remote:
            assert remote == '/tmp/build/myapp.zip'

        self.runner.run.assert_any_call(
            "mkdir -p '/tmp/build'")

        assert self.runner.put.called

        self.runner.run.assert_any_call(
            "rm -rf '/tmp/build/myapp.zip'")

    def test_as_context_manager_with_trailing_slashes(self):
        local_path = '/tmp/myapp/'
        remote_path = '/tmp/build/'

        transfer = tunic.install.LocalArtifactTransfer(
            local_path, remote_path, runner=self.runner)

        with transfer as remote:
            assert remote == '/tmp/build/myapp'

        self.runner.run.assert_any_call(
            "mkdir -p '/tmp/build'")

        assert self.runner.put.called

        self.runner.run.assert_any_call(
            "rm -rf '/tmp/build/myapp'")

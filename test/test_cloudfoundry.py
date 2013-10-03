import os
import sys
import tempfile
import shutil
from dingus import Dingus
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import CloudFoundryUtil
from build_pack_utils import CloudFoundryInstaller


class TestCloudFoundryUtil(object):

    def setUp(self):
        self.old_sys_argv = sys.argv
        sys.argv = [
            '/tmp/buildpacks/my-buildpack/bin/compile',
            os.path.join(tempfile.gettempdir(), '/tmp/staged/app'),
            os.path.join(tempfile.gettempdir(), '/tmp/cache')]
        os.environ['MEMORY_LIMIT'] = '64m'
        os.environ['TMPDIR'] = '/tmp'

    def tearDown(self):
        path = os.path.join(tempfile.gettempdir(), '/tmp/staged/app')
        if os.path.exists(path):
            shutil.rmtree(path)
        path = os.path.join(tempfile.gettempdir(), '/tmp/cache')
        if os.path.exists(path):
            shutil.rmtree(path)
        sys.argv = self.old_sys_argv

    @with_setup(setup=setUp, teardown=tearDown)
    def test_load_env(self):
        cf = CloudFoundryUtil()
        assert '/tmp/staged/app' == cf.BUILD_DIR
        assert '/tmp/cache' == cf.CACHE_DIR
        assert '/tmp' == cf.TEMP_DIR
        assert '/tmp/buildpacks/my-buildpack' == cf.BP_DIR
        assert '64m' == cf.MEMORY_LIMIT
        assert os.path.exists(cf.BUILD_DIR)
        assert os.path.exists(cf.CACHE_DIR)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_load_json_config_file(self):
        cf = CloudFoundryUtil()
        cfg = cf.load_json_config_file('./test/data/config.json')
        assert cfg['int'] == 5
        assert cfg['string'] == '1234'
        assert len(cfg['list']) == 5
        assert cfg['list'][3] == 4
        assert 'y' in cfg['map'].keys()
        assert cfg['map']['z'] == 3

    @with_setup(setup=setUp, teardown=tearDown)
    def test_load_json_config_file_from(self):
        cf = CloudFoundryUtil()
        cfg = cf.load_json_config_file_from('./test/data/', 'config.json')
        assert cfg['int'] == 5
        assert cfg['string'] == '1234'
        assert len(cfg['list']) == 5
        assert cfg['list'][3] == 4
        assert 'y' in cfg['map'].keys()
        assert cfg['map']['z'] == 3


class TestCloudFoundryInstallerBinaries(object):
    def test_install_binary_cached(self):
        # Setup mocks
        #  use __new__ to skip constructor, we set that up here
        installer = object.__new__(CloudFoundryInstaller)
        installer._cf = Dingus('cf',
                               BUILD_DIR='/tmp/build_dir',
                               CACHE_DIR='/tmp/cache_dir')
        installer._cfg = {
            'LOCAL_PACKAGE': 'tomcat.tar.gz',
            'LOCAL_PACKAGE_HASH': '1234WXYZ',
            'LOCAL_DOWNLOAD_PREFIX': 'PREFIX',
            'LOCAL_PACKAGE_INSTALL_DIR': '/tmp/packages'
        }
        installer._unzipUtil = Dingus('unzip')
        installer._hashUtil = Dingus('hash',
                                     calculate_hash__returns='1234WXYZ')
        installer._dcm = Dingus('dcm', get__returns=None)
        installer._dwn = Dingus('download')
        # Run test
        instDir = installer.install_binary('LOCAL')
        # Verify execution path, file is not cached
        # Cache manager checks for file
        assert installer._dcm.get.calls().once()
        assert None is installer._dcm.calls('get')[0].return_value
        # download is called once with file path
        assert installer._dwn.download.calls().once()
        assert 'PREFIX/tomcat.tar.gz' == \
            installer._dwn.calls('download')[0].args[0]
        # hash is called with file path
        assert installer._hashUtil.calculate_hash.calls().once()
        calls = installer._hashUtil.calls('calculate_hash')
        assert calls[0].args[0].endswith('tomcat.tar.gz')
        # cache manager is called with key and digest
        assert installer._dcm.put.calls().once()
        assert 'tomcat.tar.gz' == installer._dcm.calls('put')[0].args[0]
        assert '1234WXYZ' == installer._dcm.calls('put')[0].args[2]
        # file is extracted
        assert installer._unzipUtil.extract.calls().once()
        # verify installation directory
        eq_('/tmp/packages/tomcat', instDir)

    def test_install_binary_not_cached(self):
        # Setup mocks
        #  use __new__ to skip constructor, we set that up here
        installer = object.__new__(CloudFoundryInstaller)
        installer._cf = Dingus('cf',
                               BUILD_DIR='/tmp/build_dir',
                               CACHE_DIR='/tmp/cache_dir')
        installer._cfg = {
            'LOCAL_PACKAGE': 'tomcat.tar.gz',
            'LOCAL_PACKAGE_HASH': '1234WXYZ',
            'LOCAL_DOWNLOAD_PREFIX': 'PREFIX',
        }
        installer._unzipUtil = Dingus('unzip')
        installer._hashUtil = Dingus('hash',
                                     calculate_hash__returns='1234WXYZ')
        installer._dcm = Dingus('dcm', get__returns='/tmp/cache/tomcat.tar.gz')
        installer._dwn = Dingus('download')
        # Run test
        instDir = installer.install_binary('LOCAL')
        # Verify execution path, file is not cached
        # Cache manager checks for file
        assert installer._dcm.get.calls().once()
        assert '/tmp/cache/tomcat.tar.gz' == \
            installer._dcm.calls('get')[0].return_value
        # make sure download section is skipped
        assert 0 == len(installer._dwn.calls('download'))
        assert 0 == len(installer._hashUtil.calls('calculate_hash'))
        assert 0 == len(installer._dcm.calls('put'))
        # file is extracted
        assert installer._unzipUtil.extract.calls().once()
        eq_('/tmp/build_dir/tomcat', instDir)


class TestCloudFoundryInstallerConfig(object):
    def setUp(self):
        self._tmpDir = tempfile.mkdtemp()

    def tearDown(self):
        if self._tmpDir:
            shutil.rmtree(self._tmpDir)

    def assertFileExistsAndDelete(self, filePath):
        assert os.path.exists(filePath)
        os.remove(filePath)
        assert not os.path.exists(filePath)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_install_from_build_pack(self):
        # Setup mocks
        #  use __new__ to skip constructor, we set that up here
        installer = object.__new__(CloudFoundryInstaller)
        installer._cf = Dingus(
            'cf',
            BP_DIR='./test/data',
            BUILD_DIR=self._tmpDir)
        # Test copying files from build pack
        tmpConfig = os.path.join(self._tmpDir, 'config.json')
        # test with default toLocation
        installer.install_from_build_pack('config.json')
        self.assertFileExistsAndDelete(tmpConfig)
        # test when toLocation is same as default
        installer.install_from_build_pack('config.json', 'config.json')
        self.assertFileExistsAndDelete(tmpConfig)
        # test when toLocation is different
        installer.install_from_build_pack('config.json', 'renamed.json')
        self.assertFileExistsAndDelete(
            os.path.join(self._tmpDir, 'renamed.json'))
        # test when toLocation is nested path
        installer.install_from_build_pack('config.json',
                                          'in/a/path/renamed.json')
        self.assertFileExistsAndDelete(
            os.path.join(self._tmpDir, 'in/a/path/renamed.json'))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_install_from_app(self):
        # Setup mocks
        #  use __new__ to skip constructor, we set that up here
        installer = object.__new__(CloudFoundryInstaller)
        installer._cf = Dingus(
            'cf',
            BP_DIR='./test/data',
            BUILD_DIR=self._tmpDir)
        # Add file to temp dir
        installer.install_from_build_pack('config.json')
        # Test copying files from app
        installer.install_from_application('config.json', 'renamed.json')
        self.assertFileExistsAndDelete(
            os.path.join(self._tmpDir, 'renamed.json'))
        # Test with nested path
        installer.install_from_application(
            'config.json', 'in/a/path/renamed.json')
        self.assertFileExistsAndDelete(
            os.path.join(self._tmpDir, 'in/a/path/renamed.json'))
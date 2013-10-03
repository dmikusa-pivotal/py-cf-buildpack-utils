import os
import shutil
import tempfile
from nose.tools import with_setup
from build_pack_utils import HashUtil
from build_pack_utils import DirectoryCacheManager


class TestDirectoryCacheManager(object):

    def __init__(self):
        self._hshUtil = HashUtil(
            {'cache-hash-algorithm': 'sha256'})

    def tearDown(self):
        path = os.path.join(tempfile.gettempdir(), 'junk.txt')
        if os.path.exists(path):
            os.remove(path)
        path = os.path.join(tempfile.gettempdir(), 'DCM')
        if os.path.exists(path):
            shutil.rmtree(path)

    def create_junk_file(self, fileName):
        path = os.path.join(tempfile.gettempdir(), fileName)
        with open(path, 'w') as tmp:
            tmp.write("Hello World!")
        return (path, self._hshUtil.calculate_hash(path))

    @with_setup(teardown=tearDown)
    def test_basics(self):
        path = os.path.join(tempfile.gettempdir(), "DCM")
        dcm = DirectoryCacheManager({
            'file-cache-base-directory': path,
            'use-external-hash': False,
            'cache-hash-algorithm': 'sha256'})
        assert not dcm.exists('asdf', None)
        junk_file = self.create_junk_file('junk.txt')
        key = os.path.basename(junk_file[0])
        dcm.put(key, junk_file[0], junk_file[1])
        assert dcm.exists(key, junk_file[1])
        assert dcm.get(key, junk_file[1]).endswith('DCM/junk.txt')
        dcm.delete(key)
        assert not dcm.exists(key, junk_file[1])

from build_pack_utils import HashUtil
from build_pack_utils import ShaHashUtil


class TestHashUtils(object):
    HASH_FILE = './test/data/HASH'

    def hash_file_calc(self, hsh, digest):
        assert digest == hsh.calculate_hash(self.HASH_FILE)

    def hash_file_matches(self, hsh, digest):
        assert hsh.does_hash_match(digest, self.HASH_FILE)

    def hash_file_not_matches(self, hsh, digest):
        assert not hsh.does_hash_match(digest, self.HASH_FILE)

    def hash_file_bad_algorithm(self, hsh, algorithm, msg):
        try:
            hsh.calculate_hash(self.HASH_FILE)
            assert False  # Should not happen
        except ValueError, ex:
            assert msg.startswith(ex.args[0]), \
                "does not start with [%s]" % ex.args[0]

    # Test hashlib
    def test_hash_util_sha1(self):
        self.hash_file_calc(
            HashUtil({'CACHE_HASH_ALGORITHM': 'sha1'}),
            "cf6ef7e713aeff5426e592b8e897fed7590407af")

    def test_hash_util_sha256(self):
        self.hash_file_calc(
            HashUtil({'CACHE_HASH_ALGORITHM': 'sha256'}),
            "7cd9d6e1140dfbefecd88b7552ac6be5bf59885c604da3cf52ededb988e9fff0")

    def test_hash_util_sha512(self):
        self.hash_file_calc(
            HashUtil({'CACHE_HASH_ALGORITHM': 'sha512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_hash_util_matches(self):
        self.hash_file_matches(
            HashUtil({'CACHE_HASH_ALGORITHM': 'sha512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_hash_util_matches_extended_hash(self):
        self.hash_file_matches(
            HashUtil({'CACHE_HASH_ALGORITHM': 'sha512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1 "
            "./test/data/HASH")

    def test_hash_util_not_matches(self):
        self.hash_file_not_matches(
            HashUtil({'CACHE_HASH_ALGORITHM': 'sha512'}),
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_hash_util_no_file(self):
        hsh = HashUtil({'CACHE_HASH_ALGORITHM': '512'})
        assert '' == hsh.calculate_hash(None)
        assert '' == hsh.calculate_hash('')

    def test_hash_util_empty_algorithms(self):
        hsh = HashUtil({'CACHE_HASH_ALGORITHM': ''})
        self.hash_file_bad_algorithm(hsh, '', 'unsupported hash type ')

    def test_hash_util_bad_algorithm(self):
        hsh = HashUtil({'CACHE_HASH_ALGORITHM': '???'})
        self.hash_file_bad_algorithm(hsh, '???', 'unsupported hash type ???')

    def test_hash_util_missing_algorithm(self):
        hsh = HashUtil({'CACHE_HASH_ALGORITHM': '2'})
        self.hash_file_bad_algorithm(hsh, '2', 'unsupported hash type 2')

    # Test External SHA
    def test_sha_hash_util_sha1(self):
        self.hash_file_calc(
            ShaHashUtil({'CACHE_HASH_ALGORITHM': 'sha1'}),
            "cf6ef7e713aeff5426e592b8e897fed7590407af")

    def test_sha_hash_util_sha256(self):
        self.hash_file_calc(
            ShaHashUtil({'CACHE_HASH_ALGORITHM': 'sha256'}),
            "7cd9d6e1140dfbefecd88b7552ac6be5bf59885c604da3cf52ededb988e9fff0")

    def test_sha_hash_util_sha512(self):
        self.hash_file_calc(
            ShaHashUtil({'CACHE_HASH_ALGORITHM': 'sha512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_sha_hash_util_matches(self):
        self.hash_file_matches(
            ShaHashUtil({'CACHE_HASH_ALGORITHM': 'sha512'}),
            "829640ff489bbc9d12267fe5bbae69e0e65f293171a126b22bb760bc259120e53"
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_sha_hash_util_not_matches(self):
        self.hash_file_not_matches(
            ShaHashUtil({'CACHE_HASH_ALGORITHM': 'sha512'}),
            "fbd0e8fa973f782b27b2059b72f46c5080411f018651808a6f716eec08bc1f1")

    def test_sha_hash_util_no_file(self):
        hsh = ShaHashUtil({'CACHE_HASH_ALGORITHM': 'sha512'})
        assert '' == hsh.calculate_hash(None)
        assert '' == hsh.calculate_hash('')

    def test_sha_hash_util_empty_algorithms(self):
        hsh = ShaHashUtil({'CACHE_HASH_ALGORITHM': ''})
        self.hash_file_bad_algorithm(
            hsh, '', 'Value "" invalid for option a (number expected)')

    def test_sha_hash_util_bad_algorithm(self):
        hsh = ShaHashUtil({'CACHE_HASH_ALGORITHM': '???'})
        self.hash_file_bad_algorithm(
            hsh, '???', 'Value "???" invalid for option a (number expected)')

    def test_sha_hash_util_missing_algorithm(self):
        hsh = ShaHashUtil({'CACHE_HASH_ALGORITHM': 'sha2'})
        self.hash_file_bad_algorithm(
            hsh, '2', 'shasum: Unrecognized algorithm')

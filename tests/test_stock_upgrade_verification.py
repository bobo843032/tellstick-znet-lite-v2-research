# -*- coding: utf-8 -*-
"""Exercise the unmodified 1.3.2 upgrade verifier with synthetic input.

Run under the firmware's Python 2.7 runtime with FIRMWARE_ROOTFS set.
The GPG subprocess is replaced; no image is installed or flashed.
"""
import hashlib
import imp
import os
import shutil
import tempfile
import unittest


rootfs = os.environ['FIRMWARE_ROOTFS']
upgrade = imp.load_source(
    'stock_upgrade', os.path.join(rootfs, 'usr/bin/tellstick-upgrade.py'))


class StockUpgradeVerification(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix='upgrade-verifier-')
        self.path = os.path.join(self.directory, 'synthetic-image.bin')
        self.payload = 'synthetic firmware test data'
        with open(self.path, 'wb') as handle:
            handle.write(self.payload)
        with open(self.path + '.asc', 'wb') as handle:
            handle.write('synthetic signature placeholder')
        self.original_call = upgrade.subprocess.call
        self.calls = []

    def tearDown(self):
        upgrade.subprocess.call = self.original_call
        shutil.rmtree(self.directory)

    def gpg_result(self, code):
        def call(argv):
            self.calls.append(argv)
            return code
        upgrade.subprocess.call = call

    def test_size_mismatch_rejected_before_signature(self):
        self.gpg_result(0)
        self.assertFalse(upgrade.UpgradeManagerBase.verifyFile(
            self.path, size=len(self.payload) + 1))
        self.assertEqual(self.calls, [])

    def test_sha1_mismatch_rejected_before_signature(self):
        self.gpg_result(0)
        self.assertFalse(upgrade.UpgradeManagerBase.verifyFile(
            self.path, checksum='0' * 40))
        self.assertEqual(self.calls, [])

    def test_signature_failure_rejected(self):
        self.gpg_result(1)
        self.assertFalse(upgrade.UpgradeManagerBase.verifyFile(
            self.path, size=len(self.payload),
            checksum=hashlib.sha1(self.payload).hexdigest()))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][0:2], ['gpg', '--verify'])
        self.assertIn('/etc/upgrade/telldus.gpg', self.calls[0])
        self.assertEqual(self.calls[0][-1], self.path + '.asc')

    def test_success_requires_signature_success(self):
        self.gpg_result(0)
        self.assertTrue(upgrade.UpgradeManagerBase.verifyFile(
            self.path, size=len(self.payload),
            checksum=hashlib.sha1(self.payload).hexdigest()))
        self.assertEqual(len(self.calls), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)

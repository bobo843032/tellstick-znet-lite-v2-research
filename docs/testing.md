# Offline test record

All results below were recorded on 2026-10-24 against the official TellStick ZNet Lite V2 1.3.2 image. The published prototype and tests were rerun after removal of machine-specific paths and variable names. These are not a claim that CI reproduces the results from a fresh clone. The vendor image, extracted root filesystem, and MIPS emulator are **not distributed** here. No physical gateway was contacted during these tests.

| Test | Code exercised | Recorded result | Limit |
| --- | --- | --- | --- |
| Firmware imports | Original MIPS Python 2.7, CherryPy 3.7, API and OpenID provider via QEMU user-mode emulation | PASS | Not a full-system emulator |
| Public discovery TLS | Firmware Python/Requests/OpenSSL stack, certificate-verified HTTPS GET | PASS | Not a complete account login |
| CherryPy TLS | Original CherryPy serving a temporary loopback certificate | PASS | No real address certificate |
| Local-owner integration | [`test_firmware_integration.py`](../tests/test_firmware_integration.py), original API/JWT modules with synthetic settings and devices | 8/8 PASS | No serial or radio hardware |
| End-to-end HTTPS | [`run_local_https_probe.sh`](../tests/run_local_https_probe.sh), actual CherryPy routing, local login, approval, JWT, API read and mocked device operation, logout | PASS | Loopback only; synthetic account and devices |
| Z-Wave command paths | [`test_zwave_offline.py`](../tests/test_zwave_offline.py), original node/controller bytecode with fake serial/message sink | 2/2 PASS | No Z-Wave network or transmission |
| Local UI | JavaScript syntax check and authenticated serving over loopback HTTPS | PASS | No visual mobile-browser test |

In the integration test, owner login, rate limiting, CSRF rejection, session timeout/logout, valid and invalid JWTs, expired tokens, renewal, and the stock system/device/sensor routes were exercised. The provider kept the original Telldus Live class importable. The end-to-end probe used only short-lived synthetic credentials and a temporary certificate, then stopped its server and deleted test files.

The protocol/parser study from the preceding phase also recorded five passing isolated model tests. That model intentionally applies stricter input validation than the original firmware and is **not** evidence that the firmware rejects identical malformed datagrams. Its packet-level test helper is withheld from this public repository because the same interface can issue unauthenticated radio operations on reachable devices. The result is documented here without distributing a ready-made sender.

The scripts under [`tests/`](../tests/) require a separately obtained official firmware root filesystem and a compatible user-mode MIPS Python runner. They are research harnesses, not safe device installers. A pass means code executed under the stated mock boundary; it does not mean a physical actuator changed state. In particular, a successful `device/turnOn` API response was recorded against a fake device. The Z-Wave test observed queued messages, not radio acknowledgement.

From the repository root, with firmware and emulator paths outside the checkout:

```sh
export FIRMWARE_ROOTFS=/path/to/extracted-1.3.2-rootfs
export QEMU_MIPS=/path/to/qemu-mips

"$QEMU_MIPS" -L "$FIRMWARE_ROOTFS" \
  -E PYTHONHOME="$FIRMWARE_ROOTFS/usr" \
  -E PYTHONPATH="$PWD/prototype" \
  "$FIRMWARE_ROOTFS/usr/bin/python2.7" tests/test_firmware_integration.py
"$QEMU_MIPS" -L "$FIRMWARE_ROOTFS" \
  -E PYTHONHOME="$FIRMWARE_ROOTFS/usr" \
  "$FIRMWARE_ROOTFS/usr/bin/python2.7" tests/test_zwave_offline.py
sh tests/run_tls_probe.sh
sh tests/run_local_https_probe.sh
```

The two shell probes bind only to `127.0.0.1`, create temporary synthetic TLS material and credentials, and remove them on exit. Do not run them where the test ports are assigned to another service.

Before anyone repeats the tests, supply their own legally obtained firmware image and keep it outside the repository. See the [firmware documentation](firmware.md) for version identification and [references](references.md) for the vendor source. The software intentionally does not bundle firmware, extracted files, device-specific material, or credentials.

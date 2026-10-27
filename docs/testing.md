# Test record

## Physical follow-up on firmware 1.3.2

Targeted tests on an owned gateway subsequently verified the stock UDP discovery response, UDP 42314 registration/version response, CherryPy HTTP service and anonymous API rejection. A separately built Python 2.7 MQTT plugin was accepted through the installed plugin loader with a detached egg signature and ran its `telldus.startup` entry point on normal daemon starts. A subscriber received the controlled-import test message from the broker; later daemon starts logged successful publish calls without an independent subscriber receipt for each restart. The working plugin remains installed. These results do not verify RF/Z-Wave delivery or the local-owner prototype.

The installed loader also accepted an empty `packages` list and reported success without package signature checks. A controlled plugin-name probe confirmed that the manifest name can move the installation path outside the intended plugin directory and that replacing an existing target removes its contents. Only a uniquely named, test-owned directory was affected and then removed. The manifest is parsed before package verification. These are **RUNTIME VERIFIED** findings about the local loader; authenticated web upload and access control are separate and have not been tested end to end. The plugin keyring backup file is GPG's previous public keyring, not an additional active trust store. No keys, credentials, device identifiers or executable probe payloads are distributed here.

The firmware's device/sensor and RF433 signal hooks are **STATIC CODE VERIFIED**. A temporary sensor-only observer loaded in the normal daemon. It received no natural callback during more than five minutes of observation; the saved configuration had a sensor entry but no new values, and the physical sensor was unavailable. A separate, clearly marked one-shot trigger then called the original `DeviceManager.sensorValueUpdated` method with synthetic arguments in the production daemon. The observer received that queued callback: synthetic daemon dispatch is **RUNTIME VERIFIED**, while natural sensor delivery and sensor-to-MQTT delivery are **NOT YET VERIFIED**. Both temporary plugins were removed; the MQTT test plugin was left unchanged. See the [verification matrix](../HARDWARE_VERIFICATION.md) for the exact boundary.

## Earlier offline tests

The results below were recorded on 2026-10-24 and 2026-10-25 against the official TellStick ZNet Lite V2 1.3.2 image. The published prototype and tests were rerun after removal of machine-specific paths and variable names. These are not a claim that CI reproduces the results from a fresh clone. The vendor image, extracted root filesystem, and MIPS emulator are **not distributed** here. No physical gateway was contacted during these tests.

| Test | Code exercised | Recorded result | Limit |
| --- | --- | --- | --- |
| Firmware imports | Original MIPS Python 2.7, CherryPy 3.7, API and OpenID provider via QEMU user-mode emulation | PASS | Not a full-system emulator |
| Public discovery TLS | Firmware Python/Requests/OpenSSL stack, certificate-verified HTTPS GET | PASS | Not a complete account login |
| CherryPy TLS | Original CherryPy serving a temporary loopback certificate | PASS | No real address certificate |
| Local-owner integration | [`test_firmware_integration.py`](../tests/test_firmware_integration.py), original API/JWT modules with synthetic settings and devices | 9/9 PASS, including the original 8 tests and token-approval URL regression | No serial or radio hardware |
| End-to-end HTTPS | [`run_local_https_probe.sh`](../tests/run_local_https_probe.sh), actual CherryPy routing, local login, approval, JWT, API read and mocked device operation, logout | PASS | Loopback only; synthetic account and devices |
| Local-only web provider configuration | Same HTTPS probe with `LOCALOWNER_LOCAL_ONLY=1`; no Live web-authentication provider registered | PASS: local flow and stock approval POST rejected by web authorization | Live backend and physical application startup not exercised |
| Z-Wave command paths | [`test_zwave_offline.py`](../tests/test_zwave_offline.py), original node/controller bytecode with fake serial/message sink | 2/2 PASS | No Z-Wave network or transmission |
| Local UI | JavaScript syntax check and authenticated serving over loopback HTTPS | PASS | No visual mobile-browser test |
| Stock `system/info` authorization | [`test_original_system_info_http.py`](../tests/test_original_system_info_http.py), original CherryPy/API modules over loopback HTTP | 6/6 PASS: missing, empty, wrong-format, invalid, expired, valid JWT | Valid case uses synthetic board values; no physical gateway |
| Vendor upgrade verifier | [`test_stock_upgrade_verification.py`](../tests/test_stock_upgrade_verification.py), original `tellstick-upgrade.py:verifyFile` | 4/4 PASS: size, SHA-1, GPG rejection, and simulated GPG success | GPG subprocess is mocked; no vendor signature or flash tested |
| UDP 42314 original-module parser/listener | [`test_udp42314_original_offline.py`](../tests/test_udp42314_original_offline.py) | 7/7 PASS: parser, malformed input, listener replacement, unknown/incomplete messages, event forwarding, Z-Wave version notice | Fake sockets; no serial/radio hardware |
| UDP 42314 private queue and loopback checks | Original `CommandHandler`, `Protocol`, `RF433Msg`, `Adapter.queue`, and `SocketServer.UDPServer` | 9/9 PASS, including a real encoder to mock queue and server continuation after a malformed datagram | Test harness retained privately to avoid publishing an operational radio-command example; loopback only |

In the integration test, owner login, rate limiting, CSRF rejection, session timeout/logout, valid and invalid JWTs, expired tokens, renewal, and the stock system/device/sensor routes were exercised. The additional test checked the HTTPS approval URL, login return path, and unchanged stock response on HTTP. The provider kept the original Telldus Live class importable. The end-to-end probe exercised the approval URL and unauthenticated browser return path with short-lived synthetic credentials and a temporary certificate, then stopped its server and deleted test files.

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
"$QEMU_MIPS" -L "$FIRMWARE_ROOTFS" \
  -E PYTHONHOME="$FIRMWARE_ROOTFS/usr" \
  "$FIRMWARE_ROOTFS/usr/bin/python2.7" tests/test_original_system_info_http.py
"$QEMU_MIPS" -L "$FIRMWARE_ROOTFS" \
  -E PYTHONHOME="$FIRMWARE_ROOTFS/usr" \
  -E FIRMWARE_ROOTFS="$FIRMWARE_ROOTFS" \
  "$FIRMWARE_ROOTFS/usr/bin/python2.7" tests/test_stock_upgrade_verification.py
"$QEMU_MIPS" -L "$FIRMWARE_ROOTFS" \
  -E PYTHONHOME="$FIRMWARE_ROOTFS/usr" \
  "$FIRMWARE_ROOTFS/usr/bin/python2.7" tests/test_udp42314_original_offline.py
sh tests/run_tls_probe.sh
sh tests/run_local_https_probe.sh
LOCALOWNER_LOCAL_ONLY=1 sh tests/run_local_https_probe.sh
```

The two shell probes bind only to `127.0.0.1`, create temporary synthetic TLS material and credentials, and remove them on exit. Do not run them where the test ports are assigned to another service.

Before anyone repeats the tests, supply their own legally obtained firmware image and keep it outside the repository. See the [firmware documentation](firmware.md) for version identification and [references](references.md) for the vendor source. The software intentionally does not bundle firmware, extracted files, device-specific material, or credentials.

# TellStick ZNet Lite V2: physical hardware verification

This report covers an owned gateway running firmware 1.3.2. It separates behavior observed on that gateway from firmware code, emulation, and open hypotheses. Device addresses, hardware identifiers, credentials, MQTT broker details, raw logs, and locally generated signing material are deliberately omitted. The private working record and backups remain outside this repository.

## Evidence labels

- **RUNTIME VERIFIED:** Observed on the physical gateway. A synthetic event is always identified as synthetic.
- **STATIC CODE VERIFIED:** Established from the extracted 1.3.2 firmware, without the corresponding live behavior.
- **VERIFIED IN EMULATION ONLY:** Original code executed with an emulator or substituted hardware.
- **NOT YET VERIFIED:** The required physical behavior has not been observed.
- **HYPOTHESIS:** A proposed behavior or design that still needs a discriminating test.

## Verification matrix

| Finding | Earlier evidence | Physical observation and limit | Status |
| --- | --- | --- | --- |
| Gateway identity and firmware 1.3.2 | Official image and earlier hardware study | Discovery response, build date, board identity, and selected installed files agreed with 1.3.2. The current full flash was not rehashed. | **RUNTIME VERIFIED** for the selected identity checks |
| UDP 30303 discovery | `productiontest.Server.AutoDiscoveryHandler` | Targeted discovery received a response from the owned gateway. Sensitive response fields were not retained in public material. | **RUNTIME VERIFIED** for local response |
| UDP 42314 registration | `productiontest.Server.CommandHandler` and emulation tests | A targeted registration received a Z-Wave version notice; the listener survived one incomplete message. No RF command or received event was proven. | **RUNTIME VERIFIED** for listener, registration, and version notice; RF delivery **NOT YET VERIFIED** |
| Stock HTTP and API boundary | CherryPy/API bytecode and emulation | Port 80 served CherryPy 3.7.0; anonymous API requests returned 401; stock login began with local redirects. Authenticated API operation was not exercised. | **RUNTIME VERIFIED** for service and anonymous boundary |
| Session cookie | CherryPy configuration | Anonymous responses set `session_id` with `HttpOnly`, without `Secure` or `SameSite`. RAM session storage follows from the active firmware configuration, not a memory inspection. | Cookie attributes **RUNTIME VERIFIED**; storage **STATIC CODE VERIFIED** |
| SSH access | Dropbear firmware configuration | The owned gateway accepted an authorized root SSH login; the daemon ran on port 22. No firmware support key was used to log in. | **RUNTIME VERIFIED** |
| RF433 host interface and decoding | Firmware and earlier hardware inspection | The application held the RF433 USB serial interface and logged its controller version. One Fineoffset temperature/humidity sensor entry remained in saved configuration. A compatible physical sensor was unavailable, so physical RF-origin sensor input was outside the scope of the callback test. No RF transmit/receive delivery was proven. | Host/controller startup **RUNTIME VERIFIED**; RF-origin sensor input was outside test scope |
| Z-Wave host interface and node behavior | Firmware and earlier hardware inspection | The application held the separate Z-Wave USB serial interface; UDP registration returned a Z-Wave version notice. No node inclusion, command response, or physical network transition was tested. | Host interface/version notice **RUNTIME VERIFIED**; Z-Wave radio behavior **NOT YET VERIFIED** |
| Local-owner authentication prototype | Original modules and synthetic accounts/devices | Its login/JWT/API flow was tested under MIPS emulation. It was not installed on the physical gateway. | **VERIFIED IN EMULATION ONLY** |
| Signed plugin startup | Loader code and a separately built Python 2.7 MQTT egg | The installed loader accepted the detached egg signature. `telldus.startup` ran during normal daemon starts, including after controlled restarts. | **RUNTIME VERIFIED** |
| MQTT publication | One-shot startup publisher | A subscriber received the test topic/payload during controlled import. Later normal daemon starts logged successful publish calls; those later publishes had no independent subscriber receipt recorded. | Import-to-broker receipt and permanent startup **RUNTIME VERIFIED** within those separate evidence limits |
| Empty `packages` list | `Loader.importPlugin` code | The real loader in the real plugin directory accepted `packages: []`, completed installation/loading, and returned success. With no package to iterate, no detached package signature was checked. | **RUNTIME VERIFIED** |
| Plugin-name filesystem path | `Loader.importPlugin` path construction | A controlled, uniquely named test target outside the plugin directory was created through the manifest name. Replacing that test-owned target removed its prior sentinel. The target and staging archive were then deleted. No existing user data was tested. | **RUNTIME VERIFIED** for the local loader path and replacement behavior |
| Active plugin keyring and `~` file | GPG wrapper and pre-change backups | The loader used `plugins.keyring`. A temporary GPG reproduction showed that `plugins.keyring~` is the previous public keyring generated during a later key import; it is not a second active trust store. Neither file was changed during this verification. | **RUNTIME VERIFIED** |
| `sensorValueUpdated` callback path | Firmware `DeviceManager` and an installed temporary observer | A separate one-shot trigger called the real `DeviceManager.sensorValueUpdated` with controlled simulated sensor input. The observer received the queued callback in the production daemon. It emitted no RF signal and created no persistent sensor reading. | **RUNTIME VERIFIED** for callback dispatch with controlled simulated input |
| Physical RF-origin sensor input | Fineoffset sensor entry in saved configuration | A compatible physical sensor was unavailable during the test; no RF-origin sensor input was generated or evaluated. | Outside the scope of this test |
| Sensor-to-MQTT chain | Proposed MQTT v2 | No sensor-event publisher was implemented and no sensor-to-MQTT broker subscriber test was run. | **NOT YET IMPLEMENTED OR TESTED** |

## Plugin and MQTT evidence boundary

The one-shot MQTT plugin remains installed and unchanged. Its configuration is root-readable only and is outside this repository. On normal daemon starts, the installed egg passed GPG verification, the `telldus.startup` class was instantiated, and its logger reported a successful publish to `tellstick/status`. A separate subscriber received `hello-from-tellstick` during the controlled import run. The daemon log is evidence of the later call path; it is not an MQTT delivery acknowledgment for each later restart.

The loader parses `manifest.yml` before iterating over package signatures. Package files are verified through detached `.asc` signatures against the active public keyring. An empty package list skips that loop and still produces a loaded manifest-only plugin. This establishes a local importer behavior, not an anonymous HTTP upload path. Anonymous requests to the plugin routes redirected to login; an authenticated web upload has not been replayed end to end.

The plugin-name test exercised the installed loader with a controlled target belonging only to this experiment. It verified that the name influences the filesystem destination and that replacement can remove the existing destination. The public record intentionally omits an operational payload and private test paths. The target, staging archive, and later temporary observer plugins were removed. The original MQTT plugin and both keyring files matched their pre-probe file hashes afterward.

## Sensor callback and MQTT v2 gate

The exact slot signature is `sensorValueUpdated(self, device, valueType, value, scale)`. In firmware, `Device.setSensorValues` calls `DeviceManager.sensorValuesUpdated`, which emits the individual signal. `SignalManager` queues registered `@slot('sensorValueUpdated')` callbacks on the application main loop.

| Hook | Registration and arguments | Current status |
| --- | --- | --- |
| `telldus.DeviceManager.sensorValueUpdated(self, device, valueType, value, scale)` | `@signal` source; plugin receives it through `implements(ISignalObserver)` and `@slot('sensorValueUpdated')`. Values come from `Device.setSensorValues` through `sensorValuesUpdated`. | Callback dispatch with controlled simulated input in the production daemon **RUNTIME VERIFIED**; physical RF-origin input was outside test scope because no compatible sensor was available |
| `telldus.DeviceManager.__deviceStateChanged(self, device, state, stateValue, origin)` | `@signal('deviceStateChanged')`; a plugin slot has the same four event arguments after `self`. `Device.setState` enters this path through `stateUpdated`. | **STATIC CODE VERIFIED**; no natural state callback observed |
| `rf433.RF433.decode(self, msg)` | `@signal('rf433RawData')`; plugin slot signature is `(self, data)`. `productiontest.Server.rf433RawData` is an existing consumer that forwards decoded data to the registered UDP listener. | **STATIC CODE VERIFIED**; no RF callback observed in this test |
| `zwave.telldus.TelldusZWave` observer methods | `IZWObserver.zwaveReady(self)`, `nodeAdded(self, device, node)`, and `interviewDone(self, device, cmdClass, data)` are registered through `ObserverCollection`, not `@slot`. `productiontest.Server` is an existing observer. | **STATIC CODE VERIFIED**; no physical node/interview callback observed |

The `@signal` decorator runs its source method first, then queues matching `@slot` callbacks for the main application loop. `IZWObserver` calls are direct observer calls in the emitting flow. These execution models should remain separate in an event publisher.

The synthetic daemon test observed a numeric `valueType` of `1`, `value` of `21.5` (Python `float`), and `scale` of `0`; the observer logged UTC time and an ephemeral device pseudonym. The source object identified itself as simulated. These values describe the test input and do not establish the payload of a real Fineoffset sensor report. The temporary observer and trigger were removed, and the daemon was restarted with only the working MQTT plugin.

**Next useful test:** when a compatible physical sensor is available, capture its RF-origin input through the verified callback path, then implement one MQTT sensor topic and verify receipt with an independent broker subscriber. `deviceStateChanged`, `rf433RawData`, and Z-Wave event forwarding remain outside this sensor-only work.

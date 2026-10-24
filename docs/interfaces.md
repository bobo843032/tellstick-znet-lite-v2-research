# Local interfaces in firmware 1.3.2

The stock application starts a CherryPy web server alongside two UDP services. The descriptions below come from the official 1.3.2 firmware image, rather than network tests against a gateway. See [firmware](firmware.md) for the platform and startup context and [RF433](rf433.md) for the radio controller.

| Interface | Role | Evidence | Operational status |
| --- | --- | --- | --- |
| UDP 30303 | Discovery response | `productiontest.Server.AutoDiscoveryHandler` and application startup registration | STATICALLY VERIFIED; reachability NOT YET VERIFIED |
| UDP 42314 | RF433 event listener and command path | `productiontest.Server.CommandHandler`, `tellduslive.base.LiveMessage`, `rf433.Adapter` | STATICALLY VERIFIED; radio behavior NOT YET VERIFIED |
| Local HTTP | Web UI and token-protected API | `web.base.Server`, `api.ApiManager`, `telldus.DeviceApiManager`, `lua.Lua` | EXECUTED IN EMULATION with synthetic devices |

The discovery response includes device-specific sensitive material. We do not publish its extraction procedure, value, or a probe client. Firmware firewall rules appear to allow both UDP services on the Ethernet-facing OpenWrt zone; that is a configuration finding, **not** evidence of internet reachability. Check actual exposure before using a gateway on an untrusted network.

The other UDP service uses Telldus LiveMessage framing. It keeps one event-listener address in process memory; a later registration replaces the earlier listener. Its RF433 command path reaches the adapter queue, but there is no application-level acknowledgement to the UDP client that a transmission succeeded. The firmware handler does not show a separate sender-authentication step. We omit packet construction and radio-command recipes here. In an isolated model, parser and listener replacement tests passed; no datagram was sent to a physical gateway. A single-listener design also matters when combining independent local integrations.

## Token-protected HTTP API

`api.ApiManager` dispatches the 18 device, sensor, system, and Lua application calls declared by `@apicall` in the examined image. The bearer token is validated before dispatch. The calls divide into:

- Read operations: `devices/list`, `device/info`, `sensors/list`, `sensor/info`, and `system/info`.
- Device operations: `device/bell`, `command`, `dim`, `down`, `learn`, `rgb`, `setName`, `stop`, `turnOff`, `turnOn`, and `up`.
- Other operations: `sensor/setName` and `lua/call`. The latter calls an existing named Lua function; it is not evidence of a code-upload endpoint.

These are application handlers, not 18 separately verified hardware capabilities. Under MIPS emulation, the original dispatcher and JWT implementation handled synthetic system, device, and sensor data, including a mocked `device/turnOn` call. Neither that response nor an adapter-queue operation proves RF433 or Z-Wave delivery. The stock image starts its web service over HTTP; [authentication](authentication.md) explains the token and transport limits.

## Z-Wave boundary

`zwave.telldus.TelldusZWave` initializes a local controller and attaches nodes to the device manager. Generic device operations can reach Z-Wave node command code. Controller administration, including inclusion and exclusion, has internal methods and Telldus Live handlers, but is not exposed through the 18 examined local HTTP calls. The [Z-Wave hardware research](zwave.md) and [local code-path matrix](zwave-local.md) provide the evidence boundary; [no-cloud status](no-cloud.md) separates mocked command-queue tests from physical operation.

**Evidence key:** STATICALLY VERIFIED means present in examined firmware code; EXECUTED IN EMULATION means original firmware modules ran under MIPS user-mode emulation; TESTED WITH MOCKED HARDWARE means radio or device-facing dependencies were substituted; VERIFIED ON PHYSICAL HARDWARE applies only where an existing document explicitly records such a test; NOT YET VERIFIED means no corresponding test was performed.

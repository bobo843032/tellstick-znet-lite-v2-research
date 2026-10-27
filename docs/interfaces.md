# Local interfaces in firmware 1.3.2

The stock application starts a CherryPy web server alongside two UDP services. The firmware descriptions have since been checked with targeted requests to an owned 1.3.2 gateway. See [firmware](firmware.md) for the platform and startup context and [RF433](rf433.md) for the radio controller.

| Interface | Role | Evidence | Operational status |
| --- | --- | --- | --- |
| UDP 30303 | Discovery response | `productiontest.Server.AutoDiscoveryHandler`; targeted physical response | RUNTIME VERIFIED for discovery response; broader exposure not assessed |
| UDP 42314 | RF433 event listener and command path | `productiontest.Server.CommandHandler`; listener and registration response on physical gateway | RUNTIME VERIFIED for listener, registration and Z-Wave version notice; RF transmission and event delivery NOT YET VERIFIED |
| Local HTTP | Web UI and token-protected API | `web.base.Server`, `api.ApiManager`, `telldus.DeviceApiManager`, `lua.Lua`; targeted physical HTTP requests | RUNTIME VERIFIED for CherryPy/3.7.0, login redirects and anonymous API rejection; authenticated operations remain untested |
| RF433 sensor callback | `Device.setSensorValues` → `DeviceManager.sensorValueUpdated` | The callback path is **RUNTIME VERIFIED** in the production daemon using controlled simulated sensor input. A compatible physical sensor was not available, so physical RF-origin input was outside the scope of this test. | Callback dispatch **RUNTIME VERIFIED**; sensor-to-MQTT not yet implemented or tested |
| Z-Wave node callbacks | `zwave.telldus.TelldusZWave` and `IZWObserver` | Controller serial interface and UDP version notice were observed; no node transition was tested. | Host/controller presence RUNTIME VERIFIED; node callbacks STATIC CODE VERIFIED and physically NOT YET VERIFIED |

The discovery response includes device-specific sensitive material. We do not publish its extraction procedure, value, or a probe client. Firmware firewall rules appear to allow both UDP services on the Ethernet-facing OpenWrt zone; that is a configuration finding, **not** evidence of internet reachability. Check actual exposure before using a gateway on an untrusted network.

The other UDP service uses Telldus LiveMessage framing. It keeps one event-listener address in process memory; a later registration replaces the earlier listener. Its RF433 command path reaches the adapter queue, but there is no application-level acknowledgement to the UDP client that a transmission succeeded. The firmware handler does not show a separate sender-authentication step. Original modules passed [isolated parser, listener, and mock-queue tests](udp-42314.md). A targeted physical registration received a Z-Wave version notice; no RF command or event was verified on the gateway. Packet construction and radio-command recipes are omitted here. A single-listener design also matters when combining independent local integrations.

## Token-protected HTTP API

`api.ApiManager` dispatches the 18 device, sensor, system, and Lua application calls declared by `@apicall` in the examined image. The bearer token is validated before dispatch. The calls divide into:

- Read operations: `devices/list`, `device/info`, `sensors/list`, `sensor/info`, and `system/info`.
- Device operations: `device/bell`, `command`, `dim`, `down`, `learn`, `rgb`, `setName`, `stop`, `turnOff`, `turnOn`, and `up`.
- Other operations: `sensor/setName` and `lua/call`. The latter calls an existing named Lua function; it is not evidence of a code-upload endpoint.

These are application handlers, not 18 separately verified hardware capabilities. Under MIPS emulation, the original dispatcher and JWT implementation handled synthetic system, device, and sensor data, including a mocked `device/turnOn` call. Neither that response nor an adapter-queue operation proves RF433 or Z-Wave delivery. The stock image starts its web service over HTTP; [authentication](authentication.md) explains the token and transport limits.

## Z-Wave boundary

`zwave.telldus.TelldusZWave` initializes a local controller and attaches nodes to the device manager. Generic device operations can reach Z-Wave node command code. Controller administration, including inclusion and exclusion, has internal methods and Telldus Live handlers, but is not exposed through the 18 examined local HTTP calls. The [Z-Wave hardware research](zwave.md) and [local code-path matrix](zwave-local.md) provide the evidence boundary; [no-cloud status](no-cloud.md) separates mocked command-queue tests from physical operation.

**Evidence key:** STATIC CODE VERIFIED means present in examined firmware code; VERIFIED IN EMULATION ONLY means original firmware modules ran with emulated or mocked dependencies; RUNTIME VERIFIED means observed on the owned physical gateway (with synthetic events identified explicitly); NOT YET VERIFIED means the required physical behavior has not been observed; HYPOTHESIS means a proposed behavior still needs a discriminating test.

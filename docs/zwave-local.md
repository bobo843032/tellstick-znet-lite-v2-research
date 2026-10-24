# Z-Wave paths in stock firmware 1.3.2

This document concerns the application code in the official 1.3.2 image. The existing [hardware study](zwave.md) covers the controller and serial interface. None of the new no-cloud Z-Wave behavior below has been verified on a physical radio network.

## Controller and devices

**STATICALLY VERIFIED:** `zwave.telldus.TelldusZWave` creates a local controller, registers command classes, restores application settings, and exposes discovered nodes through the device manager. The controller queries version, capabilities, and node information from its serial interface. The firmware also has local code for handling a network key. This does not establish that a backed-up settings file alone is sufficient to restore a network: controller nonvolatile state may be separate.

The generic HTTP device API reaches `DeviceNode` for known nodes. That class maps high-level operations to supported Z-Wave command classes. **EXECUTED IN EMULATION / TESTED WITH MOCKED HARDWARE:** original `DeviceNode` bytecode queued messages for on, off, and up against a fake node. A mocked HTTP on operation returned successfully through the original API. Neither test reached a serial controller or verified a node response. Decompiled indentation suggested a narrower path than the bytecode actually executed; the executed result takes precedence.

## Administration gap

The firmware has internal controller methods for inclusion, exclusion, and other administration. Selected operations are wired through Telldus Live handlers, while the 18 examined local HTTP API calls do not expose a complete local administrative surface. **TESTED WITH MOCKED HARDWARE:** original controller code queued inclusion and exclusion requests to a fake message sink. The callback path and actual network transitions were not tested.

| Capability | Evidence in code | Offline execution | Physical test | Existing local HTTP support |
| --- | --- | --- | --- | --- |
| Controller startup and node discovery | STATICALLY VERIFIED | Imports only | NOT YET VERIFIED | Partial device listing |
| Generic node on/off/up | STATICALLY VERIFIED | TESTED WITH MOCKED HARDWARE | NOT YET VERIFIED | Generic device operations |
| Inclusion and exclusion | STATICALLY VERIFIED | Queue only, mocked | NOT YET VERIFIED | No reviewed local admin route |
| Association management | STATICALLY VERIFIED in internal components | NOT YET VERIFIED | NOT YET VERIFIED | No reviewed local admin route |
| Existing network preservation | Settings and controller paths identified | NOT YET VERIFIED | NOT YET VERIFIED | Not applicable |
| Full cloud-free management | Components exist | NOT YET VERIFIED | NOT YET VERIFIED | Missing reviewed admin/event surface |

A future adapter should begin with read-only inventory and existing generic device routes. Any new administrative route needs narrow authorization, state/event handling, preservation of existing controller data, and a recovery plan. Controller reset or raw command-class access should not be part of a first owner UI.

A Manufacturer Specific code path references device-specific sensitive material. Its reachability and security properties have **not** been established by a radio test, and details that would assist extraction are intentionally withheld. It is unrelated to the proposed owner login and is not needed for a Home Assistant integration.

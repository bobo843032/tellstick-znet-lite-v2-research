# TellStick ZNet Lite V2 research

Independent research into the hardware and stock firmware of the TellStick ZNet Lite V2, with a focus on local operation when Telldus Live is unavailable. The examined firmware is version 1.3.2. This repository contains original documentation, an experimental local-authentication plugin, offline tests, and sanitized results from targeted tests on an owned gateway. The one-shot MQTT test plugin and private test artifacts are not distributed here.

## What is established

- The examined unit has an AR933x/MIPS host running OpenWrt with a SquashFS root and writable overlay. UART, bootloader access, and the integrated Wi-Fi interface were verified on physical hardware in the earlier research. See [hardware](docs/hardware.md), [firmware](docs/firmware.md), and [Wi-Fi](docs/undocumented-wifi.md).
- Stock firmware 1.3.2 contains local discovery, an RF433 event/control interface, and a CherryPy HTTP API. UDP 42314 has one replaceable event listener and no handler-level authentication or command acknowledgement; UDP 30303 exposes sensitive discovery information. The HTTP API has device and sensor routes and uses signed tokens. See [local interfaces](docs/interfaces.md) and the [42314 analysis](docs/udp-42314.md).
- Approval of a new API token in stock firmware depends on a Telldus Live OpenID login. Existing token validation and several device routes run locally in firmware code. That distinction matters: a local API is not, by itself, a cloud-free onboarding path. See [authentication](docs/authentication.md).
- An independently written Python 2.7 plugin can use the firmware's existing API and JWT machinery. Its login, token approval, and selected API routes were exercised under MIPS user-mode emulation with synthetic settings and mocked devices. See [prototype](prototype/README.md) and [test record](docs/testing.md).
- A separate signed Python 2.7 MQTT test plugin loaded from `telldus.startup` during normal daemon starts and published a message to a local broker. The installed loader also accepted a manifest-only plugin with `packages: []`. See the [physical verification matrix](HARDWARE_VERIFICATION.md) and [security review](SECURITY_STATIC_REVIEW.md) for exact evidence limits.
- Stock Z-Wave components include local controller and command paths, but full local administration and radio behavior remain unverified. RF433 has a separate local command path. See [RF433](docs/rf433.md), [Z-Wave local paths](docs/zwave-local.md), and [no-cloud status](docs/no-cloud.md).

## Validation

Hardware inspection, UART, and Wi-Fi were verified on the examined unit. Later targeted tests verified discovery, UDP registration, the stock HTTP anonymous boundary, and permanent startup of a signed MQTT test plugin. A subscriber received the controlled-import publication; later normal daemon starts logged successful publish calls without separate subscriber receipts. The `sensorValueUpdated` callback path is **RUNTIME VERIFIED** in the production daemon using controlled simulated sensor input. A compatible physical sensor was not available, so physical RF-origin input was outside the scope of this test. Sensor-to-MQTT forwarding is not yet implemented or tested. RF433/Z-Wave radio delivery and the local-owner prototype remain unverified on the gateway. Earlier API/JWT and local-owner tests passed under MIPS emulation with synthetic data; Z-Wave command tests used mocked hardware. See the [test record](docs/testing.md) and [physical verification matrix](HARDWARE_VERIFICATION.md).

## Local architecture

```text
Local client -> stock HTTP API -> device and sensor managers -> RF433 / Z-Wave adapters
                  ^
                  | signed API token
                  |
Telldus Live OpenID -> stock token approval
                  |
                  +-- experimental local owner provider (offline prototype only)
```

The prototype retains the stock token format and API dispatcher. It adds an owner login and an approval page and, on HTTPS token requests, directs the stock approval link to that local page. A separate server draft uses CherryPy's existing TLS support. Deployment requirements and unresolved integration work are detailed in [no-cloud status](docs/no-cloud.md).

## Read next

- [Hardware and UART](docs/hardware.md) · [bootloader](docs/uart-and-uboot.md) · [firmware](docs/firmware.md) · [updates and recovery](docs/update-and-recovery.md)
- [Local interfaces and API](docs/interfaces.md) · [UDP 42314](docs/udp-42314.md) · [authentication and TLS](docs/authentication.md)
- [RF433](docs/rf433.md) · [Z-Wave hardware](docs/zwave.md) · [Z-Wave local paths](docs/zwave-local.md)
- [No-cloud design and remaining work](docs/no-cloud.md) · [offline tests](docs/testing.md) · [hardware readiness](docs/hardware-readiness.md)
- [Physical verification matrix](HARDWARE_VERIFICATION.md) · [security review](SECURITY_STATIC_REVIEW.md)
- [References and attribution](docs/references.md) · [security policy](SECURITY.md)

The [prototype README](prototype/README.md) describes the original code. The [test instructions](docs/testing.md) explain the separately obtained firmware required to reproduce the offline results.

## Acknowledgements

The hardware and firmware investigation began before [issue #1](https://github.com/bobo843032/tellstick-znet-lite-v2-research/issues/1). Thanks to ob-wn for identifying the unauthenticated UDP 30303 interface there; that lead prompted closer examination of the relevant firmware components. The [ob-wn no-cloud project](https://github.com/ob-wn/tellstick-znet-lite-v2-nocloud) provides a separate approach to local access. [R00S's local TellStick add-on](https://github.com/R00S/addon-tellstick-local) demonstrates a Home Assistant path for supported local RF433 functions. Their code has not been copied into this prototype; see [references](docs/references.md) for scope and licenses.

## License and scope

Original documentation is [CC BY 4.0](LICENSE). Original code under `prototype/` and `tests/` is [MIT licensed](LICENSE-CODE). Neither license covers Telldus firmware, third-party projects, private credentials, or device-specific data. This is independent research and is not affiliated with Telldus.

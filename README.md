# TellStick ZNet Lite V2 research

Independent research into the hardware and stock firmware of the TellStick ZNet Lite V2, with a focus on local operation when Telldus Live is unavailable. The examined firmware is version 1.3.2. This repository contains original documentation, a small experimental local-authentication plugin, and offline tests. It does not contain vendor firmware or a device-ready no-cloud patch.

The work began with hardware, UART, bootloader, Wi-Fi, and firmware inspection. A later [report from ob-wn](https://github.com/bobo843032/tellstick-znet-lite-v2-research/issues/1) drew attention to UDP 30303 and led to a more focused analysis of the firmware's local interfaces. That report did not initiate the wider project.

## What is established

- The examined unit has an AR933x/MIPS host running OpenWrt with a SquashFS root and writable overlay. UART, bootloader access, and the integrated Wi-Fi interface were verified on physical hardware in the earlier research. See [hardware](docs/hardware.md), [firmware](docs/firmware.md), and [Wi-Fi](docs/undocumented-wifi.md).
- Stock firmware 1.3.2 contains local discovery, an event/control interface, and a CherryPy HTTP API. The HTTP API has device and sensor routes and uses signed tokens. The exact roles and verification limits are in [local interfaces](docs/interfaces.md).
- Approval of a new API token in stock firmware depends on a Telldus Live OpenID login. Existing token validation and several device routes run locally in firmware code. That distinction matters: a local API is not, by itself, a cloud-free onboarding path. See [authentication](docs/authentication.md).
- An independently written Python 2.7 plugin can use the firmware's existing API and JWT machinery. Its login, token approval, and selected API routes were exercised under MIPS user-mode emulation with synthetic settings and mocked devices. See [prototype](prototype/README.md) and [test record](docs/testing.md).
- Stock Z-Wave components include local controller and command paths, but full local administration and radio behavior remain unverified. RF433 has a separate local command path. See [RF433](docs/rf433.md), [Z-Wave local paths](docs/zwave-local.md), and [no-cloud status](docs/no-cloud.md).

These statements have different evidence levels. The project uses **STATICALLY VERIFIED**, **EXECUTED IN EMULATION**, **TESTED WITH MOCKED HARDWARE**, **VERIFIED ON PHYSICAL HARDWARE**, and **NOT YET VERIFIED** in the detailed documents. Emulated API calls do not demonstrate radio transmission or a safe installation on a gateway.

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

The prototype retains the stock token format and API dispatcher. It adds an owner login and an approval page, while a separate offline server draft uses CherryPy's existing TLS support. It is **not an installation package**. Certificate trust for a device IP address, the stock firewall, compatibility with third-party token clients, and a dependable rollback path still need work. Nothing in this repository should be copied onto a gateway without a separate review and hardware test plan.

## Read next

- [Hardware and UART](docs/hardware.md) · [bootloader](docs/uart-and-uboot.md) · [firmware](docs/firmware.md)
- [Local interfaces and API](docs/interfaces.md) · [authentication and TLS](docs/authentication.md)
- [RF433](docs/rf433.md) · [Z-Wave hardware](docs/zwave.md) · [Z-Wave local paths](docs/zwave-local.md)
- [No-cloud design and remaining work](docs/no-cloud.md) · [offline tests](docs/testing.md)
- [References and attribution](docs/references.md) · [security policy](SECURITY.md)

The [prototype README](prototype/README.md) explains which files are original code and why the prototype must remain offline. Test instructions require a separately obtained copy of firmware 1.3.2; the firmware, extracted filesystem, bytecode, device backups, and secrets are not distributed here.

## Acknowledgements

Thanks to [ob-wn](https://github.com/bobo843032/tellstick-znet-lite-v2-research/issues/1) for identifying the unauthenticated UDP 30303 interface, which prompted closer examination of the relevant firmware components. The [ob-wn no-cloud project](https://github.com/ob-wn/tellstick-znet-lite-v2-nocloud) provides a separate approach to local access. [R00S's local TellStick add-on](https://github.com/R00S/addon-tellstick-local) demonstrates a Home Assistant path for supported local RF433 functions. Their code has not been copied into this prototype; see [references](docs/references.md) for scope and licenses.

## License and scope

Original documentation is [CC BY 4.0](LICENSE). Original code under `prototype/` and `tests/` is [MIT licensed](LICENSE-CODE). Neither license covers Telldus firmware, third-party projects, private credentials, or device-specific data. This is independent research and is not affiliated with Telldus.

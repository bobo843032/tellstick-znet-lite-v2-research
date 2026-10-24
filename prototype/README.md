# Local owner authentication prototype

This is independently written Python 2.7 code for an **offline integration experiment** with TellStick ZNet Lite V2 firmware 1.3.2. It has not been installed on a gateway. The prototype uses the firmware's plugin interfaces and existing API token manager; it does not contain firmware files or vendor bytecode.

`localowner/LocalOwnerAuth.py` adds an owner login, a session-backed token approval page, logout, rate limiting, and CSRF checks. A verifier must be provisioned explicitly; there is no default password. `localowner/LocalHttpsServer.py` is a draft alternative CherryPy startup with TLS and Secure cookies. `localowner/local-ui.html` is a small browser UI for system information, devices, sensors, token requests, and basic on/off actions. `provision_owner.py` generates a verifier file for offline review. It is **not an installation instruction**.

The tests use an independently obtained and extracted copy of official firmware 1.3.2, a MIPS user-mode emulator, synthetic settings, and fake devices. The actual stock `ApiManager`, API routes, JWT implementation, and CherryPy package are exercised. See [test instructions](../docs/testing.md).

Known blockers before device deployment:

- The stock token request still returns an authorization URL for Telldus Live. The prototype UI deliberately opens its own approval page, but generic clients remain incompatible.
- Stock token approval has its own CSRF behavior. The local provider blocks that route for local sessions; the stock Live provider is unchanged.
- A trusted IP-address certificate and physical TLS behavior have not been established. The stock firewall does not include a TCP 443 allowance in the reviewed image.
- Overlay capacity, import order, service identity, persistence through upgrade, and a recovery path have not been verified on hardware.
- The existing web application and actual RF433/Z-Wave state synchronization have not been validated with this plugin on a gateway.

These blockers mean the code should be read as a reproducible experiment, not as a security patch or a supported way to modify a gateway. No installer or modified stock startup file is published. Original source in this directory is under [MIT](../LICENSE-CODE); no Telldus code is relicensed.

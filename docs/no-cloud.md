# No-cloud status and deployment limits

This project is investigating a path that retains the stock 1.3.2 firmware and its local radio stack while removing Telldus Live as a prerequisite for ordinary owner access. It is not currently an installable firmware patch or a complete Home Assistant integration.

## What the evidence supports

- **STATICALLY VERIFIED:** The firmware has local RF433 event/command handling, a token-protected HTTP API, and internal Z-Wave controller code. Some API dispatch paths do not make a cloud call when a valid local token already exists.
- **EXECUTED IN EMULATION:** Original MIPS Python 2.7, CherryPy, and JWT/API modules worked with a new local-owner provider using synthetic settings and devices.
- **TESTED WITH MOCKED HARDWARE:** A generic HTTP device operation and selected Z-Wave command paths reached mocked adapters or message queues.
- **VERIFIED ON PHYSICAL HARDWARE:** Earlier repository documents record hardware inspection, UART, and Wi-Fi tests on an owned unit. **None of the new local-owner, HTTP API, RF433, or Z-Wave no-cloud paths has this status.**

The local web prototype displays synthetic system information, devices, and sensors through the stock HTTP API and can request an API token. Its UI is not a proven replacement for Telldus Live. See [authentication](authentication.md) and [testing](testing.md).

## What still prevents a supported installation

1. **Token approval compatibility.** The stock response points to the original OpenID route. The local plugin now rewrites that approval URL only for successful HTTPS token requests; offline login/approval tests pass. Third-party clients and physical deployment still need validation.
2. **Transport.** The test server used TLS on loopback, but the stock firewall does not open the proposed HTTPS port. A trustworthy certificate for the gateway address, a deliberately scoped network rule, and proof that no alternate HTTP login path bypasses protection are required.
3. **Overlay and rollback.** SquashFS with an overlay suggests a possible non-flashing deployment. Actual free space, import order, startup ownership, service recovery, backup integrity, and persistence through an update have not been checked on a device. No public installer is supplied.
4. **Device data and RF433.** The existing [R00S local integration](references.md) offers a practical RF433 baseline; its model and event coverage must be checked against an owned unit. The stock UDP listener permits only one registered receiver. Radio delivery and state synchronization remain untested in this research phase.
5. **Z-Wave administration.** Local controller and generic node command code exists, but inclusion, exclusion, association management, and callbacks lack a reviewed local administrative API. Existing network state must be preserved. No physical Z-Wave procedure has been attempted.

The smallest next step is an explicitly authorized, **read-only** device preflight: confirm firmware version and intended network exposure, determine overlay capacity and module loading order, and establish an independent recovery path with verified backups. Only after those gates pass should a scoped installation and rollback plan be reviewed. The current code and tests must not be treated as instructions to install on a gateway.

# No-cloud status and deployment limits

This project is investigating a path that retains the stock 1.3.2 firmware and its local radio stack while removing Telldus Live as a prerequisite for ordinary owner access. It is not currently an installable firmware patch or a complete Home Assistant integration.

## Options compared

| Route | What it preserves | Main gap | Assessment |
| --- | --- | --- | --- |
| Existing stock JWT | Original API, RF433, and Z-Wave stack | New approval still depends on Telldus Live; stock transport is HTTP | Useful only where a valid token already exists; not durable onboarding |
| Local owner plugin in the stock process, staged through overlay | Original token table, JWT/API, and radio stack | Verified device access, TLS, overlay persistence, and rollback | **Recommended first controlled integration**, after readiness gates |
| Shadow or modify stock auth/web modules | Original operating system and radios | Larger version-specific patch surface and the same transport/recovery gates | Possible, but no advantage established over the plugin |
| Repackaged stock firmware | Existing application if licensing and integration permit | Vendor update signature, image format, full-flash risk, recovery, redistribution rights | Research option; not needed for the demonstrated local approval flow |
| New OpenWrt-based firmware | Potentially modern operating-system stack | Board port, 16 MB/64 MB limits, radio protocols, state migration, and recovery | Long-term separate project; not yet validated for this board |

The approval compatibility fix already redirects successful HTTPS token requests to the local page while leaving the stock issuer intact. A second independent process cannot use the pending requests stored in the stock process's `ApiManager.tokens`. An overlay that loads the local plugin in that process is therefore more direct than a sidecar. A loopback test also passed with the Live **web-authentication** provider omitted and rejected stock approval through a local session; it did not remove or validate the Live backend used elsewhere in the application. The overlay is a filesystem change, but it does **not** require replacing the SquashFS firmware image. For firmware-update and preservation details, see [update and recovery paths](update-and-recovery.md).

## What the evidence supports

- **STATICALLY VERIFIED:** The firmware has local RF433 event/command handling, a token-protected HTTP API, and internal Z-Wave controller code. Some API dispatch paths do not make a cloud call when a valid local token already exists.
- **EXECUTED IN EMULATION:** Original MIPS Python 2.7, CherryPy, and JWT/API modules worked with a new local-owner provider using synthetic settings and devices.
- **TESTED WITH MOCKED HARDWARE:** A generic HTTP device operation and selected Z-Wave command paths reached mocked adapters or message queues.
- **VERIFIED ON PHYSICAL HARDWARE:** Earlier repository documents record hardware inspection, UART, and Wi-Fi tests on an owned unit. **None of the new local-owner, HTTP API, RF433, or Z-Wave no-cloud paths has this status.**

The local web prototype displays synthetic system information, devices, and sensors through the stock HTTP API and can request an API token. Its UI is not a proven replacement for Telldus Live. See [authentication](authentication.md) and [testing](testing.md).

For an initial local RF433-only use case, [UDP 42314](udp-42314.md) and the existing R00S integration provide a narrower route that does not require JWT in the examined firmware handler. The recommended general architecture is the **in-process LocalOwner overlay for HTTPS token issuance and the stock HTTP API**, with one coordinated 42314 event recipient where RF433 events are needed. Keep device state verification in the client: neither a successful HTTP handler return against a mock nor a queued UDP command proves radio delivery. Z-Wave discovery and generic device commands have local code paths, but complete inclusion/exclusion and status callbacks need separate local interfaces and physical validation. Firmware replacement is not required for the demonstrated token workflow; [update and recovery constraints](update-and-recovery.md) still make installation NO-GO.

## What still prevents a supported installation

1. **Token approval compatibility and route isolation.** The stock response points to the original OpenID route. The local plugin now rewrites that approval URL only for successful HTTPS token requests; offline login/approval tests pass. Because the stock web router accepts any registered authentication provider, a local provider alone cannot veto stock approval through a separate Live session. A local-only release must close or harden that old route, then retest third-party clients and the physical deployment.
2. **Transport.** The test server used TLS on loopback, but the stock firewall does not open the proposed HTTPS port. A trustworthy certificate for the gateway address, a deliberately scoped network rule, and proof that no alternate HTTP login path bypasses protection are required.
3. **Overlay and rollback.** SquashFS with an overlay suggests a possible non-flashing deployment. Actual free space, import order, startup ownership, service recovery, backup integrity, and persistence through an update have not been checked on a device. No public installer is supplied.
4. **Device data and RF433.** The existing [R00S local integration](references.md) offers a practical RF433 baseline; its model and event coverage must be checked against an owned unit. The stock UDP listener permits only one registered receiver. Radio delivery and state synchronization remain untested in this research phase.
5. **Z-Wave administration.** Local controller and generic node command code exists, but inclusion, exclusion, association management, and callbacks lack a reviewed local administrative API. Existing network state must be preserved. No physical Z-Wave procedure has been attempted.

The smallest next step is an explicitly authorized, **read-only** device preflight: confirm firmware version and intended network exposure, determine overlay capacity and module loading order, and establish an independent recovery path with verified backups. Only after those gates pass should a scoped installation and rollback plan be reviewed. The current code and tests must not be treated as instructions to install on a gateway.

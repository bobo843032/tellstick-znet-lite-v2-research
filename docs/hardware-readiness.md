# First gateway test: readiness gates

This page began as the preflight checklist for the **local-owner authentication prototype**. Later work on an owned 1.3.2 gateway verified root SSH, firmware identity, anonymous HTTP/API behavior, a signed **separate MQTT test plugin**, and its persistence across daemon restarts. The local-owner prototype itself has not been installed, and its TLS/rollback gates remain open. The checklist below describes that prototype's remaining requirements; see the [physical verification matrix](../HARDWARE_VERIFICATION.md) for completed tests.

## Access and baseline

1. Confirm the gateway's current LAN address through an owned network inventory. Confirm that the connection reaches the expected device rather than another host.
2. Request `GET /api/system/info` without a credential and record only the HTTP status and non-sensitive response metadata. A protected stock API should reject an unauthenticated call. Do not send an API token or owner password over stock HTTP.
3. If an authorized read-only console is actually available, check `/etc/builddate`, the Python executable and package versions, service process, listeners, mount table, and free overlay space. Record checksums for the original startup file and any file that a future overlay would shadow. Do not modify the overlay in this phase.
4. Check logs for a normal boot and API request handling without issuing device commands. Confirm whether the stock web service remains on HTTP and whether the proposed HTTPS port is blocked as the reviewed image suggests.

A guarded first network command, after setting `TELLSTICK_IP` to a confirmed address, is:

```sh
curl -sS -i --noproxy '*' --connect-timeout 3 --max-time 8 \
  "http://${TELLSTICK_IP:?set the confirmed gateway IP}/api/system/info"
```

This does not submit credentials or control a radio. An unexpected 200, a redirect to another device, or no response requires investigation before continuing. Firmware version and authenticated behavior require a verified console or a separately established protected path; they cannot be inferred from a successful TCP connection alone.

## Why a second process is insufficient

The stock `ApiManager` keeps pending token requests in process memory. A separate CherryPy process would have a different pending-token table, even if it imported the same firmware modules. The tested compatibility change therefore needs to run in the application process that handles `PUT /api/token`. Signed plugin loading in that process is now verified using a separate MQTT test egg; safe deployment of the local-owner prototype and its authentication changes has not been established.

## Backup and rollback gate

Before local-owner deployment, an authorized operator needs an independent recovery channel and verified backups of the current startup file, overlay upper layer, `/etc/telldus/Telldus.conf`, and all known Z-Wave controller state that can actually be exported. These may contain credentials or network keys: preserve them in encrypted, access-controlled storage, verify checksums and restore readability, and keep values out of public logs. A 16 MiB full-flash backup has since been located outside this repository and matched against selected official firmware regions; a restore from it has **not** been tested. Overlay capacity and the prototype's exact rollback behavior still need checking.

The proposed change must be staged as a removable overlay with an explicit return to the original startup and web/API behavior. A serial or other independent administrative path must be tested before relying on that rollback. Preserving `Telldus.conf` alone may not preserve controller nonvolatile memory. **Installation is NO-GO until the backup and rollback path, TLS certificate trust, required firewall access, and absence of an alternate insecure owner-login route are verified on the actual gateway.**

The vendor-managed updater requires a valid detached signature before flashing, while the ordinary sysupgrade configuration list does not include the proposed startup shadow or Python plugin package. Therefore a future overlay installation must document how it is disabled, restored, or deliberately re-applied across a firmware upgrade. The board's inspected flash map does not show a redundant firmware slot. See [update and recovery paths](update-and-recovery.md) before planning either an overlay write or a custom image.

The original first-session preflight ended before any plugin write. Later, separately authorized tests installed and restarted a signed MQTT plugin and temporary observers. Those tests do not satisfy the remaining local-owner TLS or rollback gates; no Z-Wave inclusion/exclusion or RF433 transmission was part of them.

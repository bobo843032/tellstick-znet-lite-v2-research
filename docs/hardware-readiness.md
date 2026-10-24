# First gateway test: readiness gates

The local-owner prototype has passed software tests against firmware 1.3.2 modules. The next activity is a **read-only preflight on an owned gateway**, not installation. The earlier [UART work](uart-and-uboot.md) documents a physical Linux console at the time of that study, but it does not prove that SSH, a root shell, or writable overlay access is available now.

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

The stock `ApiManager` keeps pending token requests in process memory. A separate CherryPy process would have a different pending-token table, even if it imported the same firmware modules. The tested compatibility change therefore needs to run in the application process that handles `PUT /api/token`. The offline overlay draft identifies possible plugin registration points but has not established a safe way to deploy them on a gateway.

## Backup and rollback gate

Before any future write, an authorized operator needs an independent recovery channel and verified backups of the current startup file, overlay upper layer, `/etc/telldus/Telldus.conf`, and all known Z-Wave controller state that can actually be exported. These may contain credentials or network keys: preserve them in encrypted, access-controlled storage, verify checksums and restore readability, and keep values out of public logs. Determine overlay capacity, file ownership, and the exact service startup path on the device rather than relying solely on the firmware image.

The proposed change must be staged as a removable overlay with an explicit return to the original startup and web/API behavior. A serial or other independent administrative path must be tested before relying on that rollback. Preserving `Telldus.conf` alone may not preserve controller nonvolatile memory. **Installation is NO-GO until the backup and rollback path, TLS certificate trust, required firewall access, and absence of an alternate insecure owner-login route are verified on the actual gateway.**

The first hardware session should end after network identity, firmware identification, harmless API rejection/response, safe authentication-path assessment, and relevant logs. It must not register the plugin, install files, restart services, include or exclude Z-Wave nodes, or transmit RF433 commands.

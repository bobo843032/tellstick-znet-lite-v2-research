# Firmware and Filesystem Analysis — TellStick ZNet Lite V2

[Documentation index](../README.md#documentation)

## Overview

The Telldus TellStick ZNet Lite V2 runs a customized OpenWrt-based Linux firmware on an Atheros AR933x embedded platform.

The firmware includes a U-Boot bootloader, Linux kernel, compressed root filesystem, persistent writable storage, hardware drivers, Python-based application services, radio-controller interfaces, and firmware upgrade components.

This document covers the firmware environment observed on a TellStick ZNet Lite V2 running stock firmware version 1.3.2.

The earlier investigation used serial console access, Linux shell inspection, captured boot messages, and filesystem examination. A complete private flash backup was reported at the time, but its present file and checksum have not been located in the current research storage.

The objective is to document the firmware architecture, identify its major components, and distinguish confirmed behavior from areas requiring further analysis.

## Firmware Identification

| Component | Observed version or identification |
| --- | --- |
| Device | Telldus TellStick ZNet Lite V2 |
| Stock firmware | 1.3.2 |
| Operating system | OpenWrt Designated Driver r49388 |
| Linux kernel | 4.1.23 |
| CPU architecture | MIPS 24Kc |
| SoC | Atheros AR9330 rev 1 |
| Bootloader | U-Boot 1.1.4 |
| BusyBox | 1.24.2 |
| Python | 2.7 |
| CherryPy | 3.7.0 |
| Root filesystem | SquashFS |
| Persistent filesystem | JFFS2 |
| Flash storage | 16 MB SPI NOR |
| RAM | 64 MB DDR2 |

The firmware version refers to the examined device. Other firmware releases may contain different packages, scripts, partition layouts, or security mechanisms.

## Boot Architecture

The system follows a conventional embedded Linux boot process.

- Power applied
- U-Boot 1.1.4
  - Initialize CPU and memory
  - Initialize SPI flash
  - Initialize Ethernet
  - Read boot configuration
- Linux 4.1.23
  - Initialize Atheros platform
  - Detect SPI flash
  - Register MTD partitions
  - Mount root filesystem
  - Initialize network interfaces
  - Initialize internal USB devices
- OpenWrt userspace
  - System initialization
  - Network configuration
  - Persistent storage
  - Device services
- Telldus application
  - Python application startup
  - RF433 subsystem
  - Z-Wave subsystem
  - Network services
  - Remote-support component

This is a logical summary of the observed boot process, not a complete trace of every initialization step.

## U-Boot Bootloader

The bootloader identifies itself as:

```text
U-Boot 1.1.4 (Apr 28 2015, 09:40:42)
AP121 (AR9331) U-Boot for Telldus TellStick ZNet Lite
DRAM:   64 MB DDR2 16-bit
FLASH:  Winbond W25Q128 (16 MB)
CLOCKS: 400/400/200/33 MHz (CPU/RAM/AHB/SPI)
```

The bootloader provides an interactive serial console and supports operations including:

- Environment inspection
- Booting Linux images
- DHCP and network diagnostics
- TFTP image loading
- HTTP firmware recovery
- Serial and network console selection
- Memory inspection
- Flash operations

Selected commands:

```text
help
version
printenv
bootm
dhcp
ping
tftpboot
httpd
startnc
startsc
```

The command httpd is described by U-Boot as starting a web server for firmware recovery.

Its presence confirms that recovery functionality exists in the bootloader command set. It does not, by itself, establish the supported image format, validation behavior, or complete recovery procedure.

Some additional commands can modify persistent flash contents and device-specific configuration. They should not be used as ordinary diagnostic commands.

## Linux Kernel

The installed operating system uses Linux 4.1.23.

The captured boot messages identify the processor:

```text
CPU0 revision is: 00019374 (MIPS 24Kc)
SoC: Atheros AR9330 rev 1
MIPS: machine is Telldus TellStick ZNet Lite v2
```

### Kernel Command Line

```text
board=TELLSTICK-ZNET-LITE-V2 console=ttyATH0,115200 rootfstype=squashfs,jffs2 noinitrd
```

The command line identifies the board, serial console, filesystem types, and boot configuration.

The bootloader identifies an AR9331-based AP121 platform, while the Linux kernel identifies the SoC as AR9330 revision 1.

Both identifiers are preserved as reported. The difference has not been independently resolved through a definitive chip-marking inspection.

### Serial Console

The Linux console is exposed as:

```text
/dev/ttyATH0
```

The kernel reports:

```text
[    0.500634] ar933x-uart: ttyATH0 at MMIO 0x18020000 (irq = 11, base_baud = 1562500) is a AR933X UART
```

The console operates at 115200 baud.

## SPI Flash and MTD Layout

The device uses a Winbond W25Q128 SPI NOR flash device with 16 MB capacity.

### Flash Identification

```text
FLASH:  Winbond W25Q128 (16 MB)
```

Linux identifies the device through its SPI NOR driver:

```text
m25p80 spi0.0: found w25q128, expected m25p80
m25p80 spi0.0: w25q128 (16384 Kbytes)
```

### Partition Map

The following addresses were reported by the installed firmware:

| Partition | Start | End | Size |
| --- | --- | --- | --- |
| u-boot | 0x000000 | 0x020000 | 128 KiB |
| kernel | 0x020000 | 0x150AD8 | Approximately 1.19 MiB |
| rootfs | 0x150AD8 | 0xFF0000 | Approximately 13.66 MiB |
| rootfs_data | 0xBF0000 | 0xFF0000 | 4 MiB |
| art | 0xFF0000 | 0x1000000 | 64 KiB |
| firmware | 0x020000 | 0xFF0000 | 15.81 MiB |

### Partition Relationships

The partition table contains intentional overlaps.

The firmware partition represents an aggregate region containing the kernel and root filesystem.

The rootfs_data region represents persistent writable storage inside the broader root filesystem allocation.

These regions should not be treated as separate, non-overlapping physical flash chips or independent allocations.

### ART Calibration Data

The final 64 KiB of flash is assigned to:

```text
art
```

This region contains device-specific Atheros wireless calibration information.

It is not interchangeable between arbitrary units.

The original calibration region was preserved as part of the private backup process.

No ART contents are published.

## Root Filesystem and Persistent Storage

The firmware uses a compressed SquashFS root filesystem and a writable JFFS2 overlay.

### SquashFS

SquashFS stores the installed operating system and application files in a compressed, read-only filesystem.

Typical contents include:

- System binaries
- Shared libraries
- Kernel-related utilities
- Python runtime components
- Telldus application packages
- Default configuration
- Startup scripts

### JFFS2

JFFS2 provides writable persistent storage.

The writable layer allows configuration and selected filesystem changes to survive reboots without modifying the original compressed SquashFS image.

### Overlay Behavior

The resulting filesystem presents a combined view of read-only firmware contents and writable modifications.

A file that appears modified at runtime may originate from the writable overlay rather than the original SquashFS image.

This distinction is important when comparing a running system against an extracted stock firmware image.

## Userspace Environment

The firmware includes a compact embedded Linux userspace.

Identified software components include:

```text
BusyBox 1.24.2
Python 2.7
CherryPy 3.7.0
```

### BusyBox

BusyBox provides many standard Unix utilities in a compact executable suitable for embedded systems.

The available commands and supported options may differ from their full GNU counterparts.

### Python Runtime

Python 2.7 is used extensively by the Telldus application stack.

The installed filesystem contains Python standard-library modules and additional application packages.

The presence of Python makes the system relatively accessible for application-level inspection, although the runtime is obsolete and no longer receives upstream security support.

### CherryPy

CherryPy is present as part of the installed Python environment.

Its presence establishes that the framework is included, but does not independently establish which network endpoints are exposed in every operating mode.

## Telldus Application Components

The primary application entry point is:

```text
/usr/bin/tellstick-znet.py
```

Filesystem inspection also identified the firmware upgrade utility:

```text
/usr/bin/tellstick-upgrade.py
```

The application stack includes components for:

- Device and protocol handling
- RF433 communication
- Z-Wave communication
- Network-facing services
- Application startup and initialization
- Plugin integration
- Remote support
- Firmware updates

### Startup Architecture

The production startup process uses explicit component initialization in addition to Python package metadata and entry points.

Consequently, installing a new package or registering an entry point does not necessarily cause it to be loaded automatically by the production application.

This distinction is relevant when investigating application extensions or independently written integrations.

## Internal Radio Interfaces

The firmware communicates with two dedicated radio subsystems through internal USB serial interfaces.

### Captured Kernel Messages

```text
[   11.839356] cdc_acm 1-1.1:1.0: ttyACM0: USB ACM device
[   11.844816] cdc_acm 1-1.4:1.0: ttyACM1: USB ACM device
```

### Device Mapping

| Interface | Function |
| --- | --- |
| /dev/ttyACM0 | RF433 controller |
| /dev/ttyACM1 | Z-Wave controller |

The RF433 subsystem is associated with a Microchip PIC18F25K50 microcontroller and Maxim MAX7030 transceiver.

The Z-Wave subsystem uses a separate Sigma Designs controller.

The Linux host communicates with these controllers through their respective serial interfaces rather than directly controlling every low-level radio signal.

## Wireless Firmware Support

The stock Linux firmware initializes the integrated Atheros wireless interface.

### Captured Driver Message

```text
[   12.154904] ieee80211 phy0: Atheros AR9330 Rev:1 mem=0xb8100000, irq=2
```

The network interface is exposed as:

```text
wlan0
```

The installed wireless configuration references:

```text
platform/ar933x_wmac
```

Functional testing demonstrated scanning, WPA2 association, DHCP address assignment and network communication.

This confirms that the wireless support present in the firmware is operational on the examined device.

The discovery is documented separately in [Undocumented Wi-Fi](undocumented-wifi.md).

## Firmware Upgrade Components

The installed filesystem contains a dedicated firmware upgrade script:

```text
/usr/bin/tellstick-upgrade.py
```

The firmware also references a GPG keyring used in the upgrade environment:

```text
/etc/upgrade/telldus.gpg
```

The vendor updater checks declared file size and SHA-1, then requires successful GPG verification of a detached signature before it invokes `sysupgrade`. The downstream `sysupgrade` path performs board/image-format checks and writes the single aggregate firmware MTD region; it is a different trust boundary from the vendor downloader. The proposed local plugin is absent from the ordinary sysupgrade preservation list, so its persistence through an upgrade cannot be assumed. The exact control paths, offline verification, and recovery limits are in [firmware update and recovery paths](update-and-recovery.md).

## Remote-Support Components

The installed Python environment contains a remote-support package.

Identified package metadata:

```text
Telldus_Remotesupport-0.1-py2.7.egg-info
```

The package includes an embedded RSA private-key file at:

```text
/usr/lib/python2.7/site-packages/remotesupport/id_rsa
```

The associated support mechanism uses an outbound SSH connection and reverse TCP port forwarding.

Controlled testing against a researcher-operated SSH endpoint reproduced the relevant forwarding behavior.

The key is associated with authentication of the outbound connection.

It does not, by itself, demonstrate an authentication bypass of the gateway’s local SSH service.

No private-key contents or usable credentials are included in this repository.

Further analysis is documented in [Remote Support Architecture](remote-support.md).

## Firmware Inspection Commands

The command blocks below are inspection examples, not captured session output.

The following read-only commands are useful when examining a device with authorized Linux shell access.

### Kernel and Platform

```text
uname -a
cat /proc/cpuinfo
cat /proc/cmdline
```

### Memory

```text
cat /proc/meminfo
free
```

### Flash Layout

```text
cat /proc/mtd
```

### Filesystem

```text
mount
df -h
```

### Installed Software

```text
busybox
python --version
```

### Network Interfaces

```text
ip link show
```

### Kernel Messages

```text
dmesg
```

### Internal Serial Devices

```text
ls -l /dev/ttyACM*
```

These commands are intended for inspection and do not deliberately write to flash.

Their output may nevertheless contain identifying information and should be reviewed before publication.

## Firmware Backup and Evidence Handling

A complete flash backup was reported during the earlier research. Its current file location, checksum, and restore readiness have not been verified in this phase.

The reported full-flash capture would include the original firmware and hardware-specific flash contents; the actual image has not been re-examined.

### Memory Constraints

The device has only 64 MB of RAM.

Creating large temporary files in RAM-backed storage can exhaust available memory and destabilize the running system.

For large captures, streaming data to a separate research host is preferable to buffering an entire flash image in temporary storage.

### Publication Policy

The following materials are intentionally excluded:

- Complete firmware images
- Device-specific calibration data
- Private SSH keys
- Authentication credentials
- Unique device identifiers
- Unsanitized configuration files
- Proprietary source code without redistribution permission

Selected technical observations, sanitized logs and independently authored documentation may be published.

## Findings and Limitations

| Research area | Finding | Status |
| --- | --- | --- |
| Bootloader | U-Boot 1.1.4 | Confirmed |
| Linux kernel | 4.1.23 | Confirmed |
| OpenWrt release | Designated Driver r49388 | Confirmed |
| CPU architecture | MIPS 24Kc | Confirmed |
| Flash device | Winbond W25Q128 | Confirmed |
| Flash layout | MTD regions identified | Documented |
| Root filesystem | SquashFS | Confirmed |
| Writable storage | JFFS2 | Confirmed |
| Python application | Installed and examined | Confirmed |
| Firmware upgrade utility | Present | Confirmed |
| Upgrade GPG keyring | Referenced in filesystem | Confirmed |
| RF433 interface | /dev/ttyACM0 | Confirmed |
| Z-Wave interface | /dev/ttyACM1 | Confirmed |
| Integrated Wi-Fi | Functional | Tested |
| Remote-support package | Installed | Confirmed |
| Embedded SSH private key | Identified | Confirmed |
| Full flash backup | Historically reported; current artifact not located in reviewed storage | Requires verification before any write |
| Complete firmware upgrade trust model | Not fully established | Further research |
| Reproducible firmware build | Not established | Further research |
| All hardware revisions | Not tested | Unknown |

## Research Significance

The TellStick ZNet Lite V2 firmware contains a relatively complete embedded Linux environment with accessible diagnostics, identifiable internal services and modular Python applications.

The combination of U-Boot, OpenWrt, SquashFS/JFFS2 storage, USB-connected radio controllers and integrated Wi-Fi provides multiple opportunities for independent interoperability and hardware research.

The firmware also contains components that merit security review, particularly the remote-support authentication material and the firmware upgrade mechanism.

The evidence presented here establishes the existence and basic architecture of those components without making unsupported claims about manufacturer infrastructure, authentication bypasses or update-validation weaknesses.

## Related Documentation

- [Hardware Architecture](hardware.md)
- [UART Console and U-Boot](uart-and-uboot.md)
- [Undocumented Wi-Fi](undocumented-wifi.md)
- [Remote Support Architecture](remote-support.md)

## License and Disclaimer

This document contains independent research performed on personally owned hardware.

It is not affiliated with, sponsored by or endorsed by Telldus.

Original documentation is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0), unless otherwise noted.

Third-party firmware, proprietary source code, private credentials and device-specific calibration data are excluded from that license.

Telldus and TellStick are trademarks of their respective owners.

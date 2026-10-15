# UART Console and U-Boot — TellStick ZNet Lite V2

[Documentation index](../README.md#documentation)

## Overview

The Telldus TellStick ZNet Lite V2 exposes a functional serial console that provides access to both the U-Boot bootloader and the embedded Linux operating system.

During this investigation, bidirectional UART communication was established using an ESP32-S3-based serial bridge. The bootloader was successfully interrupted, its command interface examined, and the Linux startup sequence captured.

The serial interface provides a valuable entry point for firmware analysis, system diagnostics, recovery research and understanding the gateway’s internal architecture.

Verified capabilities include:

- Capturing the complete bootloader startup banner
- Interrupting the automatic boot sequence
- Accessing the interactive U-Boot command prompt
- Listing the available bootloader commands
- Observing Linux kernel initialization
- Accessing the Linux serial console
- Inspecting the running operating system

The observations below were obtained from personally owned hardware running stock firmware version 1.3.2.

## Hardware and Serial Interface

| Property | Observed value |
| --- | --- |
| Device | Telldus TellStick ZNet Lite V2 |
| Bootloader | U-Boot 1.1.4 |
| Main platform | Atheros AR933x / AP121 |
| Serial interface | UART |
| Signal levels | 3.3 V logic interface |
| Baud rate | 115200 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Linux console | ttyATH0 |
| Serial bridge | ESP32-S3 |
| Communication | Bidirectional, verified |

### Serial Configuration

```text
Baud rate:    115200
Data bits:    8
Parity:       None
Stop bits:    1
Flow control: None
RX inversion: Disabled
```

The UART uses logic-level signaling and must not be connected directly to an RS-232 interface with incompatible voltage levels.

A 3.3 V-compatible USB-to-UART adapter or microcontroller-based serial bridge can be used.

## UART Connection and Signal Identification

The debug interface was investigated by observing electrical signal levels and serial output during startup.

One identified transmit signal measured approximately 2.7 V while idle.

This measurement helped identify the gateway’s UART transmit line.

The following connection was verified during initial receive-side testing:

| Gateway signal | Serial bridge signal |
| --- | --- |
| TellStick TX | Serial bridge RX |
| TellStick GND | Serial bridge GND |

The final test setup also established the reverse data path, enabling input to the bootloader.

### Bidirectional Communication

Successful interruption of U-Boot demonstrated that the gateway could receive characters from the external serial interface.

This is important because receiving boot messages alone only establishes one-way communication.

An interactive bootloader prompt confirms that both communication directions are operational.

### Electrical Considerations

The exact PCB test-point layout is not documented here as a universal pinout.

Hardware revisions may differ, and the electrical connections should be verified before attaching external equipment.

The external serial bridge should share signal ground with the gateway, use compatible logic levels and avoid driving unknown PCB pads.

## ESP32-S3 Serial Bridge

An ESP32-S3-based bridge was used during the investigation.

The bridge allowed UART communication to be accessed through a separate network-connected interface.

The research setup used the following ESP32-S3 pins:

```text
ESP32-S3 GPIO6 / D3: UART RX
ESP32-S3 GPIO7 / D4: UART TX
```

The gateway’s transmit signal was connected to the bridge’s receive input.

### Bridge Architecture

- TellStick ZNet Lite V2
  - 115200 baud UART
- ESP32-S3 serial bridge
  - TCP transport
- Research workstation
  - Bootloader console
  - Linux serial console
  - Boot-log capture

The bridge exposed two TCP services during testing:

| Port | Function |
| --- | --- |
| 2323 | Raw UART data |
| 2324 | Bridge control |

These ports describe the research bridge configuration, not services provided by the stock TellStick firmware.

The bridge supported live serial configuration adjustments without requiring firmware reflashing.

## Original U-Boot Startup Log

The following excerpt preserves the original bootloader banner captured from the device.

```text
*********************************************
*   U-Boot 1.1.4  (Apr 28 2015, 09:40:42)   *
*********************************************
AP121 (AR9331) U-Boot for Telldus TellStick ZNet Lite
DRAM:   64 MB DDR2 16-bit
FLASH:  Winbond W25Q128 (16 MB)
CLOCKS: 400/400/200/33 MHz (CPU/RAM/AHB/SPI)
LED on during eth initialization...
Hit any key to stop autobooting:  0
```

### Hardware Information

The bootloader reports:

| Component | Reported value |
| --- | --- |
| Platform | AP121 / AR9331 |
| RAM | 64 MB DDR2 |
| Memory bus | 16-bit |
| Flash | Winbond W25Q128 |
| Flash capacity | 16 MB |
| CPU clock | 400 MHz |
| RAM clock | 400 MHz |
| AHB clock | 200 MHz |
| SPI clock | 33 MHz |

These values are reported by the bootloader and have not all been independently measured.

## Interrupting Automatic Boot

The normal boot sequence includes a countdown during which user input can interrupt startup.

During testing, pressing Enter successfully interrupted the automatic boot sequence.

The interactive prompt appeared as:

```text
uboot>
```

This confirmed that the serial interface supported input as well as output.

The captured session also contained an unrecognized character sequence after entering the bootloader.

That produced the following response (the original input is replaced with `[UNRECOGNIZED INPUT]`):

```text
## Error: unknown command '[UNRECOGNIZED INPUT]' - try 'help'
```

The unrecognized input was separate from the successful interruption of automatic boot.

The bootloader itself remained functional.

## Original U-Boot Help Output

The following command list was captured from the interactive U-Boot environment.

```text
uboot> help
help
?        - alias for 'help'
boot     - boot default, i.e., run 'bootcmd'
bootd    - boot default, i.e., run 'bootcmd'
bootm    - boot application image from memory
clearclk - remove PLL and clocks configuration from FLASH
cp       - memory copy
dhcp     - invoke DHCP client to obtain IP/boot params
echo     - echo args to console
erase    - erase FLASH memory
exit     - exit script
go       - start application at address 'addr'
help     - print embedded help
httpd    - start www server for firmware recovery
itest    - return true/false on integer compare
md       - memory display
mm       - memory modify (auto-incrementing)
mtest    - RAM test
mw       - memory write (fill)
nm       - memory modify (constant address)
ping     - send ICMP ECHO_REQUEST to network host
printenv - print environment variables
printmac - print MAC address stored in FLASH
reset    - perform RESET of the CPU
run      - run commands in an environment variable
setclk   - select clocks configuration from predefined list
setenv   - set environment variables
setmac   - save new MAC address in FLASH
setsecret - save new secret in FLASH
startnc  - start net console
startsc  - start serial console
test     - minimal test like /bin/sh
tftpboot - boot image via network using TFTP protocol
version  - print U-Boot version
```

This output demonstrates that the bootloader provides more than a minimal firmware-loading environment.

It includes networking, recovery, console control, memory access and persistent configuration operations.

## Notable Bootloader Features

### HTTP Recovery Server

The command list includes:

```text
httpd    - start www server for firmware recovery
```

This indicates the presence of a bootloader-level HTTP recovery feature.

Such functionality may allow firmware recovery independently of the installed Linux operating system.

The exact recovery interface, accepted image format, validation behavior and flash-writing procedure have not been fully established by this command listing alone.

### Network Console

The following commands are available:

```text
startnc  - start net console
startsc  - start serial console
```

These indicate support for switching between network-console and serial-console operation.

The existence of these commands does not establish that a network console is enabled during normal operation.

### Network Booting

The bootloader provides:

```text
dhcp
ping
tftpboot
bootm
```

These commands support network diagnostics and loading or booting images.

No claim is made that arbitrary firmware images can be booted successfully without additional compatibility testing.

### Environment Inspection

The bootloader includes:

```text
printenv
```

This command displays U-Boot environment variables.

Depending on the installed configuration, environment variables may contain network information, boot parameters or device-specific settings.

Captured output should be reviewed before publication.

### Flash and Persistent Configuration

Several commands can modify memory, flash contents or persistent device parameters:

```text
erase
cp
mw
mm
nm
clearclk
setclk
setmac
setsecret
```

These commands are documented here because they were present in the captured command list.

They are not required for ordinary serial access or boot-log collection.

Incorrect use may overwrite firmware, calibration information or bootloader configuration.

## Linux Boot Process

After U-Boot loads the installed firmware, the Linux kernel initializes the Atheros platform and its peripheral devices.

### Kernel Identification

The captured boot log includes:

```text
CPU0 revision is: 00019374 (MIPS 24Kc)
SoC: Atheros AR9330 rev 1
MIPS: machine is Telldus TellStick ZNet Lite v2
```

The bootloader identifies an AR9331-based AP121 platform, while Linux identifies the SoC as AR9330 revision 1.

These are the original identifiers reported by their respective software components.

### Kernel Command Line

```text
board=TELLSTICK-ZNET-LITE-V2 console=ttyATH0,115200 rootfstype=squashfs,jffs2 noinitrd
```

The command line identifies:

- The board-specific machine configuration
- The Linux serial console
- The console baud rate
- SquashFS and JFFS2 filesystem support
- The absence of an initial RAM disk

### Serial Console Initialization

The kernel identifies its UART device as:

```text
ttyATH0
```

The original kernel log includes:

```text
[    0.500634] ar933x-uart: ttyATH0 at MMIO 0x18020000 (irq = 11, base_baud = 1562500) is a AR933X UART
```

This confirms that the Linux serial console uses the Atheros UART peripheral.

## Linux Console Access

During normal startup, the device displays:

Please press Enter to activate this console.

This message indicates that an interactive Linux console is available after the system has booted.

During the investigation, the serial interface was used to interact with the running Linux environment.

The ability to inspect the operating system through the console enabled subsequent analysis of:

- Kernel messages
- Network interfaces
- Filesystem structure
- Flash partitions
- Internal USB devices
- Wireless hardware
- Application startup behavior
- Installed Python packages

The exact authentication and access behavior may differ between firmware versions and device configurations.

## Flash and Filesystem Information

The boot process identifies a 16 MB SPI NOR flash device.

The installed Linux system reports the following partitions:

| Partition | Start | End |
| --- | --- | --- |
| u-boot | 0x000000 | 0x020000 |
| kernel | 0x020000 | 0x150AD8 |
| rootfs | 0x150AD8 | 0xFF0000 |
| rootfs_data | 0xBF0000 | 0xFF0000 |
| art | 0xFF0000 | 0x1000000 |
| firmware | 0x020000 | 0xFF0000 |

The firmware region is an aggregate partition, while rootfs_data represents writable storage within the root filesystem allocation.

The device uses SquashFS with JFFS2 writable storage.

The ART partition contains device-specific calibration information.

## Additional Hardware Identified During Boot

The serial boot log also reveals internal peripherals that are not directly visible through the standard product interface.

### Wireless Hardware

```text
[   12.154904] ieee80211 phy0: Atheros AR9330 Rev:1 mem=0xb8100000, irq=2
```

This confirms that the kernel recognizes the integrated Atheros wireless MAC.

Subsequent experiments demonstrated functional Wi-Fi connectivity.

### USB Serial Interfaces

```text
[   11.839356] cdc_acm 1-1.1:1.0: ttyACM0: USB ACM device
[   11.844816] cdc_acm 1-1.4:1.0: ttyACM1: USB ACM device
```

These interfaces correspond to the internal RF433 and Z-Wave subsystems.

The boot log therefore provides evidence for the gateway’s multi-controller architecture.

## Reproducible Read-Only Inspection

The command blocks below are inspection examples, not captured session output.

The following commands are suitable for basic inspection of an accessible U-Boot or Linux console.

### U-Boot

```text
help
version
```

The following command may expose device-specific configuration and should not be published without sanitization:

```text
printenv
```

### Linux

Inspect kernel messages:

```text
dmesg
```

Inspect the kernel command line:

```text
cat /proc/cmdline
```

Inspect MTD partitions:

```text
cat /proc/mtd
```

Inspect CPU information:

```text
cat /proc/cpuinfo
```

Inspect available memory:

```text
cat /proc/meminfo
```

Inspect network interfaces:

```text
ip link show
```

Inspect USB serial devices:

```text
ls -l /dev/ttyACM*
```

These commands do not intentionally modify flash contents or persistent configuration.

Outputs should still be reviewed for identifiers before public distribution.

## Recovery Considerations

The bootloader provides several capabilities relevant to firmware recovery, including HTTP recovery, TFTP image loading and direct flash operations.

However, the presence of recovery commands does not guarantee that every firmware image is accepted or that every failure can be recovered through software alone.

Before modifying firmware, relevant considerations include:

- Preserving the original flash contents
- Preserving device-specific calibration data
- Understanding partition boundaries
- Confirming image compatibility
- Maintaining reliable serial access
- Avoiding interruption during flash operations

A full flash backup was preserved privately during this research.

No device-specific firmware image or calibration data is distributed in this repository.

## Findings and Limitations

| Finding | Evidence | Status |
| --- | --- | --- |
| UART output available | Serial capture | Verified |
| Bidirectional UART communication | Interactive bootloader | Verified |
| 115200 8N1 configuration | Working serial connection | Verified |
| U-Boot 1.1.4 | Original boot banner | Confirmed |
| AP121 / AR9331 bootloader identification | Original boot banner | Confirmed |
| 64 MB DDR2 | U-Boot output | Confirmed |
| 16 MB Winbond SPI flash | U-Boot and Linux | Confirmed |
| Interactive U-Boot prompt | Controlled test | Verified |
| HTTP recovery command | U-Boot help | Confirmed |
| Network console commands | U-Boot help | Confirmed |
| Linux serial console | Boot output and interaction | Verified |
| AR9330 Linux identification | Kernel log | Confirmed |
| Internal Wi-Fi interface | Kernel log and functional testing | Verified |
| Internal USB serial interfaces | Kernel log | Confirmed |
| Complete UART PCB pinout | Not fully documented | Not established |
| Full HTTP recovery behavior | Not fully tested | Not established |
| Complete electrical schematic | Not available | Not established |

## Research Significance

The accessible UART interface is one of the most useful diagnostic features of the TellStick ZNet Lite V2.

It allows direct observation of the boot process before the main application starts and provides visibility into both the bootloader and operating system.

The U-Boot command environment exposes recovery and diagnostic capabilities that are not available through the standard gateway interface.

Combined with Linux console access, the serial interface enabled identification of the device’s hardware architecture, internal radio interfaces, firmware layout and undocumented wireless functionality.

These findings establish a practical foundation for further firmware, hardware and interoperability research.

## Related Documentation

- [Hardware Architecture](hardware.md)
- [Undocumented Wi-Fi](undocumented-wifi.md)
- [Remote Support Architecture](remote-support.md)

## License and Disclaimer

This document contains independent research performed on personally owned hardware.

It is not affiliated with, sponsored by or endorsed by Telldus.

Original research documentation is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0), unless otherwise noted.

No private credentials, device-specific secrets, firmware images or calibration data are distributed.

Telldus and TellStick are trademarks of their respective owners.

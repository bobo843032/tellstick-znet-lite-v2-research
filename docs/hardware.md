Hardware Architecture — TellStick ZNet Lite V2

Overview

The Telldus TellStick ZNet Lite V2 is an embedded Linux home automation gateway built around an Atheros AR933x platform.

Unlike a simple radio-to-Ethernet bridge, the device contains a complete Linux computer with dedicated processing, memory, non-volatile storage, networking hardware and separate radio controllers.

The examined hardware includes:

* Atheros AR933x system-on-chip
* 64 MB DDR2 RAM
* 16 MB Winbond SPI NOR flash
* Integrated Ethernet networking
* Integrated 2.4 GHz Wi-Fi hardware
* USB host controller and internal USB hub
* Maxim MAX7030 RF433 transceiver
* Microchip PIC18F25K50 microcontroller
* Sigma Designs Z-Wave controller
* Accessible 3.3 V UART console

This document combines physical component identification with evidence obtained from the bootloader, Linux kernel and operating-system interfaces.

Hardware observations refer to the examined TellStick ZNet Lite V2 running firmware version 1.3.2.

⸻

1. Hardware Specifications

Component	Identification	Function	Evidence
Main SoC	Atheros AR933x family	CPU, networking and USB	Bootloader and Linux
CPU	MIPS 24Kc	Main application processor	Linux kernel
RAM	64 MB DDR2, 16-bit	System memory	U-Boot
SPI flash	Winbond W25Q128	Firmware storage	U-Boot and Linux
Flash capacity	16 MB	Non-volatile storage	U-Boot and Linux
Ethernet	AR933x integrated networking	Wired network connectivity	Linux
Wi-Fi	AR9330 integrated wireless MAC	2.4 GHz wireless networking	Linux and functional test
USB	EHCI USB 2.0 host	Internal peripheral communication	Linux
RF433 transceiver	Maxim MAX7030	ASK/OOK radio	Physical identification
RF433 MCU	Microchip PIC18F25K50	Radio interface processing	Physical identification
Z-Wave controller	Sigma Designs	Z-Wave communication	Physical identification
Debug console	AR933x UART	Bootloader and Linux console	Serial testing

The bootloader identifies the board as an AR9331-based AP121 platform, while Linux reports an AR9330 revision 1 SoC.

Both identifications are retained because they originate from different software layers. A definitive reconciliation would require further hardware identification.

2. Logical System Architecture

TellStick ZNet Lite V2
|
+-- Atheros AR933x SoC
|   |
|   +-- MIPS 24Kc CPU
|   +-- DDR2 memory interface
|   |   |
|   |   +-- 64 MB RAM
|   |
|   +-- SPI controller
|   |   |
|   |   +-- Winbond W25Q128
|   |       +-- U-Boot
|   |       +-- Linux kernel
|   |       +-- Root filesystem
|   |       +-- Persistent data
|   |       +-- ART calibration region
|   |
|   +-- Ethernet controller
|   |   |
|   |   +-- Wired network interface
|   |
|   +-- Integrated wireless MAC
|   |   |
|   |   +-- phy0
|   |   +-- wlan0
|   |
|   +-- UART controller
|   |   |
|   |   +-- ttyATH0
|   |
|   +-- USB 2.0 host controller
|       |
|       +-- Internal USB hub
|           |
|           +-- USB CDC ACM interface
|           |   |
|           |   +-- ttyACM0
|           |   +-- RF433 subsystem
|           |       +-- PIC18F25K50
|           |       +-- MAX7030
|           |
|           +-- USB CDC ACM interface
|               |
|               +-- ttyACM1
|               +-- Z-Wave subsystem
|                   +-- Sigma Designs
|
+-- External interfaces
    |
    +-- Ethernet
    +-- Power
    +-- Radio antennas

This is a logical architecture diagram derived from observed hardware and software behavior.

It is not a verified electrical schematic. Individual signal paths, power rails and component interconnections require further physical measurement.

3. Main Processor — Atheros AR933x

The main processor belongs to the Atheros AR933x family.

It provides the computing resources required to run Linux and the gateway application.

Bootloader Identification

The captured U-Boot startup identifies the platform as:

AP121 (AR9331) U-Boot for Telldus TellStick ZNet Lite

Linux Identification

The kernel reports:

[    0.000000] SoC: Atheros AR9330 rev 1

Additional processor information:

CPU0 revision is: 00019374 (MIPS 24Kc)

The device runs a MIPS-based OpenWrt environment with the Telldus application stack executing directly on the Linux host.

Observed Clock Configuration

U-Boot reports:

CLOCKS: 400/400/200/33 MHz (CPU/RAM/AHB/SPI)

These values describe the clock configuration reported during the captured boot process.

4. System Memory

The bootloader reports:

DRAM:   64 MB DDR2 16-bit

This establishes the installed memory capacity and bus width reported by the bootloader.

The device’s 64 MB RAM capacity is relevant when performing firmware analysis or collecting large memory and flash captures.

A complete 16 MB flash image represents a substantial fraction of the available system memory.

For this reason, storing large captures in RAM-backed temporary storage can exhaust available memory.

Streaming data to an external research host is preferable when collecting large diagnostic artifacts.

5. SPI Flash — Winbond W25Q128

The device contains a Winbond W25Q128 SPI NOR flash device.

Bootloader Evidence

FLASH:  Winbond W25Q128 (16 MB)

Linux Detection

[    0.527493] m25p80 spi0.0: found w25q128, expected m25p80
[    0.531448] m25p80 spi0.0: w25q128 (16384 Kbytes)

The flash contains the bootloader, Linux firmware, filesystem data and hardware-specific calibration information.

Observed Flash Layout

Partition	Start	End
u-boot	0x000000	0x020000
kernel	0x020000	0x150AD8
rootfs	0x150AD8	0xFF0000
rootfs_data	0xBF0000	0xFF0000
art	0xFF0000	0x1000000
firmware	0x020000	0xFF0000

The firmware region overlaps the kernel and root filesystem partitions because it represents an aggregate firmware region.

The rootfs_data region occupies part of the root filesystem allocation.

ART Calibration Region

The ART partition is located at the end of the flash:

Start: 0xFF0000
End:   0x1000000
Size:  64 KiB

This region contains hardware-specific wireless calibration information.

Preserving the original ART data is important when performing firmware recovery or hardware experiments.

Calibration data from another device should not be assumed compatible.

6. Ethernet Networking

The Atheros platform provides integrated wired networking.

The operating system exposes the Ethernet interface as:

eth0

During startup, the kernel reports:

[   24.199626] IPv6: ADDRCONF(NETDEV_UP): eth0: link is not ready

This message records the interface state during initialization and does not indicate a permanent connectivity failure.

Ethernet is the gateway’s standard network connection method.

7. Integrated Wi-Fi Hardware

The examined device contains a working integrated 2.4 GHz Wi-Fi interface.

The Linux kernel registers the wireless hardware as:

[   12.154904] ieee80211 phy0: Atheros AR9330 Rev:1 mem=0xb8100000, irq=2

The wireless network interface is:

wlan0

The OpenWrt wireless configuration references:

platform/ar933x_wmac

This identifies the integrated Atheros wireless MAC rather than a USB-connected Wi-Fi adapter.

Functional Verification

Controlled testing demonstrated:

* 2.4 GHz wireless network scanning
* WPA2 association
* DHCP address assignment
* Working network communication

Recorded connection measurements included:

Frequency:  2462 MHz
Signal:     -56 dBm
TX bitrate: 57.8 Mbit/s

These values are summarized from the functional test rather than reproduced as a complete original terminal transcript.

The presence of working Wi-Fi hardware does not establish that the product was designed, validated or certified for Wi-Fi use as an official customer-facing feature.

Detailed findings are documented in Undocumented Wi-Fi.

8. USB Host and Internal Hub

The main SoC provides a USB host controller.

The Linux kernel identifies an EHCI USB 2.0 controller.

Original Boot Log

[    3.739028] ehci_hcd: USB 2.0 'Enhanced' Host Controller (EHCI) Driver
[    3.755774] ehci-platform ehci-platform: new USB bus registered, assigned bus number 1
[    3.787114] ehci-platform ehci-platform: USB 2.0 started, EHCI 1.00
[    3.793245] hub 1-0:1.0: USB hub found

A downstream USB hub is subsequently detected:

[    4.390036] usb 1-1: new high-speed USB device number 2 using ehci-platform
[    4.551045] hub 1-1:1.0: USB hub found

Two full-speed USB devices appear behind the hub:

[    4.837085] usb 1-1.1: new full-speed USB device number 3 using ehci-platform
[    5.027086] usb 1-1.4: new full-speed USB device number 4 using ehci-platform

Later, the CDC ACM driver registers two serial interfaces:

[   11.839356] cdc_acm 1-1.1:1.0: ttyACM0: USB ACM device
[   11.844816] cdc_acm 1-1.4:1.0: ttyACM1: USB ACM device

Interface Mapping

USB path	Linux device	Function
1-1.1	/dev/ttyACM0	RF433 controller
1-1.4	/dev/ttyACM1	Z-Wave controller

The operating system communicates with both radio subsystems through these internal USB serial interfaces.

9. RF433 Hardware

The 433 MHz subsystem contains two identified components.

Maxim MAX7030

The Maxim MAX7030 is an ASK/OOK radio transceiver associated with the device’s 433 MHz functionality.

The transceiver provides the radio-frequency interface, while higher-level signal handling involves the accompanying microcontroller and software.

Microchip PIC18F25K50

The PIC18F25K50 is a USB-capable microcontroller associated with the RF433 subsystem.

The Linux host communicates with the controller through:

/dev/ttyACM0

The observed USB identification for this subsystem is:

1781:0c32

The application receives structured radio messages through this interface.

This does not establish that the host receives unrestricted raw RF waveforms.

Areas for Further Investigation

Additional hardware research could examine:

* Connections between the PIC and MAX7030
* Serial and control signals
* Radio transmit and receive control
* Microcontroller firmware behavior
* Available test points
* The division of protocol processing between the PIC and Linux

The exact electrical connections have not been completely mapped.

10. Z-Wave Hardware

The gateway includes a separate Sigma Designs Z-Wave controller.

The examined hardware was associated with a controller marked approximately:

SD3503T-CNE3

This marking should be verified against high-resolution PCB photographs before being treated as a definitive component identification.

The observed USB identifier is:

0658:0200

The operating system exposes the controller as:

/dev/ttyACM1

The Z-Wave subsystem is separate from the RF433 controller.

Its dedicated radio hardware and firmware should not be assumed to provide general-purpose sub-GHz reception.

11. UART Debug Interface

The device provides a UART console connected to the Atheros platform.

Serial Parameters

Baud rate: 115200
Data bits: 8
Parity:    None
Stop bits: 1
Signaling: 3.3 V UART

The Linux console device is:

ttyATH0

The kernel reports:

[    0.500634] ar933x-uart: ttyATH0 at MMIO 0x18020000 (irq = 11, base_baud = 1562500) is a AR933X UART

Verified Functionality

The serial interface was used to:

* Capture U-Boot startup output
* Interrupt the bootloader
* Access the interactive U-Boot prompt
* Observe Linux initialization
* Interact with the running Linux console

A 3.3 V USB-to-UART adapter or equivalent serial bridge is appropriate for this interface.

The exact PCB pad arrangement should be verified independently before connecting equipment.

Do not connect RS-232 voltage levels directly to the SoC UART.

Connecting two independently powered devices also requires a common signal ground and appropriate voltage-level compatibility.

12. Hardware Evidence and Limitations

The research combines several evidence sources.

Observation	Evidence	Confidence
Atheros platform	Bootloader and Linux	Confirmed
MIPS 24Kc CPU	Kernel identification	Confirmed
64 MB DDR2 RAM	U-Boot output	Confirmed
Winbond W25Q128 flash	U-Boot and Linux	Confirmed
Integrated Wi-Fi	Kernel and functional test	Confirmed
USB host controller	Kernel log	Confirmed
Internal USB hub	Kernel log	Confirmed
Two CDC ACM interfaces	Kernel log	Confirmed
RF433 MAX7030	Physical identification	Identified
RF433 PIC18F25K50	Physical identification	Identified
Z-Wave controller	Physical and USB identification	Identified
UART console	Serial testing	Verified
Complete PCB schematic	Not available	Not established
Full power-rail mapping	Not completed	Not established
Complete RF signal mapping	Not completed	Not established

The distinction between software identification, physical inspection and direct electrical measurement is maintained throughout this document.

13. Research Opportunities

Several areas remain suitable for further investigation.

RF433 Microcontroller

The PIC18F25K50 may be investigated to better understand the processing performed before radio events reach the Linux application.

Hardware Signal Mapping

Tracing the connections between the MAX7030, PIC microcontroller and surrounding components would help establish the exact radio-control architecture.

Wi-Fi Antenna and RF Path

Further physical inspection could establish the antenna configuration and any populated or unpopulated matching-network components.

Power Architecture

Identifying voltage regulators, supply rails and power sequencing would improve the hardware documentation.

Hardware Revision Comparison

Comparing multiple TellStick ZNet Lite V2 units could help determine whether the identified components and wireless capability are consistent across production revisions.

These are potential research directions, not completed findings.

14. Evidence and Publication Policy

The repository publishes technical observations and sanitized evidence.

The following material is excluded:

* Personal identifiers
* Device-specific MAC addresses
* Wi-Fi credentials
* Private SSH keys
* Authentication tokens
* Unique hardware calibration data
* Unmodified firmware images containing sensitive material

Hardware identifiers, component markings, kernel messages and technical measurements are retained when relevant to reproducibility.

Conclusion

The TellStick ZNet Lite V2 is a complete embedded Linux system built around an Atheros AR933x platform.

Its hardware includes 64 MB DDR2 RAM, 16 MB SPI flash, integrated Ethernet and Wi-Fi, an internal USB architecture, and separate RF433 and Z-Wave controllers.

The integrated Wi-Fi interface is especially notable because it was successfully tested despite not being exposed as a standard product feature.

The accessible UART console and identifiable internal interfaces make the device suitable for detailed hardware, firmware and interoperability research.

The available evidence establishes the main system architecture, while complete electrical schematics and lower-level radio-controller behavior remain subjects for further investigation.

⸻

Related Documentation

* Undocumented Wi-Fi
* Remote Support Architecture

License and Disclaimer

This is independent research performed on personally owned hardware.

The documentation is not affiliated with, sponsored by or endorsed by Telldus.

Original research documentation is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0), unless otherwise noted.

Telldus and TellStick are trademarks of their respective owners.

# Z-Wave Subsystem — Hardware, USB Interface and Firmware Architecture

[Documentation index](../README.md#documentation)

## Overview

The Telldus TellStick ZNet Lite V2 contains a dedicated Z-Wave subsystem that operates independently of the gateway’s 433 MHz radio controller.

The Z-Wave hardware is connected internally to the Atheros Linux host through USB and appears as a CDC ACM serial device.

The installed firmware communicates with this controller through a software adapter integrated into the Telldus application stack.

This document describes the identified USB interface, controller architecture, software integration, and opportunities for further research.

The findings are based on examination of a personally owned TellStick ZNet Lite V2 running stock firmware version 1.3.2.

The central architectural finding is that Z-Wave functionality is provided by a separate controller, not by the Atheros processor’s integrated wireless interface.

## Identified Hardware

The investigation identified a dedicated Sigma Designs Z-Wave controller connected to the Linux host.

| Component | Identification | Function |
| --- | --- | --- |
| Host processor | Atheros AR933x | Runs Linux and Telldus applications |
| Z-Wave controller | Sigma Designs | Z-Wave communication |
| USB vendor ID | 0658 | Sigma Designs |
| USB product ID | 0200 | Z-Wave controller interface |
| Linux driver | cdc_acm | USB serial communication |
| Linux device | /dev/ttyACM1 | Z-Wave serial interface |
| Firmware platform | OpenWrt / Linux 4.1.23 | Host operating system |

The exact Z-Wave controller chip model, hardware revision, firmware version and supported Z-Wave feature set have not been independently established.

The USB identification is not sufficient to determine all of those properties.

## System Architecture

The Z-Wave controller is part of the gateway’s internal USB architecture.

- TellStick ZNet Lite V2
  - Atheros AR933x
    - Linux 4.1.23
    - Telldus application
- |
  - Z-Wave software adapter
- |
  - Device management
- |
  - Application events
  - USB host controller
    - Internal USB hub
      - Sigma Designs Z-Wave controller
        - USB CDC ACM
        - /dev/ttyACM1
        - Z-Wave radio
  - Separate RF433 subsystem
    - PIC18F25K50
    - MAX7030
    - /dev/ttyACM0

This is a logical architecture outline based on the identified components and interfaces.

It is not a complete electrical schematic.

## USB Identification

The Z-Wave controller was identified with the following USB vendor and product identifiers:

```text
Vendor ID:  0658
Product ID: 0200
```

These identifiers are associated with Sigma Designs Z-Wave controller hardware.

The interface is exposed to Linux as:

```text
/dev/ttyACM1
```

### Original Kernel Log

The captured boot sequence includes:

```text
[   11.839356] cdc_acm 1-1.1:1.0: ttyACM0: USB ACM device
[   11.844816] cdc_acm 1-1.4:1.0: ttyACM1: USB ACM device
```

The two interfaces correspond to different internal controllers.

| Device | Subsystem |
| --- | --- |
| /dev/ttyACM0 | RF433 |
| /dev/ttyACM1 | Z-Wave |

The association was established on the examined device.

Linux device numbering is determined during enumeration and should not be assumed to remain identical under every hardware or boot configuration.

## USB CDC ACM Communication

The controller uses the Linux USB Communications Device Class Abstract Control Model driver.

The kernel module is commonly identified as:

```text
cdc_acm
```

This driver exposes compatible USB devices through character-device interfaces such as:

```text
/dev/ttyACM1
```

### Communication Layers

1. Telldus application
2. Z-Wave software adapter
3. Linux serial interface
4. USB CDC ACM
5. Sigma Designs controller
6. Z-Wave radio network

The USB connection carries communication between the host application and the dedicated controller.

It does not mean that the Linux host directly handles all radio timing, modulation, routing or protocol operations.

Those responsibilities may be divided between the controller firmware and host software.

The precise division has not been completely characterized.

## Z-Wave and RF433 Are Separate Systems

The TellStick ZNet Lite V2 supports two distinct radio subsystems.

Although both appear as USB serial devices, their hardware and protocol architectures differ.

| Property | Z-Wave | RF433 |
| --- | --- | --- |
| Controller manufacturer | Sigma Designs | Microchip |
| Identified controller | Exact model not established | PIC18F25K50 |
| Radio hardware | Dedicated Z-Wave controller | Maxim MAX7030 |
| USB ID | 0658:0200 | 1781:0c32 |
| Observed Linux device | /dev/ttyACM1 | /dev/ttyACM0 |
| Host interface | USB CDC ACM | USB CDC ACM |
| Protocol | Z-Wave | Supported 433 MHz protocols |
| Network behavior | Z-Wave protocol stack | Protocol-dependent |

These differences are important when considering driver support, firmware modification or independent integrations.

A technique applicable to the RF433 controller cannot automatically be applied to the Z-Wave controller.

## Software Integration

The stock Telldus firmware includes Python-based application components responsible for interacting with the radio subsystems.

The main application entry point is:

```text
/usr/bin/tellstick-znet.py
```

The application stack includes Z-Wave adapter functionality.

### Logical Application Flow

1. Application startup
2. Z-Wave adapter initialization
3. Serial communication
4. /dev/ttyACM1
5. Z-Wave controller
6. Z-Wave network

The application may use the controller for operations such as device communication and network management.

However, the precise commands, supported management functions and error-handling behavior have not been fully documented in this investigation.

### Startup Considerations

The production Telldus application uses explicit initialization of selected components.

The presence of a Python module or package entry point does not necessarily mean that arbitrary replacement modules will be loaded automatically.

Any independent integration would need to account for the actual application startup path and serial-port ownership.

## Z-Wave Controller Responsibilities

A dedicated Z-Wave controller typically performs protocol-specific operations that are separate from ordinary Linux networking.

Potential responsibilities include:

- Radio communication
- Z-Wave protocol framing
- Controller state management
- Communication with included nodes
- Network-related protocol operations
- Reporting received events to the host

These are architectural possibilities consistent with a dedicated Z-Wave controller.

They are not a verified inventory of functions exposed by the specific firmware installed in this device.

### Important Distinction

The USB interface establishes a communication channel between the Linux host and the Z-Wave controller.

It does not, by itself, establish whether the host can:

- Read or replace the controller firmware
- Access all controller configuration
- Export complete network state
- Perform controller backup and restore
- Use every Z-Wave command class
- Operate the controller with arbitrary third-party software

Each capability requires separate verification.

## Serial API Considerations

Sigma Designs Z-Wave controllers commonly use a host-to-controller protocol known as the Z-Wave Serial API.

The observed USB identification is consistent with hardware used for this type of communication.

However, this investigation has not established the exact Serial API version, command set or controller capabilities of the installed unit.

### Research Questions

Further protocol-level inspection could determine:

1. Whether the controller exposes a standard Z-Wave Serial API implementation.
2. Which controller identification and capability commands are supported.
3. Which protocol and firmware versions are installed.
4. How the Telldus application initializes the controller.
5. How controller events are translated into application events.
6. Which controller-management operations are exposed by the stock firmware.

Until these are verified, compatibility with any particular third-party Z-Wave software stack should not be assumed.

## Controller Ownership and Serial Access

The stock Telldus application may maintain an active connection to the Z-Wave serial interface.

This matters when attempting independent inspection.

### Concurrent Access

Opening /dev/ttyACM1 from multiple applications can cause problems such as:

- Competing reads
- Unexpected consumption of controller responses
- Interrupted message sequences
- Application timeouts
- Conflicting controller operations

The interface should not be treated as a broadcast data stream that multiple applications can safely read independently.

### Safe Inspection Approach

For initial investigation, read-only system information is preferable to sending undocumented commands to the controller.

Commands that change Z-Wave network state, reset controller memory or modify inclusion information should be kept separate from basic interface identification.

## Read-Only Inspection Commands

The command blocks below are inspection examples, not captured session output.

The following commands can be used on a device with authorized Linux shell access.

### Confirm the Serial Device

```text
ls -l /dev/ttyACM1
```

### Inspect USB Enumeration

```text
dmesg | grep -i -E 'usb|cdc_acm|ttyACM'
```

### Inspect the Device’s Sysfs Information

```text
cat /sys/class/tty/ttyACM1/device/uevent
```

### Inspect USB Device Descriptors

If the utility is installed:

```text
lsusb
```

To inspect the identified controller:

```text
lsusb -d 0658:0200
```

### Inspect Driver Information

```text
ls -l /sys/class/tty/ttyACM1/device/driver
```

### Identify Processes Using the Interface

If supported by the installed userspace:

```text
fuser /dev/ttyACM1
```

These commands are intended for observation.

They do not deliberately send Z-Wave commands or modify controller state.

## Controller State and Network Data

Z-Wave controllers may retain network-specific information, depending on their hardware and firmware architecture.

Potentially sensitive data can include:

- Network identifiers
- Included-node information
- Controller configuration
- Security-related network material

The precise storage format and location on the examined controller have not been established.

### Publication Policy

No controller memory dump, security keys, complete network configuration or device-specific controller backup is included in this repository.

Any future protocol traces should be sanitized before publication.

This is particularly important when documenting security-enabled Z-Wave networks.

## Potential Independent Integration

The internal USB interface raises an interesting interoperability question:

Could the built-in Z-Wave controller be used independently of the original Telldus application?

The hardware architecture makes this a reasonable research direction.

However, successful integration would depend on several unresolved factors.

### Compatibility Requirements

An independent application would need to establish:

- The actual controller protocol
- Supported Serial API commands
- Controller firmware compatibility
- Correct initialization behavior
- Exclusive access to the serial interface
- Network-state preservation
- Compatibility with the desired Z-Wave software stack

The presence of /dev/ttyACM1 alone does not prove that a particular integration will work.

### Preservation of Existing Networks

Experiments involving controller initialization or replacement software should distinguish between read-only discovery and operations that could alter existing network state.

Controller resets, exclusions and network reinitialization may affect previously included devices.

No such destructive operation is required to establish the USB hardware identity.

## Firmware and Controller Update Research

The Z-Wave controller has its own firmware environment, distinct from the Atheros Linux operating system.

Updating the gateway’s Linux firmware does not necessarily imply that the Z-Wave controller firmware is updated through the same mechanism.

Possible research areas include:

- Controller firmware version reporting
- Controller bootloader identification
- Vendor-specific update mechanisms
- Firmware compatibility constraints
- Recovery capabilities
- Relationship between gateway updates and controller updates

No controller firmware update procedure has been verified in this research.

No third-party controller firmware images are distributed.

## Areas for Further Investigation

### Exact Controller Identification

Determine the controller’s precise hardware model and revision using verified physical markings or protocol-level identification.

### Serial API Compatibility

Establish whether the interface supports a standard Z-Wave Serial API implementation and identify its version.

### Application Protocol Analysis

Examine how the stock Telldus software initializes the controller, sends commands and processes responses.

### Controller Backup Support

Investigate whether supported controller-management interfaces provide a reliable backup mechanism without changing the active Z-Wave network.

### Independent Software Compatibility

Test interoperability with an alternative host software stack only after controller capabilities and network-state preservation requirements are understood.

### Hardware Signal Mapping

Identify the controller’s physical connections to the internal USB architecture and document the relevant PCB layout.

## Findings and Limitations

| Research area | Finding | Status |
| --- | --- | --- |
| Dedicated Z-Wave controller | Present | Confirmed |
| Manufacturer identification | Sigma Designs | Confirmed |
| USB vendor ID | 0658 | Observed |
| USB product ID | 0200 | Observed |
| Linux interface | /dev/ttyACM1 | Confirmed |
| USB driver | cdc_acm | Confirmed |
| Internal USB connection | Kernel enumeration | Confirmed |
| Separate RF433 controller | Present | Confirmed |
| Telldus application integration | Z-Wave adapter components | Identified |
| Exact controller chip | Not established | Further research |
| Controller firmware version | Not established | Further research |
| Serial API version | Not established | Further research |
| Complete supported command set | Not established | Further research |
| Controller backup support | Not established | Further research |
| Third-party software compatibility | Not tested | Unknown |
| Controller firmware replacement | Not tested | Unknown |
| Complete electrical schematic | Not available | Further research |

## Research Significance

The TellStick ZNet Lite V2 does not implement Z-Wave as a software-only function of its main Linux processor.

Instead, it contains a dedicated Sigma Designs controller connected through an internal USB serial interface.

This separation is significant because the controller may be technically capable of operating independently of the original gateway application, provided its protocol and firmware capabilities are compatible with the intended host software.

The available evidence establishes the physical and operating-system interface, but not full third-party compatibility.

The most valuable next step is controller identification and protocol-level characterization without altering the existing Z-Wave network.

## Conclusion

The TellStick ZNet Lite V2 exposes its internal Z-Wave controller through USB CDC ACM as /dev/ttyACM1.

The controller identifies with USB vendor and product IDs 0658:0200 and is associated with Sigma Designs Z-Wave hardware.

The stock Telldus application uses this dedicated controller as part of its radio subsystem architecture.

The confirmed discovery is the presence of an identifiable, separately connected Z-Wave controller. Its complete capabilities and interoperability with alternative software remain subjects for further investigation.

## Related Documentation

- [Hardware Architecture](hardware.md)
- [Firmware and Filesystem Analysis](firmware.md)
- [UART Console and U-Boot](uart-and-uboot.md)
- [RF433 Subsystem](rf433.md)
- [Undocumented Wi-Fi](undocumented-wifi.md)

## License and Disclaimer

This document contains independent research performed on personally owned hardware.

It is not affiliated with, sponsored by or endorsed by Telldus.

Original documentation is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0), unless otherwise noted.

Third-party firmware, proprietary source code, private credentials and device-specific network security material are not distributed.

Telldus and TellStick are trademarks of their respective owners.

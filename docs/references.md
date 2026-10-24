# Sources, prior work, and attribution

The primary source for the new offline findings is the official TellStick ZNet Lite V2 firmware **1.3.2**, obtained from [Telldus's firmware server](https://fw.telldus.com/tellstick-znet-lite-v2/tellstick-znet-lite-v2-1.3.2.bin). The analyzed download measured 12,386,308 bytes and SHA-256 `869495b7e3f5acb58f290c20ee58c9c60249d1be76a7230db077a6e93d0598ca`. The embedded build date also reported 1.3.2. No independent vendor signature was verified. Firmware, extracted root filesystem, bytecode, and device-specific data are not redistributed here.

The relevant firmware modules are named in [interfaces](interfaces.md), [authentication](authentication.md), and [testing](testing.md). Static analysis used extracted Python 2.7 bytecode and decompilation as a reading aid; behavior-sensitive conclusions were checked against original bytecode where possible. Decompiled output is not represented as vendor source code.

## Independent projects

- [ob-wn/tellstick-znet-lite-v2-nocloud](https://github.com/ob-wn/tellstick-znet-lite-v2-nocloud) documents local discovery, configuration-backup, and JWT research. The examined reference checkout was commit `8ace822` and is **Apache-2.0**. Its work informed comparisons; no code was copied into this publication.
- [R00S/addon-tellstick-local](https://github.com/R00S/addon-tellstick-local) implements a local Home Assistant integration for TellStick Net/ZNet RF433, including events, devices, and sensors subject to its documented limitations. The examined checkout was commit `0946a83` and is **GPL-3.0**. This repository does not copy that implementation.
- [Telldus's public source](https://github.com/telldus/telldus-server) was used as a secondary, readable cross-reference. The downloaded 1.3.2 firmware remained the evidence for the exact build studied here.

The wider hardware and firmware investigation predates the external port lead. In [issue #1](https://github.com/bobo843032/tellstick-znet-lite-v2-research/issues/1), `ob-wn` drew attention to UDP 30303. That specific tip prompted targeted analysis of the service and adjacent firmware code; it did not initiate the whole research project.

Original documentation in this repository is covered by the root [CC BY 4.0 license](../LICENSE), subject to its third-party exclusions. Independently authored prototype and test code has its own license; neither license grants rights to redistribute Telldus firmware or code from other projects.

# Security Policy

## Scope

This repository contains independent hardware, firmware, and security research concerning the Telldus TellStick ZNet Lite V2.

The research is conducted on personally owned hardware and is not affiliated with, sponsored by, or endorsed by Telldus.

This repository is not an official firmware distribution or security support channel.

## Reporting Security Vulnerabilities

If you discover a potential security vulnerability related to the research documented here, please avoid publishing sensitive exploitation details, credentials, private keys, or device-specific information in a public GitHub issue.

For vulnerabilities affecting Telldus products or infrastructure, contact the manufacturer through its official support or security reporting channels.

For issues involving this repository itself, such as accidentally exposed sensitive information or unsafe documentation, contact the repository maintainer privately through an available GitHub contact method.

If no private contact method is available, do not disclose secrets in a public issue.

## Research Principles

This project follows these principles:

- Research is performed on owned or explicitly authorized devices.
- Technical findings are documented accurately, with observations distinguished from hypotheses.
- No unauthorized access to third-party systems is performed or encouraged.
- Private credentials and cryptographic keys are not distributed.
- Device-specific calibration data and identifying information are excluded.
- Proprietary firmware images are not redistributed.
- Potential vulnerabilities are described with consideration for responsible disclosure.

## Embedded Credentials and Remote Support

The stock firmware contains remote-support components, including an embedded SSH private-key file.

The existence and architectural role of these components are documented for research purposes.

This repository does not publish the private key, authentication secrets, or instructions for accessing third-party infrastructure.

An embedded credential should not automatically be interpreted as an authentication bypass or proof of unauthorized access.

Security implications must be evaluated against verified behavior and actual trust boundaries.

## Firmware Modification

Firmware modification, bootloader operations, and direct flash access may permanently damage a device or erase device-specific information.

Users are responsible for understanding the risks of any experiments they perform.

No firmware images, flashing guarantees, or official recovery services are provided.

## Supported Versions

Research observations currently cover:

| Device | Firmware | Research status |
| --- | --- | --- |
| TellStick ZNet Lite V2 | 1.3.2 | Examined |
| Other firmware versions | Not verified | Unknown |
| Other hardware revisions | Not verified | Unknown |

The project does not provide security patches or ongoing vendor firmware maintenance.

## Disclaimer

All information is provided for educational, interoperability, and independent security research purposes.

Findings are based on the examined hardware and software versions and may not apply to other configurations.

The repository maintainers make no warranty regarding completeness, compatibility, or security.

Telldus and TellStick are trademarks of their respective owners.

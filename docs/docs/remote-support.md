Remote Support Architecture and Embedded SSH Key

Overview

The Telldus TellStick ZNet Lite V2 firmware contains a remote-support component that uses SSH to establish an outbound connection and provide remote access through reverse port forwarding.

The investigation identified an RSA private key distributed within the installed firmware filesystem, along with the Python package responsible for remote-support functionality.

Controlled experiments against a researcher-operated SSH endpoint reproduced the reverse-forwarding mechanism.

This document describes the observed architecture, the location and role of the embedded authentication material, the verification performed, and the associated security considerations.

The embedded SSH key is not a demonstrated authentication bypass of the gateway’s local SSH service.

1. Research Environment

Property	Observed value
Device	Telldus TellStick ZNet Lite V2
Examined firmware	1.3.2
Operating system	OpenWrt Designated Driver r49388
Linux kernel	4.1.23
Application runtime	Python 2.7
Remote-support package	Telldus-Remotesupport 0.1
Authentication material	RSA private key in PEM format
Transport	SSH
Remote access mechanism	Reverse TCP port forwarding
Verification endpoint	Researcher-controlled SSH server

The investigation was performed on personally owned hardware and a locally extracted firmware filesystem.

2. Discovery of the Remote-Support Package

Filesystem inspection identified a Python package named Telldus-Remotesupport.

The installed package metadata is located at:

/usr/lib/python2.7/site-packages/
    Telldus_Remotesupport-0.1-py2.7.egg-info/

The package inventory also references the following files:

/usr/lib/python2.7/site-packages/remotesupport/
    __init__.pyc
    RemoteSupport.pyc
    id_rsa

The main application startup configuration includes a remote-support component:

'remotesupport': ['RemoteSupport']

This establishes that remote support is integrated into the gateway’s Python application architecture rather than being an unrelated external utility.

Package entry point

The extracted package metadata contains:

c = remotesupport:RemoteSupport [creq]

The component therefore participates in the application’s Python package and initialization system.

3. Embedded RSA Private Key

The firmware filesystem contains a private-key file at:

/usr/lib/python2.7/site-packages/remotesupport/id_rsa

This location is part of the installed application package rather than a conventional per-user SSH directory.

Original filesystem evidence

The following file listing is reproduced from the examined filesystem:

usr/lib/python2.7/site-packages/remotesupport/RemoteSupport.pyc
usr/lib/python2.7/site-packages/remotesupport/id_rsa
usr/lib/python2.7/site-packages/remotesupport/__init__.pyc

The file identification command returned:

usr/lib/python2.7/site-packages/remotesupport/id_rsa: PEM RSA private key

Inspection of the file header confirmed the expected RSA private-key container format:

-----BEGIN RSA PRIVATE KEY-----
[PRIVATE KEY MATERIAL OMITTED]

The private-key contents are deliberately excluded from this repository.

Significance

An SSH private key included in a firmware filesystem is recoverable by a party who obtains sufficient access to that filesystem.

This differs from a private key generated uniquely on a device during initial setup and stored only on that device.

However, identifying an embedded key in one examined firmware image does not, by itself, establish whether the same key is present in every manufactured unit or firmware release.

The deployment scope of the key remains an important unanswered question.

4. Remote-Support Connection Architecture

The investigated mechanism uses an outbound SSH connection initiated by the gateway.

Instead of requiring an inbound connection directly to the gateway from the internet, the device connects to a remote SSH endpoint.

The SSH connection can then carry a reverse port forward back toward a local service on the gateway.

Logical connection flow

                  OUTBOUND CONNECTION
  TellStick ZNet Lite V2
  +--------------------------------+
  |                                |
  | RemoteSupport component        |
  |            |                   |
  |            v                   |
  | SSH client                     |
  |            |                   |
  | Embedded RSA authentication    |
  |            |                   |
  +------------|-------------------+
               |
               | SSH connection
               |
               v
  +--------------------------------+
  | Remote SSH endpoint            |
  |                                |
  | SSH authentication             |
  | Reverse forwarding listener    |
  +------------|-------------------+
               |
               | Forwarded TCP connection
               |
               v
  +--------------------------------+
  | TellStick local SSH service    |
  |                                |
  | Separate SSH authentication    |
  +--------------------------------+

The diagram represents the observed mechanism, not a complete specification of the manufacturer’s production support infrastructure.

5. How Reverse SSH Forwarding Works

Ordinary SSH typically allows a client to establish an encrypted connection to a remote SSH server.

SSH also supports TCP forwarding.

With reverse forwarding, the client requests that the remote SSH server make a listening endpoint available and forward accepted connections back through the existing encrypted session.

In the examined architecture, the TellStick acts as the SSH client.

The sequence is:

1. The remote-support component starts on the gateway.
2. An SSH client establishes an outbound connection.
3. The embedded private key is used as authentication material for that connection.
4. The client requests reverse TCP forwarding.
5. The remote SSH endpoint accepts forwarded connections according to its configuration and authorization rules.
6. Traffic is carried through the established SSH session to the gateway’s local SSH service.
7. The local SSH service applies its own authentication requirements.

The precise availability and reachability of the remote listener depend on the SSH server configuration.

For example, a reverse-forwarded listener may be restricted to the remote host’s loopback interface rather than exposed to other network clients.

A reverse tunnel creates a network path. It does not automatically grant an authenticated shell session on the destination device.

6. Authentication Boundaries

There are two separate SSH authentication contexts.

A. Gateway to remote-support server

The gateway establishes the outbound SSH connection.

The embedded RSA private key is associated with authentication of this connection.

Successful authentication depends on the remote server accepting the corresponding public key and any applicable account or forwarding restrictions.

B. Remote endpoint to gateway SSH service

Once a reverse forward is established, a connection can be carried to the gateway’s local SSH service.

That service has its own authentication configuration.

The private key used to establish the outbound support tunnel does not automatically authenticate a client to the gateway’s local SSH server.

These authentication boundaries are important when assessing the security impact of the embedded key.

7. Controlled Verification

The remote-support behavior was examined using a researcher-controlled SSH endpoint.

The experiment reproduced the relevant outbound SSH and reverse-forwarding behavior without relying on access to the manufacturer’s production support infrastructure.

Verified observations

* The installed filesystem contains the remote-support Python package.
* The package includes an RSA private-key file.
* The application startup configuration references the remote-support component.
* The investigated mechanism uses outbound SSH.
* Reverse TCP forwarding behavior was reproduced against a controlled endpoint.
* The forwarded connection remained subject to the destination SSH service’s authentication requirements.

What the experiment did not establish

The experiment did not demonstrate:

* Unauthorized access to a Telldus-operated SSH server.
* Access to another customer’s gateway.
* An authentication bypass of the gateway’s local SSH service.
* That every manufactured unit uses identical key material.
* That the remote-support endpoint is publicly reachable.
* That possession of the embedded key is sufficient to activate remote support on arbitrary devices.

These distinctions are necessary to avoid overstating the findings.

8. Security Considerations

8.1 Recoverable authentication material

The private key is stored in an application package within the firmware filesystem.

Anyone with sufficient access to the firmware contents may be able to recover the same material.

The security impact depends on what that key is authorized to do.

8.2 Potential credential reuse

If identical private-key material is distributed across multiple devices, compromise of one firmware image could expose authentication material shared by other installations.

This is a conditional risk.

The investigation has not conclusively established the extent of key reuse across devices or firmware releases.

8.3 Server-side restrictions

An SSH server can restrict what an authenticated key is allowed to do.

Relevant controls include:

* Restricting the account associated with the key.
* Limiting permitted forwarding destinations and listeners.
* Preventing interactive shell access.
* Restricting source addresses where practical.
* Monitoring support-session establishment.
* Revoking or rotating compromised credentials.

The effective risk cannot be determined from the presence of the private key alone.

8.4 Reverse forwarding and network exposure

Reverse forwarding can provide access to a device located behind NAT or a firewall without opening an inbound port on the local router.

This is a legitimate remote-support technique.

However, it also creates an access path whose security depends on authentication, server policy, forwarding restrictions and operational controls.

8.5 Local SSH authentication

The gateway’s SSH service remains a separate security boundary.

The observed forwarding mechanism should not be described as a root-login bypass.

9. Recommended Security Design

For embedded remote-support implementations, the following design properties reduce the impact of credential exposure:

Unique device credentials

Generate separate credentials for individual devices rather than embedding a shared private key in a common firmware image.

Restricted server authorization

Grant remote-support identities only the permissions required to establish approved support sessions.

Controlled forwarding

Restrict listening interfaces, ports and forwarding destinations.

Credential revocation

Provide a practical mechanism to revoke and rotate authentication material.

Explicit support-session lifecycle

Make support access time-limited, auditable and subject to appropriate authorization.

Independent destination authentication

Preserve authentication at the final destination service even when a forwarding tunnel has already been established.

These are general security recommendations, not claims that the examined firmware implements or omits every listed control.

10. Evidence Handling and Publication

The investigation distinguishes between technical observations and sensitive authentication material.

The following information may be documented:

* Installed package names
* Relevant filesystem paths
* File formats
* Component relationships
* Connection direction
* SSH forwarding architecture
* Results of controlled experiments
* Security boundaries and limitations

The following material is intentionally excluded:

* RSA private-key contents
* Authentication credentials
* Device-specific secrets
* Operational third-party support endpoint details
* Reusable authenticated connection configurations
* Unmodified firmware images containing sensitive material

Sanitized evidence should preserve the original technical meaning without exposing usable credentials.

11. Findings Summary

Finding	Evidence	Status
Remote-support Python package exists	Installed package metadata	Confirmed
Application references remote support	Startup configuration	Confirmed
Embedded RSA private-key file exists	Filesystem listing and file identification	Confirmed
Private key is stored in firmware filesystem	Extracted filesystem inspection	Confirmed
Outbound SSH support mechanism	Implementation investigation	Investigated
Reverse TCP forwarding	Controlled SSH experiment	Reproduced
Separate local SSH authentication	Controlled test and protocol behavior	Confirmed for tested configuration
Key reuse across all devices	Not established	Unknown
Access to production support infrastructure	Not tested	Not claimed
Authentication bypass	Not demonstrated	Not established

12. Conclusion

The examined TellStick ZNet Lite V2 firmware contains a Python-based remote-support component with an embedded RSA private key.

The support architecture uses an outbound SSH connection and reverse TCP forwarding to provide a path toward a local service on the gateway.

The embedded authentication material can be identified in the firmware filesystem, and the reverse-forwarding mechanism was reproduced in a controlled test environment.

The primary security concern is the presence of recoverable private authentication material in distributed firmware, particularly if credentials are reused or granted broad server-side permissions.

However, the local evidence does not establish the key’s complete deployment scope, the manufacturer’s server-side authorization policies, or access to arbitrary devices.

The observed mechanism provides remote connectivity, not an independently demonstrated bypass of the gateway’s SSH authentication.

⸻

References

* Telldus GitHub organization
* tellstick-server
* tellstick-server-plugins
* OpenSSH manual pages

License and Disclaimer

This is independent research performed on personally owned hardware.

The document is not affiliated with or endorsed by Telldus.

Original documentation is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0), unless otherwise noted.

No private keys, usable authentication credentials, proprietary firmware images or device-specific secrets are distributed.

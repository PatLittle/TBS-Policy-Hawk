# Improving GC Cyber Security Health: Security Policy Implementation Notice

- Notice source: Security Policy Implementation Notice (SPIN)
- Source page URL: https://www.canada.ca/en/government/system/digital-government/policies-standards/spin.html
- Source page modified: 2025-10-09
- Notice URL: https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/improving-gc-cyber-security-health.html
- Notice modified: 2024-08-14
- Notice identifier: 2024-01
- Listed date: 2024-08-14
- Captured at (UTC): 2026-07-18T01:28:35Z

---

# Improving GC Cyber Security Health: Security Policy Implementation Notice

## 1. Effective date

This Security Policy Implementation Notice (SPIN) is effective as of August 14, 2024.

## 2. Purpose

The purpose of this SPIN is to reinforce requirements under the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578) and the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603) in order to:

- reduce the overall attack surface and minimize the risk of unauthorized access to GC information systems as soon as possible
- aggressively remediate known exploited vulnerabilities to protect federal information systems and reduce cyber incidents
- make measurable progress toward enhancing visibility into departmental assets and associated vulnerabilities

## 3. Scope

This SPIN applies to any Government of Canada (GC) information system (departmental or enterprise), that collects, processes, stores, transmits, disseminates or otherwise maintains GC information and data. This includes, but is not limited to:

- servers and workstations, virtual machines, routers and switches, firewalls, network appliances, and network printers — whether in on-premises, roaming or cloud-based environments
- all software and hardware found on federal information systems managed on-premises or in GC-managed cloud-based environments
- all IP-addressable networked assets that can be reached over IPv4 and IPv6 protocols

The scope excludes ephemeral assets, such as containers and third party-managed software as a service (SaaS) solutions.

## 4. Application

This SPIN applies to the organizations listed in section 6 of the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578).

## 5. Context

The GC, like all other government and private sector organizations around the world, faces a dynamic and challenging cyber threat environment. These threats can exploit vulnerabilities and improperly configured network devices or can use activities such as phishing to gain access to government information. Inadequate security, misconfigurations and out-of-date software of Internet-accessible assets make network security devices more vulnerable to exploitation. The risk is further compounded if device management interfaces are connected directly to and accessible from the public-facing internet.

Given the increasing sophistication and frequency of cyber attacks, now more than ever the GC must be cyber vigilant. Recent cyber incidents serve as a reminder that cyber security is a shared responsibility across the GC. Without proper cyber security measures, departments and agencies are vulnerable and at risk of compromise.

All departments and agencies play a critical role in ensuring the confidentiality, integrity and availability of the GC’s information and networks.

According to the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611), deputy heads have a duty and responsibility to ensure the protection of information systems under their organization’s custody and/or control. These responsibilities include:

- safeguarding the confidentiality, integrity and availability of GC information and information technology (IT) assets
- implementing appropriate measures to assure the protection of personal information

As the GC’s common IT service provider, Shared Services Canada (SSC) is mandated to provide secure, reliable IT services to its partner clients. Within this shared responsibility model, there are interdependencies between SSC infrastructure and the applications that are delivered by departmental programs and services.

Collaboration across departments and agencies will be essential in improving cyber security and resilience for the GC.

## 6. Direction

To improve the cyber security health of federal information systems, the GC must continue to take deliberate steps to ensure the security of IT assets across the federal enterprise. As per Appendix B of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611), and to ensure that cyber security risks to the GC are reduced according to section 4.4.1.9 of the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603), departments and agencies will:

- assess threats to information systems that support departmental activities, hold departmental information, or hold information under the custody or control of the department (section B.2.2.1 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611))
- manage the configuration of information systems to maintain known and approved system and component designs, settings, parameters and attributes (section B.2.3.3 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611))
- implement measures to protect information systems, their components and the information they process and transmit (section B.2.3.7 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611))

The following subsections outline required actions on GC information systems in scope of this SPIN.

### 6.1 Identify assets

Continuous and comprehensive asset visibility, along with the monitoring of these assets, is critical to the understanding and effective management of cyber security risks to the GC enterprise network.

#### Within 3 months of issuance, departments and agencies will:

- 6.1.1 review departmental records of information systems that support departmental critical services and activities in the TBS Office of the Chief Information Officer (OCIO)’s [Application Portfolio Management (APM) tool](https://tbs-clarity.ssc-spc.gc.ca/niku/nu#action:homeActionId) or comparable tool and update as appropriate
- 6.1.2 confirm whether the Canadian Centre for Cyber Security (Cyber Centre)’s host-based sensors have been deployed on all client endpoints (laptops, desktops) (section 1.5.1 of the [Endpoint Management Configuration Requirements](https://www.canada.ca/en/government/system/digital-government/policies-standards/enterprise-it-service-common-configurations/endpoint.html)). If they have not been implemented, contact Cyber Centre’s [Cyber Defence Operations (CDO) Service Deployments](mailto:CDOServiceDeployments@cyber.gc.ca) for support
- 6.1.3 confirm whether Cyber Centre’s cloud-based sensors have been deployed according to the [Government of Canada Cloud Guardrails](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32787). If they have not been implemented, contact Cyber Centre’s [CDO Service Deployments](mailto:CDOServiceDeployments@cyber.gc.ca) for support

### 6.2 Understand exposure

Understanding the security exposure of assets enables a risk-based approach for prioritization of mitigation measures.

#### Within 6 months of issuance, departments and agencies will:

- 6.2.1 for departments that do not receive network services from SSC, develop a plan to identify and assess network devices under their management to ensure that they are securely configured and hardened (for example, disabling access to network device management interfaces from the Internet), leveraging SSC hardening standards or industry best practices such as the [Center for Internet Security (CIS) Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- 6.2.2 develop a plan to identify, assess and remediate applicable vulnerabilities from the Top 25 Vulnerabilities List that has been developed by TBS, in collaboration with the Cyber Centre and SSC, following a risk-based approach with priority given to information systems that are publicly accessible
- 6.2.3 develop an emergency patch management plan that will ensure that departmental procedures are in place, with clear roles and responsibilities outlined to support the execution of emergency patches to address critical vulnerabilities, in accordance with the [GC Patch Management Guidance](https://www.canada.ca/en/government/system/digital-government/online-security-privacy/patch-management-guidance.html), and in consideration of the SSC [Patch Management Standard](https://service.ssc-spc.gc.ca/en/page/patch-management-standard)
- 6.2.4 onboard departmental publicly accessible systems into Cyber Centre’s National Cyber Threat Notification System, in collaboration with TBS and Cyber Centre, to ensure that departments are notified of misconfigured services, vulnerabilities and compromised infrastructure on their IP space

#### Within 6 months of issuance, SSC will:

- 6.2.5 develop a plan to identify and assess network devices under their management to ensure that they are securely configured and hardened (for example, disabling access to network device management interfaces from the Internet, forwarding events to a central log facility), leveraging SSC hardening standards or industry best practices such as the [Center for Internet Security (CIS) Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- 6.2.6 develop a plan to identify, assess and remediate applicable vulnerabilities from the Top 25 Vulnerabilities List that has been developed by TBS, in collaboration with the Cyber Centre and SSC, with priority given to SSC-managed infrastructure that poses the greatest risk

### 6.3 Reduce exposure

Reduce the GC’s overall attack surface and strengthen safeguards to minimize the risk of unauthorized access to federal information systems.

#### Within 9 months of issuance, departments and agencies will:

- 6.3.1 for departments not receiving network services from SSC, implement mitigations based on the action plan developed in section 6.2.1 to address non-compliant perimeter network devices to ensure that they are securely hardened and configured with a priority on devices at the edge of the GC’s enterprise network
- 6.3.2 implement mitigations to address the applicable vulnerabilities from the Top 25 Vulnerabilities List based on the action plan developed in section 6.2.2 with a priority focus on information systems that are publicly accessible
- 6.3.3 employ secure remote access configurations that:
- 6.3.3.1 enforce multifactor authentication (section 2.1 of the [Remote Access Configuration Requirements](https://www.canada.ca/en/government/system/digital-government/policies-standards/enterprise-it-service-common-configurations/remote-access.html)) with security measures in place to achieve phishing resistance for the overall authentication process, such as ensuring that the user is authenticating from a GC-managed device, verifying the device is configured properly, and detecting anomalous geolocations according to the guidance from the Cyber Centre’s “User authentication guidance for information technology systems” (ITSP.30.031 v3)
- 6.3.3.2 provide a secure, encrypted connection to the GC enterprise network (section 3.1 of the [Remote Access Configuration Requirements](https://www.canada.ca/en/government/system/digital-government/policies-standards/enterprise-it-service-common-configurations/remote-access.html)) using GC-approved pathways to the Internet rather than via a direct connection to the Internet, in order to leverage the Cyber Centre’s cyber defences (section 3.2 of the [Remote Access Configuration Requirements](https://www.canada.ca/en/government/system/digital-government/policies-standards/enterprise-it-service-common-configurations/remote-access.html)) with the exception of domains that are included in the split tunneling list approved by GC Enterprise Architecture Review Board (section 1.4 of the [Endpoint Management Configuration Requirements](https://www.canada.ca/en/government/system/digital-government/policies-standards/enterprise-it-service-common-configurations/endpoint.html))

## 7. Compliance monitoring

For an outline of the consequences of non‑compliance, refer to the [Framework for Management of Compliance](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=17151) (Appendix C: Consequences for Institutions and Appendix D: Consequences for Individuals).

TBS will perform active cyber verification of the GC’s perimeter and publicly accessible systems to ensure that potentially exposed devices and interfaces are identified and evaluated for potential vulnerabilities and remediated as appropriate by departments.

TBS will monitor departmental progress and will engage departmental senior officials, such as the chief information officer (CIO), chief security officer (CSO), and designated official for cyber security (DOCS), as necessary and appropriate, when the department has not met the direction (required actions) deadlines specified above.

SSC will provide periodic updates to the IT Security Tripartite on progress at remediating the Top 25 Vulnerabilities List and non-compliant perimeter network devices under their management, along with the associated implementation status of their plans.

## 8. Enquiries

For additional information or clarification regarding this SPIN, address enquiries to:

[TBS Cyber Security](mailto:%20zztbscybers@tbs-sct.gc.ca)

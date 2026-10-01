# Direction on Government of Canada Cyber Security Readiness in the Frontier Artificial Intelligence Era: Security Policy Implementation Notice

- Notice source: Security Policy Implementation Notice (SPIN)
- Source page URL: https://www.canada.ca/en/government/system/digital-government/policies-standards/spin.html
- Source page modified: 2026-10-01
- Notice URL: https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/direction-government-canada-cyber-security-readiness-frontier-artificial-intelligence-era.html
- Notice modified: 2026-10-01
- Notice identifier: 2026-01
- Listed date: 2026-10-01
- Captured at (UTC): 2026-10-01T20:44:16Z

---

# Direction on Government of Canada Cyber Security Readiness in the Frontier Artificial Intelligence Era: Security Policy Implementation Notice

## 1. Effective date

This Security Policy Implementation Notice (SPIN) is effective as of October 1, 2026.

## 2. Purpose

The purpose of this SPIN is to reinforce requirements under the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578) and the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603) in order to ensure that departments and agencies:

- apply baseline cyber security controls consistently to protect Government of Canada (GC) information systems and services in the frontier artificial intelligence (AI) era
- identify and remediate material gaps that could be exploited by AI-enabled threat actors
- operate under an “assume breach” paradigm, ensuring rapid containment, blast-radius limitation, and swift recovery during cyber security events

## 3. Scope

The scope of this SPIN includes:

- servers and workstations, virtual machines, mobile devices, mainframes, high-performance computing environments, routers and switches, firewalls, network appliances, Internet of things devices, network- or Wi-Fi–connected laboratory equipment and network printers—whether in on-premises, roaming or cloud-based environments
- all software and hardware found on federal information systems managed on premises or in GC-managed cloud-based environments
- all IP-addressable networked assets that can be reached over IPv4 or IPv6 protocols

## 4. Application

This SPIN applies to the organizations listed in section 6 of the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578).

## 5. Context

The GC, like all other government and private sector organizations around the world, faces ongoing cyber threats. These threats often arise from a range of weaknesses across systems, networks, cloud services, user access, configurations, and external dependencies, which are now being found easier and faster due to advances in AI.

As highlighted in the Canadian Centre for Cyber Security’s [Frontier AI guidance](https://www.cyber.gc.ca/en/guidance/frontier-artificial-intelligence-itsap10050), advances in frontier models are significantly increasing cyber risks. Frontier AI technologies can enable more powerful automation, reasoning and decision-making than previous generations of AI. They can perform autonomous vulnerability discovery, zero-day vulnerability exploit generation and multistage cyber attack orchestration at unprecedented speed and scale.

Frontier AI increases the risks posed by known vulnerabilities, legacy systems, weak cyber hygiene, and unknown or unmanaged assets, while accelerating exploitation and amplifying the consequences across GC environments. The [Five Eyes](https://www.cyber.gc.ca/en/news-events/five-eyes-cyber-security-agencies-statement-ai-shift-cyber-risk-why-leaders-must-act-now) have highlighted that the rapid pace of frontier AI development means cyber risk assumptions can become outdated in months, not years, requiring action now to be prepared to adapt and withstand evolving threats.

To that end, to ensure that the GC is prepared for this evolving threat environment, sustained attention and prioritization at the highest levels are required to achieve the following outcomes:

- Enable the department to continue delivering its mission effectively and securely by focusing on remediating or reducing cyber risk to acceptable levels
- Reduce the potential for exploitation in a more timely and cost-effective manner than reacting to an incident after an exploitation has occurred
- Support better decision-making by aligning risk management efforts and resources to the areas of greater impact

All departments and agencies play a critical role in ensuring the confidentiality, integrity and availability of the GC’s information and networks. Reducing risk requires sustained focus on preparation, speed, resilience and cyber hygiene. Strong cyber security fundamentals—good cyber hygiene, preparation, speed and resilience—are essential to reduce risk, including from AI-enabled threats, and to keep critical services for Canadians available and quickly restored when key systems or trusted IT services are disrupted or compromised.

Under the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578) and [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603), deputy heads are responsible for:

- safeguarding the confidentiality, integrity and availability of GC information and information technology (IT) assets (section B.2.3.7 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611#claB.2.3.7))
- implementing appropriate measures to ensure the protection of personal information (section 4.1.19 of the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603#cla4.1.19))

As the GC’s common IT service provider, Shared Services Canada (SSC) is mandated to provide secure, reliable IT services to its partner clients. Within this shared responsibility model, there are interdependencies between SSC infrastructure and the applications that are delivered by departmental programs and services. Collaboration across departments and agencies will be essential in strengthening cyber security defences and resilience for the GC.

## 6. Direction

To improve the cyber security defences of federal information systems in an AI-enabled cyber threat landscape, the GC must continue to take deliberate steps to ensure the security of IT assets across the federal enterprise.

According to Appendix B of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611), and to ensure that cyber security risks to the GC are reduced according to section 4.4.17 of the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603), departments and agencies will:

- assess threats to information systems that support departmental activities, hold departmental information, or hold information under the custody or control of the department (section B.2.2.1 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611))
- manage the configuration of information systems to maintain known and approved system and component designs, settings, parameters and attributes (section B.2.3.3 of the Directive on Security Management)
- implement measures to protect information systems, their components and the information they process and transmit (section B.2.3.7 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611#claB.2.3.7)) including configurations specified in [Appendix G: Standard on Enterprise Information Technology Service Common Configurations](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32713)
- ensure that technologies deployed are current and risks and vulnerabilities are addressed in accordance with [Appendix H: Standard on At-Risk Information Technology](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32714)

The following subsections outline the required actions on the GC information systems in the scope of this SPIN with a priority focus on departmental critical services. The implementation approach is outlined in section 7 of this document.

### 6.1 IDENTIFY – Identify critical services and maintain up-to-date asset inventory

To effectively defend against machine-speed, AI-driven threats, departments and agencies must have comprehensive visibility into their attack surface and a clear understanding of their most critical assets. Because threat actors scan and exploit Internet-facing vulnerabilities indiscriminately, and then move laterally toward high-value data, departments and agencies must prioritize what they defend. To establish this foundation, departments and agencies are expected to:

| IDT-1 | Review departmental critical services and the information systems that support them, and prioritize them based on how severe the impact would be (operational, legal, financial, or reputational) if they were compromised (based on section 7). Submit a prioritized list in TBS’s Enterprise Portfolio Management (EPM) tool by November 30, 2026, to support central prioritization and SSC planning. |
| --- | --- |
| IDT-2 | Keep an up‑to‑date inventory of all applications supporting critical services (for example, system owner, software versions) in the TBS Application Portfolio Management (APM) Tool. Where possible, link this inventory to asset data stores such as SSC’s Operational Data Store (ODS). |
| IDT-3 | Maintain an up‑to‑date architecture diagram that shows each critical service, the systems that support it, and key components (edge devices, internal network segments, identity systems, management interfaces, and administrative pathways). Use this diagram to map likely attack paths, including AI‑enabled lateral movement, after a compromise and to focus monitoring, detection and containment. |
| IDT-4 | Maintain a complete list of all Internet connections including SSC Local Internet Access Service (LIAS) lines, public-facing IP addresses (where available), subnets and sub-domains. Provide this list (and subsequent updates) to the Canadian Centre for Cyber Security’s National Cyber Threat Notification System to increase visibility of external threat surfaces. |
| IDT-5 | Maintain a Software Bill of Materials (SBOM) for department-developed software that supports critical services. Use it to track and update software dependencies and improve supply chain visibility, following the Canadian Centre for Cyber Security’s guidance on the [Minimum Elements for a SBOM](https://www.cisa.gov/resources-tools/resources/2026-minimum-elements-software-bill-materials-sbom). |
| IDT-6 | Improve endpoint management, asset visibility and rogue device detection by onboarding to SSC's Endpoint Visibility and Awareness (EVA) solution, prioritizing endpoints that support critical services. |

### 6.2 ACCELERATE – Accelerate patch management and vulnerability response

Frontier AI collapses the window between vulnerability disclosure and exploitation. It has also demonstrated the ability to chain lower-severity flaws into critical-impact exploit chains. To reduce the time between critical vulnerability disclosures, assessments and deployment of remediation measures, departments and agencies are expected to:

| ACC-1 | Regularly review, triage and act on relevant security alerts from software and hardware vendors; the Canadian Centre for Cyber Security, including the National Cyber Threat Notification System (NCTNS); and central GC exposure tools and findings. |
| --- | --- |
| ACC-2 | Establish and operate a risk‑based vulnerability and patch management process aligned with the [GC Guideline on Vulnerability Management](https://www.canada.ca/en/government/system/digital-government/online-security-privacy/cyber-security-guidance-policy/guideline-vulnerability-management.html) and the GC’s [Patch Management Guidance](https://www.canada.ca/en/government/system/digital-government/online-security-privacy/cyber-security-guidance-policy/patch-management-guidance.html) to fix vulnerabilities within GC recommended time frames, with faster patching for critical, Internet‑facing and other high‑risk systems. This includes: using the [GC Vulnerability Listing](https://gcxgce.sharepoint.com/teams/1000419/PD/Vulnerability%20Management/GC%20Vulnerability%20Listing.xlsx?web=1) (accessible only on the Government of Canada network) to prioritize work based on exposure, likelihood of exploit, impact and effort to fix setting faster targets and shorter testing cycles for the highest‑risk vulnerabilities and systems using compensating controls when timely patching is not feasible replacing, isolating or retiring unsupported and deprecated technology that cannot be patched or adequately secured, aligned with the [GC Guideline on Managing Risks with End-of-Life IT](https://gcxgce.sharepoint.com/teams/1000913/SitePages/Guide-of-End-of-Life-IT.aspx?xsdata=MDV8MDJ8R3JlZy5CZWxsQHRicy1zY3QuZ2MuY2F8YTI5ZjlhOTAxYThiNDZmZjk0MDkwOGRmMWZjMjVlOGV8NjM5N2RmMTA0NTk1NDA0NzljNGYwMzMxMTI4MjE1MmJ8MHwwfDYzOTI2NDU5MTgwMzI3NTA3MHxVbmtub3dufFRXRnBiR1pzYjNkOGV5SkZiWEIwZVUxaGNHa2lPblJ5ZFdVc0lsWWlPaUl3TGpBdU1EQXdNQ0lzSWxBaU9pSlhhVzR6TWlJc0lrRk9Jam9pVFdGcGJDSXNJbGRVSWpveWZRPT18MHx8fA%3d%3d&sdata=YW1GOUFzWWluSzJTcDJwOVNjN1lVYit5R1ZScWpFM29QZ3diZUh0Uy9WYz0%3d&clickparams=eyAiWC1BcHBOYW1lIiA6ICJNaWNyb3NvZnQgT3V0bG9vayIsICJYLUFwcFZlcnNpb24iIDogIjE2LjAuMjAzMjYuMjAxNDIiLCAiT1MiIDogIldpbmRvd3MiIH0%3d&SafelinksUrl=https%3a%2f%2fgcxgce.sharepoint.com%2fteams%2f1000913%2fSitePages%2fGuide-of-End-of-Life-IT.aspx) (accessible only on the Government of Canada network) tracking remediation progress using GC tools, such as the Canadian Centre for Cyber Security’s Observation Deck and SSC’s Self-Serve Vulnerability Analysis Portal, and documenting decisions when fixes are delayed |
| ACC-3 | Use defensive AI models and AI security tools in a safe, secure and responsible way, to help find vulnerabilities and to review and analyze software code for security issues. |

### 6.3 HARDEN – Harden identity controls and limit exposures

Threat actors increasingly target identities as a primary path for access, using sophisticated AI-enabled phishing, vishing, helpdesk impersonation, credential theft, and account compromise to gain entry and move laterally. To protect and prevent unauthorized access of user, administrative, privileged and non-person identities, including those associated with AI agent accounts, departments and agencies are expected to:

| HRD-1 | Turn on and enforce multi-factor authentication (MFA) for all user accounts. Use phishing-resistant MFA (for example, security keys) for administrative, privileged and other high-risk accounts, following the [GC Guideline on Multi-Factor Authentication](https://www.canada.ca/en/government/system/digital-government/guideline-multi-factor-authentication.html). |
| --- | --- |
| HRD-2 | Set and enforce password protection policies and tools that block weak, common, and known‑compromised passwords. Keep these protections up to date using centralized threat intelligence and automated tools. |
| HRD-3 | Enforce least privilege access so users have only the access they need to do their job. Regularly review and audit access, prioritizing accounts that administer critical services. |
| HRD-4 | Use centralized authentication and single sign-on (SSO) as the default approach to sign in to internal government systems. Where centralized authentication or SSO is not available, use an enterprise-grade password manager, following the GC [Guideline on Password Managers](https://gcxgce.sharepoint.com/teams/1000419/SitePages/ICAM.aspx?xsdata=MDV8MDJ8R3JlZy5CZWxsQHRicy1zY3QuZ2MuY2F8Nzc0NjhhMWI2NTQ2NGMxZGU0ZGUwOGRmMWU0YzhmMTF8NjM5N2RmMTA0NTk1NDA0NzljNGYwMzMxMTI4MjE1MmJ8MHwwfDYzOTI2Mjk4NjMzNTQxMzUwOHxVbmtub3dufFRXRnBiR1pzYjNkOGV5SkZiWEIwZVUxaGNHa2lPblJ5ZFdVc0lsWWlPaUl3TGpBdU1EQXdNQ0lzSWxBaU9pSlhhVzR6TWlJc0lrRk9Jam9pVFdGcGJDSXNJbGRVSWpveWZRPT18MHx8fA==&sdata=ZldpajRUZHc0UnZTeGRMdXc3bG5rQ2NySXJocW9JTHFKK1J1TkszcDlXYz0=&clickparams=eyAiWC1BcHBOYW1lIiA6ICJNaWNyb3NvZnQgT3V0bG9vayIsICJYLUFwcFZlcnNpb24iIDogIjE2LjAuMjAzMjYuMjAxNDIiLCAiT1MiIDogIldpbmRvd3MiIH0=&SafelinksUrl=https://gcxgce.sharepoint.com/teams/1000419/SitePages/ICAM.aspx). |
| HRD-5 | Use dedicated administrative accounts only for administrative tasks (for example, no email or general web browsing) and protect them with a centrally managed Privileged Access Management (PAM) solution that provides “just-in-time” auditable elevation of privileges. Where PAM is not yet available, use an enterprise-grade password manager as a temporary measure. |
| HRD-6 | Manage non‑person entities (NPE) (such as service accounts, service principals, machine identities and AI agents) with clear ownership, documented business purpose, life cycle management and regular privilege reviews, minimizing always‑on access and static credentials. |
| HRD-7 | Use centrally managed identity threat detection and response (ITDR) tools to continuously find and reduce identity‑based attack paths that enable unauthorized access and lateral movement, including AI‑enabled attacks, and act on the results to improve controls for critical services and privileged accounts. |
| HRD-8 | Regularly update departmental cyber security awareness and simulation programs to address AI‑enabled phishing, vishing, deepfakes and helpdesk impersonation, with targeted exercises for personnel who support critical services or occupy other high‑risk roles. |

### 6.4 FORTIFY – Implement layered, defence-in-depth architectures

Operating under an “assume breach” mindset[Footnote 1](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/direction-government-canada-cyber-security-readiness-frontier-artificial-intelligence-era.html#fn1) treats compromises as a normal operating condition, rather than an exceptional failure. To limit lateral movement and reduce the blast radius of AI-driven attacks, departments and agencies are expected to:

| FTY-1 | Lock down edge devices,[Footnote 2](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/direction-government-canada-cyber-security-readiness-frontier-artificial-intelligence-era.html#fn2) remote access, administrative interfaces, Internet-facing services, and APIs to only essential functions, and keep them free of unnecessary software, services and components, following the Canadian Centre for Cyber Security’s [hardening guidance.](https://www.cyber.gc.ca/en/guidance/top-10-security-actions-number-4-harden-operating-systems-and-applications-itsm10090) |
| --- | --- |
| FTY-2 | Tightly control vendor remote access to department-operated information systems that support critical services by keeping an up‑to‑date inventory of vendor access, using only approved access methods, limiting access by time or task (for example, just-in-time access), logging and monitoring sessions, and quickly removing access that is no longer needed or is dormant. |
| FTY-3 | Deploy information systems that support critical services in network zones that are segmented in accordance with the Canadian Centre for Cyber Security’s [Baseline security requirements for network security zones (version 2.0): ITSP.80.022](https://www.cyber.gc.ca/en/guidance/baseline-security-requirements-network-security-zones-version-20-itsp80022) and [Network Security Zoning: Design considerations for placement of services within zones (ITSG-38)](https://www.cyber.gc.ca/en/guidance/network-security-zoning-design-considerations-placement-services-within-zones-itsg-38) or equivalent controls. |
| FTY-4 | In environments that host critical services, block outbound Internet traffic by default and allow only explicitly approved connections. |
| FTY-5 | Protect administrative activities and pathways by performing all authorized administrative work only from GC‑approved hardened endpoints (for example, Dedicated Administrator Workstations (DAWs)) over designated, protected, and closely monitored administrative channels that are isolated from lower‑trust environments. |

### 6.5 MONITOR – Strengthen event logging and monitoring

Maintaining visibility across enterprise systems is essential to identifying malicious activity early, understanding the scope of compromise, and enabling timely containment. Deception trip wires can provide low-cost, high-fidelity alerts to adversarial activity. To improve the ability to detect and identify anomalous behaviours, accounting for anticipated dwell time, departments and agencies are expected to:

| MTR-1 | Set up logging according to the GC’s [Event Logging Guidance](https://www.canada.ca/en/government/system/digital-government/online-security-privacy/cyber-security-guidance-policy/event-logging-guidance.html), focusing first on information systems that support critical services, to enable visibility end-to-end across endpoints, identity, cloud and edge devices. |
| --- | --- |
| MTR-2 | Protect event logs from tampering using the Canadian Centre for Cyber Security’s approved [cryptographic safeguards](https://www.cyber.gc.ca/en/guidance/cryptographic-algorithms-unclassified-protected-protected-b-information-itsp40111) and forward them to a central logging facility for storage, monitoring and analysis. |
| MTR-3 | For endpoints that support critical services and administrative functions, deploy centrally managed endpoint detection and response (EDR/XDR) capabilities integrated with departmental logging and monitoring. |

### 6.6 PREPARE – Test cyber security event response, containment and recovery readiness

Conducting structured exercises ensures that organizations can perform with precision and resilience during critical events. To ensure effective response to cyber incidents, departments and agencies are expected to:

| PRP-1 | Keep the departmental cyber security event management plan (CSEMP) up to date so that it clearly shows who has authority; how escalation works during a cyber event; and how roles, responsibilities and processes align with the departmental business continuity plan (BCP).[Footnote 3](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/direction-government-canada-cyber-security-readiness-frontier-artificial-intelligence-era.html#fn3) |
| --- | --- |
| PRP-2 | Run regular cyber simulation (tabletop) exercises to confirm that the departmental CSEMP works in practice and remains aligned with the departmental BCP. |
| PRP-3 | Develop, approve and maintain incident response playbooks for key scenarios that support fast action with clear decision steps, service levels and escalation paths, pre-approved containment actions (for example, blocking malicious traffic, isolating compromised hosts or identities), and procedures to capture the telemetry (such as logs, system images) needed for forensic analysis. |
| PRP-4 | Regularly test restoring from backups for systems that support critical services and verify the restored data against a known good reference to confirm its integrity. |
| PRP-5 | Ensure that backups for information systems supporting critical services are logically separated from production environments and, where feasible, use immutable or write‑once storage. Protect backup environments with appropriate access controls and monitoring to reduce the risk that they are compromised during an attack. |

## 7. Implementation approach

Departments and agencies remain responsible for implementing all applicable cyber security requirements according to the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578) and the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603). The SPIN does not replace these obligations; it is established to help organizations prioritize key actions and investments in response to the evolving cyber threat environment.

Implementation of the SPIN is expected to follow a risk-informed and phased approach, leveraging common solutions where available, starting with a small number of the highest-priority systems first, then expanding implementation across the organization over time. This phased approach is meant to reduce risk quickly for the most important services.

### 7.1 Identify and categorize critical services

To ensure that the GC demonstrates meaningful risk reduction for the services that matter most to Canadians, departments and agencies are expected to begin with a rapid identification of their most critical services and associated information systems (for example, applications, infrastructure, devices, integrations and data) that support them (that is, the “crown jewels”). The department’s critical services inventory should be leveraged as the starting point for developing a refined priority list.

Where a department does not have the capacity to implement the SPIN actions for all of their critical services at the same time, it is recommended that departments and agencies group their critical services into two categories, as set out in the table below.

Descriptions of the critical service categories

| Category | Description |
| --- | --- |
| Category 1 (C1) – Initial Critical Services Scope | Focus first on no more than three of the highest‑priority critical services for the department. |
| Category 2 (C2) – Remaining Departmental Critical Services | Expand the same approach, tools and patterns used for C1 to all remaining critical services until full critical services coverage is achieved. |

### 7.2 Enterprise prioritization

Departments and agencies are expected to submit the prioritized list of critical services to TBS, based on IDT-1 in section 6 of this document.

This will enable TBS, in collaboration with Shared Services Canada (SSC) and the Canadian Centre for Cyber Security, to establish government-wide priorities for SPIN implementation and SSC support, based on cyber risk, dependencies and delivery capacity.

This will support joint planning and reporting across TBS, SSC, departments and agencies.

### 7.3 Third-party or managed services

Departments and agencies remain responsible for GC information and assets, even when they are managed or supported by a third-party or managed service provider.

Where SPIN actions rely on a third party, departments and agencies are expected to work with that provider to make sure they continue to meet contractual obligations that align with the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578) and Public Services and Procurement Canada (PSPC)’s [Contract Security Program](https://www.canada.ca/en/public-services-procurement/services/industrial-security/security-requirements-contracting/security-screening-government-contracts.html).

For third-party and managed service arrangements, departments and agencies should include the relevant SPIN and GC security requirements in procurement documents and contracts. These requirements should also be reflected in ongoing contract management, involving PSPC’s Contract Security Program when needed.

## 8. Compliance monitoring

For an outline of the consequences of non‑compliance, refer to the [Framework for the Management of Compliance](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=17151) (Appendix C: Consequences for Institutions and Appendix D: Consequences for Individuals).

TBS will perform active cyber verification of the GC’s perimeter and publicly accessible systems to ensure that potentially exposed devices and interfaces are identified and evaluated for potential vulnerabilities and remediated as appropriate by departments and agencies.

TBS will monitor departmental progress and will engage departmental senior officials, such as the chief information officer (CIO), chief security officer (CSO), and designated official for cyber security (DOCS), as necessary and appropriate, when the department or agency has not met the direction (required actions).

Appendix A provides a notional list of key performance indicators for each of the key actions to monitor the progress of achieving the objectives of the SPIN.

## 9. Enquiries

For additional information or clarification regarding this SPIN, address enquiries to:

[TBS Cyber Security](mailto:zztbscybers@tbs-sct.gc.ca)

## Appendix A. Key performance indicators

The following tables outlines a notional list of key performance indicators for each of the key actions to monitor the progress of achieving the objectives of the SPIN.

| Reference ID | Key actions (simplified) | Key performance indicators |
| --- | --- | --- |
| IDT-1 | Identify and rank departmental critical services; submit prioritized list in EPM. | % of organizations with a prioritized critical services list in EPM updated in the last 12 months |
| IDT-2 | Maintain current inventory of applications supporting critical services in APM; link to SSC ODS where possible. | % of applications supporting critical services that are recorded in APM and, where applicable, linked to SSC ODS |
| IDT-3 | Maintain up-to-date architecture diagrams for critical services. | % of critical services with diagrams updated in the last 12 months |
| IDT-4 | Maintain complete list of Internet connections (LIAS, public IPs, subnets, sub-domains) and provide to NCTNS. | % of LIAS circuits, public IP ranges, Internet-facing subnets and sub‑domains identified in authoritative network and billing records that are recorded and validated (within the last 12 months) in the Internet connection inventory submitted to NCTNS |
| IDT-5 | Maintain SBOMs for department-developed software supporting critical services. | % of department-developed software components supporting critical services with SBOMs created and updated within the last 12 months |
| IDT-6 | Improve endpoint management, asset visibility and rogue device detection via SSC EVA, prioritizing critical‑service endpoints. | % of endpoints supporting critical services with EVA agent deployed and healthy % of rogue or unmanaged endpoints detected by SSC EVA in environments supporting critical services that are investigated and either removed from the network or onboarded into managed inventory within 30 business days |

| Reference ID | Key actions (simplified) | Key performance indicators |
| --- | --- | --- |
| ACC-1 | Regularly check and triage vulnerability alerts from vendors, the Canadian Centre for Cyber Security, NCTNS and GC exposure findings. | % of high‑ and critical‑severity vulnerability notifications from vendors, the Canadian Centre for Cyber Security, NCTNS and GC exposure tools that are triaged, risk‑assessed and assigned a documented response within 10 business days of receipt |
| ACC-2 | Fix vulnerabilities based on risk within GC time frames, using GC tools and the GC Vulnerability Listing, with faster patching for critical, Internet-facing, and other high‑risk systems. | % of high‑risk vulnerabilities identified on critical, Internet‑facing and other designated high‑risk systems that are remediated or mitigated within the GC‑defined accelerated target time frame % of high‑risk vulnerabilities exceeding the target time frame that have documented risk acceptance or mitigation rationale |
| ACC-3 | Use defensive AI models/tools safely to find vulnerabilities and analyze software code. | % of new code repositories integrated with AI assisted vulnerability scanning |

| Reference ID | Key actions (simplified) | Key performance indicators |
| --- | --- | --- |
| HRD-1 | Enforce MFA for all user accounts; implement phishing-resistant MFA for administrative, privileged and other high-risk accounts. | % of all user accounts enforced with MFA % of administrative and privileged accounts enforced with phishing-resistant MFA |
| HRD-2 | Enforce password protection (block weak, common and compromised passwords). | % of accounts that have enforced password protection policies |
| HRD-3 | Apply least‑privilege access and regularly review/audit access, prioritizing administrative accounts for critical services. | % of privileged accounts whose rights match documented role requirements that have been reviewed within the last 12 months |
| HRD-4 | Prioritize centralized authentication with the use of enterprise-grade password manager for non-federated accounts. | % of applications integrated into centralized authentication % of non-federated accounts using an enterprise-grade password manager |
| HRD-5 | Use administrative accounts only for administrative tasks; protect them via centrally managed PAM with just‑in‑time elevation; use enterprise password manager as interim. | % of administrators using dedicated accounts for administrative tasks % of these privileged accounts managed by an enterprise PAM solution |
| HRD-6 | Set rules and life cycle controls for NPEs including ownership, purpose, credential rotation and periodic privilege attestation. | % of organizations who have a documented NPE governance % of NPEs with owner, purpose and rotation schedule recorded |
| HRD-7 | Use centrally managed tools to continuously find and fix identity‑based attack paths to critical services. | % of high‑risk identity attack paths to critical services that are remediated within the department’s target time frame |
| HRD-8 | Train and test staff on AI‑enabled phishing and impersonation, with extra focus on people in critical service and other high‑risk roles. | % of staff in critical service and other high‑risk roles who completed AI‑enabled phishing/impersonation training or simulations in the last 12 months |

| Reference ID | Key actions (simplified) | Key performance indicators |
| --- | --- | --- |
| FTY-1 | Harden edge devices, remote access, administrative interfaces, Internet-facing services, and APIs to essential functions and free of unnecessary software, services and components. | % of edge devices, remote access solutions, administrative interfaces, Internet‑facing services and APIs supporting critical services whose configurations conform to the approved departmental hardening baseline and have been validated through scan or audit within the last 12 months |
| FTY-2 | Tightly control vendor remote access (inventory, approved methods, time/task limits, logging, rapid removal). | % of vendor remote access channels inventoried with owner and approved access methods |
| FTY-3 | Deploy critical services in network zones segmented according to ITSP.80.022 and ITSG-38. | % of critical services segmented in networks zones aligned to GC standards |
| FTY-4 | Enforce default‑deny outbound Internet traffic for environments hosting critical services; allow only approved destinations. | % of network environments hosting components of critical services that enforce a default‑deny outbound Internet policy with an approved destination allow‑list, and whose enforcement has been validated within the last 12 months |
| FTY-5 | Perform all authorized administrative work only from GC‑approved hardened devices (for example, DAWs) over protected administrative channels that are isolated from lower‑trust environments. | % of privileged administrative sessions on critical and other high‑risk systems that use GC‑approved hardened endpoints and designated protected administrative channels. |

| Reference ID | Key actions (simplified) | Key performance indicators |
| --- | --- | --- |
| MTR-1 | Implement logging per GC Event Logging Guidance, prioritizing critical‑service systems, to provide end‑to‑end visibility. | % of critical services generating required log types |
| MTR-2 | Protect logs from tampering using approved cryptography; forward to central logging facility for storage, monitoring and analysis. | % of critical services sending logs to central logging facility |
| MTR-3 | Use centrally managed EDR/XDR on endpoints that support critical services and administrative work, integrated with departmental logging and monitoring. | % of endpoints supporting critical services and administrative functions with centrally managed EDR/XDR active and reporting to departmental monitoring |

| Reference ID | Key actions (simplified) | Key performance indicators |
| --- | --- | --- |
| PRP-1 | Review and update the CSEMP so authorities and escalation are clear and aligned with the departmental BCP. | % of organizations with departmental CSEMP that has been updated to include escalation pathways aligned to departmental BCP within the last 12 months |
| PRP-2 | Run cyber tabletop exercises to test the CSEMP and confirm alignment with BCP. | % of critical services exercised over the last 12 months % of tabletop exercises that resulted in documented updates to CSEMP/BCP within the last 12 months |
| PRP-3 | Develop, approve, and maintain incident response (IR) playbooks with decision steps, service level agreements, escalation, pre‑approved containment actions and forensic telemetry procedures. | % of critical services covered by an approved IR playbook updated within the last 12 months |
| PRP-4 | Regularly test restores from backups and verify restored data against a known good reference. | % of restore tests that meet integrity checks and align with business continuity management requirements % of critical services whose backups were tested in the last 12 months |
| PRP-5 | Keep backups for critical systems separated from production and, where possible, use immutable (write‑once) storage, with access controls and monitoring to prevent compromise. | % of critical services whose primary backups are on logically separated and, where feasible, immutable storage, and have been successfully restore‑tested in the last 12 months |

## Footnotes

**Footnote 1**: [Top 10 artificial intelligence security actions: A primer](https://www.cyber.gc.ca/en/guidance/top-10-artificial-intelligence-security-actions-primer-itsap10049) (ITSAP.10.049) [Return to footnote 1 referrer](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/direction-government-canada-cyber-security-readiness-frontier-artificial-intelligence-era.html#fn1-rf)

**Footnote 2**: [Security considerations for edge devices](https://www.cyber.gc.ca/en/guidance/security-considerations-edge-devices-itsm80101) (ITSM.80.101) [Return to footnote 2 referrer](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/direction-government-canada-cyber-security-readiness-frontier-artificial-intelligence-era.html#fn2-rf)

**Footnote 3**: [Directive on Security Management – Appendix D: Mandatory Procedures for Business Continuity Management Control](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611&section=procedure&p=D) [Return to footnote 3 referrer](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/direction-government-canada-cyber-security-readiness-frontier-artificial-intelligence-era.html#fn3-rf)

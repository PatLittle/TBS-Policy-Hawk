# Migrating the Government of Canada to Post-Quantum Cryptography: Security Policy Implementation Notice

- Notice source: Security Policy Implementation Notice (SPIN)
- Source page URL: https://www.canada.ca/en/government/system/digital-government/policies-standards/spin.html
- Source page modified: 2025-10-09
- Notice URL: https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/migrating-government-canada-post-quantum-cryptography.html
- Notice modified: 2025-10-09
- Notice identifier: 2025-01
- Listed date: 2025-10-09
- Captured at (UTC): 2026-07-14T09:47:12Z

---

# Migrating the Government of Canada to Post-Quantum Cryptography: Security Policy Implementation Notice

## 1. Effective date

This Security Policy Implementation Notice (SPIN) is effective as of October 9, 2025.

## 2. Purpose

The purpose of this SPIN is to reinforce requirements under the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578) and the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603) to:

- mitigate the risks that quantum computers pose to the security of the cryptography used in Government of Canada (GC) services, systems and devices
- make measurable progress toward migration to post-quantum cryptography (PQC) within the GC

## 3. Scope

This SPIN is applicable to any GC information system (departmental or enterprise) that employs cryptography. Systems that use cryptography include network services, operating systems, applications, code development pipelines and all physical information technology (IT) assets.

## 4. Application

This SPIN applies to the organizations listed in section 6 of the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578).

## 5. Context

The GC, like all other government and private sector organizations around the world, faces the threat of a future quantum computer that is powerful enough to break modern cryptographic algorithms (often called a cryptographically relevant quantum computer (CRQC)). A CRQC, when used by malicious actors, will be able to break many of the cryptographic algorithms that underlie the GC’s IT infrastructure.

To address this risk, cryptographic algorithms that are not vulnerable to quantum-enabled attacks have been designed and standardized. These algorithms make up what is called PQC. As outlined in the Canadian Centre for Cyber Security’s (Cyber Centre’s) [Roadmap for the Migration to Post-Quantum Cryptography for the Government of Canada (ITSM.40.001)](https://www.cyber.gc.ca/en/guidance/roadmap-migration-post-quantum-cryptography-government-canada-itsm40001), every organization that manages IT systems must migrate cyber security components to become quantum-safe in order to protect against the cryptographic threat of a future quantum computer.

To that end, migration to PQC is critical to ensure that GC systems remain secure against future threats posed by quantum computing. Migrating the current cryptography to PQC across the GC to protect the GC’s communications and data is a significant technological change that will take careful planning and execution over a period of years. Delaying the process could result in failure to meet the migration timeline, thereby increasing the risk of exposure for sensitive data entrusted to the GC.

All departments and agencies play a critical role in ensuring the confidentiality, integrity and availability of the GC’s information and networks. According to the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611), deputy heads have a responsibility to implement security controls to protect information systems under their organization’s custody or control. These responsibilities include:

- safeguarding the confidentiality, integrity and availability of GC information and IT assets
- implementing measures for the protection of personal information

Departments and agencies must understand their cryptography usage and analyze their information systems and system components, including supporting hardware and software, across the entire organization. As Shared Services Canada (SSC) manages IT infrastructure and services on behalf of many departments and agencies across the GC, it plays a key role in supporting the migration to PQC. Within this shared responsibility model, there are interdependencies between SSC infrastructure and the applications that are delivered by departmental programs and services. Collaboration across departments and agencies is thus essential for the transition to PQC.

## 6. Direction

**In this section**

- [6.1 Phase 1: Preparation](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/migrating-government-canada-post-quantum-cryptography.html#toc6-1)
- [6.2 Phase 2: Identification](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/migrating-government-canada-post-quantum-cryptography.html#toc6-2)
- [6.3 Phase 3: Transition](https://www.canada.ca/en/government/system/digital-government/policies-standards/spin/migrating-government-canada-post-quantum-cryptography.html#toc6-3)

To ensure that the GC remains resilient in the face of emerging quantum threats, the GC must proactively safeguard its digital infrastructure by migrating to quantum-safe cryptography. As set out in Appendix B of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611), and to ensure that cyber security risks to the GC are reduced according to section 4.4.17 of the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603), departments and agencies are expected to:

- implement measures to protect information systems, their components and the information they process and transmit (section B.2.3.6 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611))
- maintain reasonable confidence of the IT supply chain (section B.2.5 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611)), including ensuring that security controls are implemented to protect information systems that are used to electronically process or transmit sensitive information or that are relied on to produce or deliver the goods or services being procured (section F.2.3 of the [Directive on Security Management](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32611))

The establishment of a migration plan is a key component to support the transition to PQC. Following are the three phases of the migration plan:

- Phase 1: Preparation, which focuses on establishing an initial plan to help clarify the roles and responsibilities involved in developing and migrating systems to use PQC within a department, with consideration of financial requirements and updates to contract clauses to support PQC as part of departmental procurement activities
- Phase 2: Identification, which focuses on cryptographic discovery needs to determine where cryptography is used in IT systems, and the creation of an inventory of systems that need to be transitioned, including identification of high-priority systems for migrating to PQC
- Phase 3: Transition, which focuses on the implementation activities required to migrate IT systems to PQC, based on priorities

The scope of the migration plan is for information systems that store and process up to and including Protected B information. For classified systems and systems that handle Protected C information, departments must contact the Cyber Centre.

The following subsections outline key milestones and activities in keeping with this SPIN.

### 6.1 Phase 1: Preparation

By April 1, 2026, departments and agencies will:

- 6.1.1 Develop a high-level departmental PQC migration plan that guides Phase 1 of the PQC migration of systems that use cryptography for which the department is responsible; and
- 6.1.2 Begin reporting on the PQC migration progress on an annual basis, with incremental updates to the departmental PQC migration plan, in accordance with section 4.1.7 of the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603).

By April 1, 2026, SSC will:

- 6.1.3 Develop a high-level PQC migration plan to guide Phase 1 of the PQC migration of systems that use cryptography for which SSC is responsible. The SSC PQC migration will be shared with departments and agencies to support departmental migration plans and account for potential dependencies and interoperability considerations; and
- 6.1.4 Begin reporting on the PQC migration progress on an annual basis, with incremental updates to the departmental PQC migration plan, in accordance with section 4.1.7 of the [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603).

### 6.2 Phase 2: Identification

By April 1, 2027, departments and agencies will:

- 6.2.1 Update the high-level departmental PQC migration plan to guide Phase 2 of the PQC migration of systems that use cryptography for which the department is responsible.

By April 1, 2027, SSC will:

- 6.2.2 Update the high-level PQC migration plan to guide Phase 2 of the PQC migration of systems for which they are responsible.

By April 1, 2028, departments and agencies, including SSC, will:

- 6.2.3 Update departmental records of IT systems captured in the Treasury Board of Canada Secretariat’s (TBS’s) [Application Portfolio Management (APM) tool](https://tbs-clarity.ssc-spc.gc.ca/niku/nu) (accessible only on the GC network) of the Office of the Chief Information Officer, or a comparable tool, to ensure that system information includes, at a minimum: System architecture and cryptographic details Vendor and life-cycle information Migration planning and oversight
- System components that employ cryptography
- Location of system components (for example, external-facing, internal)
- Current cryptographic algorithms and protocols employed
- Hosting platform
- System dependencies

- Vendor and product version for each of the components
- Relevant service contracts and expiry dates
- Expected refresh year for the system or its components

- Responsible departmental point of contact
- Priority for migration
- Migration status

- 6.2.4 Identify systems that are a high priority for migrating to PQC, such as those that are susceptible to a “harvest now, decrypt later” (HNDL) threat (for example, systems that protect the confidentiality of information in transit over public network zones) or custom applications; and
- 6.2.5 Engage with SSC via the SSC client executive to review plans (for example, upgrades versus replacement) to implement PQC for the services provided by SSC for the department.

### 6.3 Phase 3: Transition

By April 1, 2026, departments and agencies, including SSC, will:

- 6.3.1 Ensure that all contracts that have a digital component entered into after this date include procurement clauses for IT systems, aligned with the [Cyber Centre’s recommendation on PQC procurement clauses](https://www.cyber.gc.ca/en/guidance/recommended-contract-clauses-cryptography-itsm00501) , that support:
- PQC that is compliant with Cyber Centre recommendations in [Cryptographic Algorithms for Unclassified, Protected A, and Protected B Information: ITSP.40.111](https://www.cyber.gc.ca/en/guidance/cryptographic-algorithms-unclassified-protected-protected-b-information-itsp40111)
- cryptographic modules that have been certified by the [Cryptographic Module Validation Program (CMVP)](https://www.cyber.gc.ca/en/tools-services/cryptographic-module-validation-program-cmvp)
- [cryptographic agility](https://www.cyber.gc.ca/en/guidance/guidance-becoming-cryptographically-agile-itsap40018) to allow for future configuration changes

By April 1, 2028, departments and agencies will:

- 6.3.2 Update the high-level departmental PQC migration plan to guide Phase 3 of the PQC migration, including prioritization of systems for migration; and
- 6.3.3 Begin transitioning systems for which the department is responsible to quantum-safe cryptography.

By April 1, 2028, SSC will:

- 6.3.4 Update the high-level PQC migration plan to guide Phase 3 of the PQC migration, including prioritization of systems for migration; and
- 6.3.5 Begin transitioning systems for which SSC is responsible to quantum-safe cryptography.

By the end of 2031, departments and agencies, including SSC, will:

- 6.3.6 Complete the PQC migration of high-priority systems.

By the end of 2035, departments and agencies, including SSC, will

- 6.3.7 Complete the PQC migration of remaining systems.

## 7. Compliance monitoring

For an outline of the consequences of non-compliance, refer to the [Framework for the Management of Compliance](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=17151) (Appendix C: Consequences for Institutions and Appendix D: Consequences for Individuals).

TBS will monitor departmental progress and will engage departmental senior officials, such as the chief information officer (CIO), chief security officer (CSO), designated official for cyber security (DOCS), and designated official for procurement, as necessary and appropriate, when the department has not met the direction (required actions) deadlines specified above.

SSC will provide periodic updates to the IT Security Tripartite on progress for the PQC migration plan as it relates to the infrastructure and network components under SSC’s management.

## 8. Enquiries

For additional information or clarification regarding this SPIN, address enquiries to TBS Cyber Security at [zztbscybers@tbs-sct.gc.ca](mailto:zztbscybers@tbs-sct.gc.ca).

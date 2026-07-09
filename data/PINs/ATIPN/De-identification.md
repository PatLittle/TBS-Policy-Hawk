# De-identification

- Notice source: Access to Information and Privacy Notices (ATIPN)
- Source page URL: https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices.html
- Source page modified: 2026-03-23
- Notice URL: https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html
- Notice modified: 2026-06-29
- Notice identifier: 2023-01
- Notice group: Privacy implementation notices
- Listed date: 
- Captured at (UTC): 2026-07-09T17:48:02Z
- Page title: Privacy Implementation Notice 2023-01: De-identification

---

# Privacy Implementation Notice 2023-01: De-identification

## 1. Effective date

This implementation notice takes effect on May 27, 2025. It replaces the notice published on March 17, 2023.

## 2. Authorities

This implementation notice is issued pursuant to paragraph 71(1)(d) of the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html).

## 3. Purpose

This implementation notice provides information and guidance to government institutions on the use of de‑identification as a privacy‑preserving technique to bolster the privacy protections around the personal information under their control in support of their obligations under the section 3.1.3 of the [Policy on Privacy Protection](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=12510).

This notice provides new and updated guidance on the concepts first introduced in [PIN 2020‑03: Protecting privacy when releasing information about a small number of individuals](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2020-03-protecting-privacy-releasing-information-about-small-number-individuals.html), which contains useful guidance on how to de‑identify information that is to be released, when the intent is to not release the identity of individuals. This notice offers additional information and considerations on de‑identification as a way to protect personal information. It will not offer guidance on anonymization for the public release of information.

To introduce government institutions to possible uses of de‑identification, this notice sets out:

- considerations into the context and risk of re‑identification
- an introduction to methods for de‑identification
- working definitions of key terms related to de‑identification

This guidance is to be read in conjunction with other privacy and data protection guidance and requirements, including those related to information management, data governance and security.

Definitions used throughout this notice are found in the [Appendix](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#app).

## 4. Context

Government institutions collect, use and disclose information for a variety of purposes and in a variety of situations, such as for administering a program or activity, statistical analysis, research, program evaluation and business intelligence. This information may take the form of individual records or tables and summary statistics.

If there is a reasonable expectation that individuals can be identified through the information, alone or in combination with other available information, it constitutes personal information, which is defined in section 3 of the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html).

When information is considered personal it must be protected in accordance with the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html), which imposes limitations to what an institution can do with the information. However, there are privacy‑preserving techniques that can be used to enable institutions to derive further value from the information they have already collected in line with their legal authority, while protecting the privacy of individuals. One approach is to de‑identify the information prior to use or disclosure in cases when the identity of individuals does not need to be known. Other privacy protective actions can be taken in addition to de‑identification, such as data minimization and the appropriate use of agreements and arrangements.

This guidance applies to all information recorded in any form, but specifically focuses on information in written, typed, tabular or other similar digital formats. As the format of information changes, so would the de‑identification practices.

For the purposes of this notice, the term “information” is to be interpreted broadly and includes “data.” For a comparison of the terms “information” and “data,” consult [Appendix D of the Guideline on Service and Digital.](https://www.canada.ca/en/government/system/digital-government/guideline-service-digital.html#ToC9)

## 5. Guidance

De‑identification is a statistical process and comprises one step toward anonymization. It is a privacy‑preserving technique that can be applied to personal information to support deriving additional value from information, while also protecting individual privacy.

Because de‑identified information carries a risk of re‑identification, it falls within the scope of the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html). At the discretion of the institution and following an assessment, de‑identified information may be used or disclosed with appropriate and proportionate privacy protections.

As it is an emerging field, the term “de-identification” will evolve over time. Three main elements of the definition are central to the concept, regardless of the wording of the definition itself:

- Context: The circumstances around using and disclosing the information impacts the degree of de‑identification necessary to protect the information from re‑identification.
- Residual risk of re‑identification: It is rarely possible to completely eliminate the risk that de‑identified information can be re‑identified. The acceptable risk level must be determined based on the context.
- Process: The steps taken to remove or obscure direct and/or indirect identifiers with the purpose of de‑identifying the information.

More than one [de‑identification method](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#dim) may be used to reduce the risk of re‑identification. This, in turn, reduces the likelihood of misuse and minimizes the impact of inappropriate disclosures or other privacy breaches. Depending on the degree of de‑identification applied, other technical and administrative controls may be required.

There are activities that increase the risk of re‑identification, such as integrating datasets or data matching, so it is important to continually assess privacy and re‑identification risks, even after applying privacy safeguards.

Program and privacy officials should work with statistical and data experts to determine the acceptable level of residual risk given the nature of the information (data itself, context of use or disclosure, impacts of re‑identification on individuals, among others), the proposed use case and the kinds of de‑identification methods possible based on the institution’s data infrastructure.

Institutions are also encouraged to consult [Statistics Canada](https://www.statcan.gc.ca/en/reference/refcentre/index) as Canada’s lead authority on statistical standards, methods and processes.

### A note on identifiability

To assist in ensuring privacy protection while deriving value from information, it may help to think of identification along a spectrum. Where the de‑identified information lands on the spectrum may help determine the proportionate privacy protections required to safeguard the information.

At one end of the spectrum is personal information as defined in the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html). [Direct identifiers](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#di) would fall at this end, as would the combination of many [indirect identifiers](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#ii). Strong privacy safeguards must be in place when managing personal information.

At the other end of the spectrum is information that is non‑personal, and never was personal. Budget reports, corporate planning, project dashboards and other similar information are examples of information that is not personal. Privacy safeguards are not needed in managing non‑personal information; however, general government security and information management measures must continue to be applied as appropriate.

#### 5.1 When to de‑identify

Institutions may want to use and/or disclose de‑identified information to support a wide range of activities where the identity of individuals is not required. Some of these activities include but are not limited to:

- research, statistical analysis, peer review or trend analysis activities internally or involving other government institutions or jurisdictions
- evidence‑informed policy or program decisions, including business intelligence, program evaluation, and impact of programs on diversity groups
- bias and harm assessment, such as analyses of information to find and mitigate systemic biases within the institution’s information holdings

#### 5.2 Considerations

This guidance assumes a decision has been made that de‑identification is an acceptable privacy‑preserving technique to use in the particular context. This decision should be made by the appropriate official(s) responsible for the information, in consultation with the official(s) responsible for privacy within their institution.

Under section 4.2.9 of the [Policy on Privacy Protection](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=12510), institutions must establish a privacy protocol for the collection, use or disclosure of personal information for non‑administrative purposes, de‑identified or otherwise. A privacy protocol may also be used to document the steps taken to assess and appropriately de‑identify the information.

##### 5.2.1 Information context

Each use of de‑identified information should be assessed on a case‑by‑case basis, in collaboration with the institution’s privacy experts. The following are examples of factors that should be taken into account in assessments (adapted from [PIN 2020‑03](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2020-03-protecting-privacy-releasing-information-about-small-number-individuals.html)):

- external versus internal uses
- the sensitivity of the information
- the potential harm that could result from re‑identification
- the level of detail of the information (for example, does it contain full birthdate or just birth year)
- any information at the user’s disposal that could be matched or integrated with the de‑identified information and used to re‑identify individuals

Additional information on sensitivity and harm can be found in the [Privacy Breach Toolkit](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/privacy/breach-management.html) and the [Policy on Government Security](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=16578).

###### 5.2.1.1 External uses (an institution discloses de‑identified information to an entity outside of the institution)

Institutions may disclose personal information without an individual’s consent only in limited circumstances described under subsection 8(2) of the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html). With sufficient de‑identification and considering the context, an institution may deem that the information does not meet the definition of personal information in the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html).

In making this determination, institutions should consider who is using the information (such as another federal government institution, a different level of government, academia), the likelihood of re‑identification and the risks to individuals if the information were re‑identified. For example, entities both internal to and outside the Government of Canada may be privy to other information or knowledge that, when combined with the de‑identified information, may facilitate re‑identification. They may also be subject to different laws with or without penalties for re‑identification and may be less aware of the risk of re‑identification. They may also have different requirements around privacy safeguards and privacy breaches.

The appropriate administrative controls should be in place ahead of the disclosure. Agreements and arrangements must delineate how the information is to be handled and safeguarded, that the onward disclosure of the de‑identified information by the receiving entity be limited and describe procedures to be actioned in the event of a privacy breach.[Footnote 1](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#fn1) See the [Guidance on Preparing Information Sharing Agreements Involving Personal Information](https://www.tbs-sct.canada.ca/ATIP-AIPRP/isa-eer/isa-eer00-eng.asp) for considerations of when to enter into an arrangement or agreement.

Information that will be published as open data or open information must be anonymized. Open government and other public posting of information is out of the scope of this notice. Institutions within the core public administration must follow the [Directive on Open Government](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=28108).

###### 5.2.1.2 Internal uses

In general, and subject to the need‑to‑know principle, employees and officers of a program or activity may process personal information. When employees or officers need to use information for their job that is not directly related to a decision‑making process, such as program evaluation or research, working with de‑identified information is a privacy‑preserving practice, as it reduces the likelihood and impact of a privacy breach.

Institutions may consider including de‑identification in new or existing processes where other uses of information are envisioned. For example, creating a de‑identified version of the information immediately following its administrative use may facilitate future uses. This version of the information would inherently have a layer of privacy protection that can then be built upon with additional de‑identification methods later for a particular use or disclosure. Building de‑identification into processes allows institutions to make greater use of the data under their control, while also protecting the personal information of individuals.

##### 5.2.2 Risk of re‑identification

The risk of re‑identification is inherent in de‑identified information. Therefore, the acceptable level of risk must be determined on a case‑by‑case basis, and appropriate privacy safeguards must be applied. The risk of re‑identification can be considered in terms of the information itself, the probability of re‑identification and the potential harm if the information were breached.

As an example, an institution may de‑identify personal information ahead of statistical analysis. Because the statisticians do not need to know the identity of the individuals for the analysis, the institution is protecting the personal information in that dataset. If the analysis is so detailed, it may be possible the statisticians can re‑identify individuals from the dataset. While the probability or likelihood of that happening may be high, the risk to the individuals in the dataset and the reputational risk to the institution are low because of the limited use of the data (statistical analysis) and the controlled access to the data (internal use only by accountable employees with appropriate training in information handling practices and security clearances). Even when the risk to individuals is low, de‑identification is a privacy‑preserving technique that institutions can take to reduce the probability of re‑identification.

The assessment of the risk of re‑identification for disclosures of de‑identified information should include an analysis of the context of disclosure to determine the likelihood of re‑identification and the impact to the individual and the institution. In this case, the likelihood may be medium, but the impact to the individual and the institution could be high, depending on who the recipient is (for example, it might be higher if the disclosure was to a private researcher rather than a provincial government that has privacy obligations of their own). Institutions may wish to update existing subsection 8(2) processes for routine disclosures to include a determination of whether the recipient would accept de‑identified information rather than personal information.

Institutions can leverage statistical methods to measure the risk of re‑identification and develop risk thresholds for certain information types, such as structured data tables. The [Privacy Breach Management Toolkit](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/privacy/breach-management.html) provides guidance on risk and can help inform the re‑identification risk threshold.

###### 5.2.2.1 Sensitive information

When de‑identifying sensitive personal information, it is important to take steps to ensure that the risk of re‑identification is very low, given its high impact to the individual. Institutions may choose to de‑identify sensitive personal information to the point of anonymization to ensure an almost‑nil risk of re‑identification. Health information and the personal information of minors are common examples of sensitive personal information.

##### 5.2.3 Methods

Information may be de‑identified manually or by using tools in the form of code or an algorithm. Statistics Canada may be consulted for advice and recommendations on how this can be achieved.

Manual methods can be as straightforward as suppressing entire columns of a dataset that are direct identifiers or considered highly sensitive. A moderate approach may include reducing the granularity of datasets to ensure that units are less unique. This could be, for example, using the age range rather than the exact age, or using just the area code rather than the exact phone number. A more sophisticated method could use algorithms to artificially create or mask data. This can be further explored with data experts within the institution.

The methods chosen depend on a variety of factors—most notably those factors we have already discussed such as context, the data itself and the acceptable level of residual risk of re‑identification. More than one method may also be used on one dataset or set of information.

Technical methods are only one aspect of preserving privacy. De‑identification helps protect the information by reducing the risk of inadvertent disclosure of personal information. Other controls such as administrative controls, including agreements and arrangements, access controls and auditing, are also important to further reduce the risk of inadvertent disclosure or unauthorized access, re‑identification or inference, and to generally preserve and promote the privacy of individuals.

###### 5.2.3.1 Small numbers of individuals

[PIN 2020‑03: Protecting privacy when releasing information about a small number of individuals](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2020-03-protecting-privacy-releasing-information-about-small-number-individuals.html) provides useful information when releasing data about a small number of individuals when the intent is to not release the identity of individuals. The PIN includes information on measures to protect against re‑identification with microdata files, specifically suppressing, masking and redacting direct identifiers, and assessing the risk of re‑identification through indirect identifiers. It also offers guidance when releasing aggregate tables, such as determining the appropriate minimum cell size when releasing data in tables and modifying the data to mitigate the risk of re‑identification.

###### 5.2.3.2 Masking and obfuscating

Masking and obfuscating are general terms that encompass a variety of methods to delete, remove, replace, alter or hide identifiers in a dataset. Below are some more specific examples.

- Nulling, field suppression –Replacing the values with empty strings, such as dashes.
- Rounding, generalization, aggregation – Rounding numbers up or down to a nearest round value. For example, rounding or generalizing to the nearest decimal point or to the nearest five, or grouping age ranges together.
- Regex – Code that searches a dataset to find specific strings of characters and replaces them with certain values (nulls specific elements of a value that has a certain characteristic). For example, the regex function could search for a series of nine digits (such as a Social Insurance Number [SIN]) and replace the first six with zeros but leave the final three.
- Perturbation –Replacing specific values with other values that are consistent for each individual. For example, adding or subtracting two years from each individual’s actual age.
- Hashing – Applying cryptographic functions to mix‑up the original data into an unrecognizable value. Hash functions are widely known, and it is possible to reverse-engineer the hashed value into the original value.
- Salting – Adds long random values (the salt) to the original dataset before the hashing happens. As the salt is added to the dataset prior to the hashing, it makes it next to impossible to reverse-engineer the dataset.

###### 5.2.3.3 Pseudonymization

Broadly, pseudonymization is a process of masking direct identifiers. Pseudonymization is a popular form of de‑identification.

Pseudonymization is very similar to nulling and field suppression described above, but where the direct identifiers are replaced with aliases and that same alias is used consistently across datasets. In this manner, although an individual’s direct identifiers are pseudonymized in a variety of datasets, those with a “key” can re‑identify individuals. It is therefore important to properly generate a pseudo‑identifier and ensure that the correspondence to direct identifiers is protected and limited to those with a need to know.

Pseudonymization may be particularly useful for internal uses of de‑identified information where a unique identifier is needed. This may include hierarchical files (such as, family structures) or when linking different sources of information is necessary. When no other de‑identification strategies are in place along with pseudonymization, there remains a fairly high risk of re‑identification.

###### 5.2.3.4 Synthetic data generation

Algorithms may perform synthetic data generation whereby the algorithm “reads” the original dataset and creates a new dataset with completely fake values. The newly created dataset contains the same statistical properties of the source dataset but would not contain real individual data. Synthetic data generation may be of particular interest when training artificial intelligence and machine learning tools, and in open data strategies such as training, outreach and data familiarization.

#### 5.3 Auditing and monitoring

Once data has been de‑identified, regular auditing and monitoring will make sure that the level of de‑identification remains to ensure that the institution’s de‑identification processes are effective. Over time, additional information and technologies may emerge that make it easier to re‑identify information that had once been de‑identified. This is especially important for de‑identified information that has been or is intended to be disclosed outside of the institution. Auditing and monitoring can be used to modify strategies going forward, and technology can be leveraged to bolster de‑identification practices.

Institutions should build in scheduled time frames for testing, auditing and monitoring commensurate to the type and nature of information being used in order to ensure that the information remains de‑identified into the future, and that the techniques they use to de‑identify are up to date.

## 6. Application

This implementation notice applies to the government institutions defined in section 3 of the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html), including parent Crown corporations and any wholly owned subsidiary of these corporations. However, this notice does not apply to the Bank of Canada or to information that is excluded under the [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/P-21/index.html).

## 7. References and resources

- [Directive on Privacy Practices](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=18309)
- [Directive on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32601)
- [IAPP – De‑identification 101: A lawyer’s guide to masking, encryption, and everything in between](https://iapp.org/news/a/de-identification-101-a-lawyers-guide-to-masking-encryption-and-everything-in-between/)
- [ICO call for views: Anonymisation, pseudonymisation and privacy enhancing technologies guidance | ICO](https://ico.org.uk/about-the-ico/ico-and-stakeholder-consultations/2023/12/ico-call-for-views-anonymisation-pseudonymisation-and-privacy-enhancing-technologies-guidance/)
- [IPC – De‑identification Guidelines for Structured Data](https://www.ipc.on.ca/wp-content/uploads/2016/08/Deidentification-Guidelines-for-Structured-Data.pdf)
- [NIST – De‑identification of personal information](https://nvlpubs.nist.gov/nistpubs/ir/2015/NIST.IR.8053.pdf)
- [Policy on Privacy Protection](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=12510)
- [Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603)
- [Privacy Act](https://laws-lois.justice.gc.ca/eng/acts/p-21/FullText.html)
- [Privacy Breach Management Toolkit](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/privacy/breach-management.html)
- [Privacy Implementation Notice 2020‑03: Protecting privacy when releasing information about a small number of individuals](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2020-03-protecting-privacy-releasing-information-about-small-number-individuals.html)

## 8. Enquiries

Members of the public can contact [TBS Public Enquiries](mailto:questions@tbs-sct.gc.ca) for information about this implementation notice.

Employees of federal institutions may contact their [Access to Information and Privacy coordinator](https://www.tbs-sct.canada.ca/ap/atip-aiprp/coord-eng.asp) for information about this implementation notice.

Access to Information and Privacy coordinators may contact the Treasury Board of Canada Secretariat’s [Privacy and Responsible Data Division](mailto:ippd-dpiprp@tbs-sct.gc.ca) for information about this implementation notice and ensuring that their institution is meeting their privacy obligations concerning de‑identification.

For advice and recommendations on anonymization and on how to assess the risk of re‑identification, contact [Statistics Canada](https://www.statcan.gc.ca/en/reference/refcentre/index).

## Appendix: Definitions

There are several definitions for the following concepts, and the meaning may shift depending on the context in which the word is being used. For the purposes of this implementation notice, the following definitions are used.

anonymized information (renseignements anonymisés)

Personal information that has been de‑identified to the point that there is no serious possibility of re‑identification, by any person or body using any additional data or technology at this point in time.[Footnote 2](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#fn2)

data (données)

Set of values of subjects with respect to qualitative or quantitative variables representing facts, statistics, or items of information in a formalized manner suitable for communication, reinterpretation or processing ([Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603)).

de-identification (dépersonnalisation)

A process that involves modifying personal information to remove or alter identifiers to reduce identifiability and implementing mitigation controls to a degree that is reasonable in the context. De-identified information carries a residual risk of re-identification ([Directive on Privacy Practices](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=18309)).

de‑identified information (renseignements dépersonnalisés)

Information resulting from the application of de-identification ([Directive on Privacy Practices](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=18309)).

direct identifier (identifiant direct)

Attributes that can be used alone to identify or point explicitly to an identifiable individual (such as, name, social insurance number, or medical record number) ([PIN 2020‑03: Protecting privacy when releasing information about a small number of individuals](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2020-03-protecting-privacy-releasing-information-about-small-number-individuals.html)).

indirect identifier (identifiants indirect)

Attributes that alone or in combination could be linked with other information, or used by someone with background knowledge, to identify an individual (such as, age, gender or province of residence). The greater the number of indirect identifiers, the greater the likelihood of re‑identification ([PIN 2020‑03: Protecting privacy when releasing information about a small number of individuals](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2020-03-protecting-privacy-releasing-information-about-small-number-individuals.html)).

information (information)

Knowledge captured in any format, such as facts, events, things, processes or ideas, that can be structured or unstructured, including concepts that within a certain context have particular meaning. Information includes data ([Policy on Service and Digital](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603)).

proportionate privacy protections (mesures de protections des renseignements personnels proportionnées)

Privacy safeguards applied to the information that are commensurate with the risk of privacy breaches or re‑identification. Determining the proportionate privacy protections includes an analysis of many interrelated factors, such as the degree of sensitivity associated with the original information, whether the users of the information are within the institution or elsewhere, the purpose for which they are using the information and how the information is being transferred.[Footnote 3](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#fn3)

## Footnotes

**Footnote 1**: See section 4.2.16 of the [Policy on Privacy Protection](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=12510) and sections 4.2.33–37 of the [Directive on Privacy Practices](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=18309). [Return to footnote 1 referrer](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#fn1-rf)

**Footnote 2**: This is a working definition. As the term is not defined in federal Canadian law or policy at the time of writing this PIN, this definition is used solely for the purposes of this PIN. [Return to footnote 2 referrer](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#fn2-rf)

**Footnote 3**: Ibid. [Return to footnote 3 referrer](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices/2023-01-de-identification.html#fn3-rf)

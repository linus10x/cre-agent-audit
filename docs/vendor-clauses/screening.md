# Vendor clause — Tenant-screening AI

> **Reference contract addendum, not legal advice.** Adapt to your jurisdictions and risk appetite in consultation with counsel. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

Drop-in contract language for the operator's next vendor contract renewal or change-order with a tenant-screening AI vendor (SafeRent, RentGrow, TransUnion SmartMove, Real Capital Solutions, Findigs, or equivalent). The clauses below pair with [ADR-0011 (Vendor-Output Adapter Pattern)](../adr/0011-vendor-output-adapter-pattern.md); the adapter only works if the vendor exposes the data these clauses obligate.

## Section 1 — Data Processing Addendum (DPA) — tenant data

1.1 **Data residency.** Vendor shall process all Personal Data of Operator's applicants ("Applicant Data") within the United States. No Applicant Data shall be transferred outside the United States without Operator's prior written consent in each instance.

1.2 **Subprocessors.** Vendor shall maintain a written list of all subprocessors with access to Applicant Data; the list shall be made available to Operator upon request; Vendor shall provide Operator no fewer than 30 days' written notice of any new subprocessor and shall accept Operator's reasonable objection.

1.3 **Retention.** Vendor shall retain Applicant Data only for the period necessary to perform the screening function and shall delete or anonymize the data within 30 days of the completion of the screening, except where retention is required by applicable law (in which case the legal basis and retention period shall be documented in writing and made available to Operator on request).

1.4 **Breach notification.** Vendor shall notify Operator of any actual or reasonably-suspected breach of Applicant Data within 48 hours of discovery, with the notification including: (i) the nature of the breach, (ii) the categories and approximate number of data subjects affected, (iii) the likely consequences, (iv) the measures taken or proposed.

## Section 2 — Model Risk Addendum

2.1 **Model documentation.** Vendor shall provide Operator with a current Model Card (in the form of Mitchell et al. 2019 — *Model Cards for Model Reporting*) for each model used to generate a score, recommendation, or reason-code that Operator receives. The Model Card shall be updated within 30 days of any material model change and shall include at minimum: training-data summary, intended use, performance characteristics, fairness evaluation methodology, known limitations.

2.2 **Reason codes.** Every vendor-generated decision shall include an FCRA-style reason code drawn from a published reason-code dictionary maintained by Vendor. The dictionary shall be made available to Operator on request and shall be versioned.

2.3 **Adverse-action support.** Vendor shall provide Operator with sufficient information about each declined or threshold-below-cutoff decision to enable Operator to issue a compliant FCRA adverse-action notice to the applicant (15 U.S.C. § 1681m).

2.4 **Model-change notification.** Vendor shall provide Operator no fewer than 30 days' written notice of any material change to the underlying model (algorithm change, training-data refresh of greater than 10% by row count, threshold or scoring-scale change). Operator shall have the right to require an additional 30-day shadow-mode period before the change goes live for Operator's applicants.

## Section 3 — Fairness Reporting SLA

3.1 **Four-fifths-rule report.** Vendor shall provide Operator with a quarterly report ("Fairness Report") showing the selection rate (rate at which Vendor's model produces an "accept" or above-cutoff recommendation) for each protected cohort under the Fair Housing Act (race, color, national origin, religion, sex, familial status, disability) where reportable demographics are lawfully available, and shall include the four-fifths-rule ratio against the highest-selection cohort.

3.2 **Trigger threshold.** If the four-fifths-rule ratio for any reportable cohort falls below 0.80, Vendor shall notify Operator within 5 business days, shall provide a written explanation of the suspected cause, and shall provide a remediation plan within 30 days.

3.3 **Voucher / source-of-income.** Vendor shall not use housing-voucher participation, source-of-income, or any feature directly correlated with these as an input to the score or recommendation in jurisdictions with source-of-income protections (currently CA, CT, DC, MA, MN, NJ, NY, OR, VT, WA — list maintained by Operator and updated quarterly).

3.4 **Disparate-impact remediation cooperation.** In the event of a regulatory inquiry, litigation, or Operator-initiated disparate-impact review, Vendor shall make available within 10 business days: (i) the model's reason-code distribution across the Operator's applicant population for the prior 12 months, (ii) the Fairness Report for the prior 12 months, (iii) the Vendor's internal disparate-impact testing methodology.

## Section 4 — Audit and Inspection

4.1 **Annual audit.** Operator shall have the right to conduct a remote audit of Vendor's compliance with this addendum no more than once per calendar year, on at least 30 days' written notice, at Operator's cost. Vendor shall make available: documentation responsive to Sections 1–3 above, model documentation per Section 2.1, and any internal audit reports relating to the AI services Vendor provides to Operator.

4.2 **Regulatory inquiry cooperation.** Vendor shall cooperate with Operator's response to any regulatory inquiry, subpoena, or enforcement action relating to Vendor's AI services to Operator, and shall make available within 15 business days of Operator's request any documentation reasonably required to respond.

## Section 5 — Term, Termination, and Survival

5.1 **Term.** This addendum shall be coterminous with the master services agreement between Operator and Vendor.

5.2 **Termination for cause.** Operator may terminate the master agreement for cause upon 30 days' written notice if Vendor materially breaches Sections 1, 2, or 3 and fails to cure within the notice period.

5.3 **Survival.** Sections 1.3 (retention), 1.4 (breach), 4.2 (regulatory cooperation), and any indemnity provisions shall survive termination for a period equal to the longer of: (i) 6 years, or (ii) the applicable statute of limitations for any claim arising from Vendor's services.

## What this addendum does NOT cover

- Indemnification (separate negotiation; consult counsel)
- Pricing, payment terms, or service-level credits (commercial negotiation)
- Insurance requirements (consult risk management)
- Jurisdiction-specific consumer-reporting agency licensing requirements (Vendor's responsibility; consult counsel for state-specific posture)
- HUD-funded-housing-specific compliance addenda (separate addendum if applicable)

## How to use this template

1. Have counsel review and adapt to the Operator's risk-appetite + the specific Vendor relationship
2. Include as Schedule [N] to the master services agreement renewal or as a standalone change-order
3. Pair runtime adoption with [ADR-0011 (Vendor-Output Adapter)](../adr/0011-vendor-output-adapter-pattern.md) — the adapter expects the data this addendum obligates the Vendor to provide
4. File the executed addendum in the Operator's contract repository with a 6-month renewal review reminder

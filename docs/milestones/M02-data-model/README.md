# M02 – Data model

≈ 13h · 11 work items · Starts after: [M01 – Org and repo](../M01-org-and-repo/README.md)

**Goal:** Every object and field in BRD §10 exists, with record types, layouts, the LAMS app and seed data for the four products.

**Exit criteria:** seed data loads; AC-09 EMI checks by hand on a record (₹8,979).

**Order inside this milestone:** LAMS-094 first (Account record types and Contact sharing come before any Account data), then LAMS-007 onwards.

## Work items

Tick items here; the linked file says what to build.

- [ ] [LAMS-094](094-account-record-types-individual-and-business-borrower.md) · Account record types Individual Borrower and Business Borrower (no Person Accounts) · `S`
- [ ] [LAMS-007](007-loan-product-c-product-document-c.md) · Loan_Product__c + Product_Document__c · `M`
- [ ] [LAMS-008](008-contact-custom-fields-pan-duplicate-rule.md) · Contact custom fields + PAN Duplicate Rule · `S`
- [ ] [LAMS-009](009-loan-application-c-fields-4-record-types.md) · Loan_Application__c fields, 4 record types, picklists · `L`
- [ ] [LAMS-010](010-application-document-c-roll-ups-docs-complete-c.md) · Application_Document__c, roll-ups, Docs_Complete__c · `M`
- [ ] [LAMS-011](011-formulas-risk-grade-emi-emi-to-income-ltv.md) · Formulas: Risk_Grade, EMI, EMI_To_Income, LTV · `M`
- [ ] [LAMS-012](012-loan-c-with-application-key-c-encrypted-payout.md) · Loan__c with Application_Key__c, encrypted Payout_Account__c · `M`
- [ ] [LAMS-013](013-emi-instalment-c-payment-c-loan-roll-ups-and.md) · EMI_Instalment__c, Payment__c, loan roll-ups and formulas · `M`
- [ ] [LAMS-014](014-case-record-type-fields-integration-log-c-loan.md) · Case record type + fields, Integration_Log__c, Loan_Event__e, CDC · `M`
- [ ] [LAMS-015](015-page-layouts-lightning-record-pages-dynamic.md) · Page layouts, Lightning record pages (Dynamic Forms), LAMS app, tabs · `L`
- [ ] [LAMS-016](016-seed-data-plans-4-products-checklists-demo.md) · Seed data plans: 4 products, checklists, demo borrowers · `S`

## Milestone exit checklist

- [ ] All work items above ticked
- [ ] Exit criteria demoed: seed data loads; AC-09 EMI checks by hand on a record (₹8,979).
- [ ] Deploys cleanly from source to the org
- [ ] Devlog entry written in [DEVLOG.md](../DEVLOG.md)
- [ ] BRD updated if the design changed

## Parking lot

_Bugs and ideas found during this milestone. Add them here; don't fix them in the current branch._

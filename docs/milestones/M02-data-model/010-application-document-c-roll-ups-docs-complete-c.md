# LAMS-010 · Application_Document__c, roll-ups, Docs_Complete__c

**Milestone:** [M02 – Data model](README.md) · **Size:** M (2–5h) · **Delivers:** BR-19

**Depends on:** LAMS-009 (Loan_Application__c); uses the `LAMS_Document_Type` global value set from LAMS-007

## Goal

Each application has its own document checklist rows (BR-16), each moving Requested → Uploaded → Verified or Rejected (BR-17, BR-18). Two roll-ups and a formula tell the application when every mandatory document is verified (BR-19), and the formula stays false when there are no mandatory rows at all (the v1 "0 = 0" bug, appendix #4).

## Build

**Object `Application_Document__c`** — label *Application Document*; Name = Auto Number `AD-{000000}` (proposed); enable Reports and Search (proposed).

| Field (API name) | Type | Details |
| --- | --- | --- |
| Loan_Application__c | Master-Detail(Loan_Application__c) | Sharing setting *Read/Write* (proposed; borrowers and officers with edit on the application can upload); reparenting off; related list label *Documents*; child relationship `Application_Documents` |
| Document_Type__c | Picklist (restricted) | Global value set `LAMS_Document_Type` |
| Mandatory__c | Checkbox | Default false (proposed). Copied from Product_Document__c when the checklist is created (LAMS-038) |
| Status__c | Picklist (restricted) | Requested (default), Uploaded, Verified, Rejected |
| Rejection_Reason__c | Text Area(255) (proposed type) | Required when Rejected (validation in LAMS-032); shown to the borrower |
| Verified_By__c | Lookup(User) | Child relationship `Verified_Application_Documents`; set when Verified or Rejected |
| Verified_Date__c | Date/Time (proposed type) | |

The file itself is a ContentDocument linked to the row (ContentDocumentLink), so no file field is needed. File type and size (PDF, JPG, PNG, ≤ 10 MB, BR-17) are enforced in the documentChecklist LWC (LAMS-045).

**Fields on `Loan_Application__c`**

| Field (API name) | Type | Definition |
| --- | --- | --- |
| Mandatory_Docs__c | Roll-Up Summary (COUNT) | Application_Document__c where `Mandatory__c = True` |
| Mandatory_Docs_Verified__c | Roll-Up Summary (COUNT) | Application_Document__c where `Mandatory__c = True` AND `Status__c = Verified` |
| Docs_Complete__c | Formula (Checkbox) | `AND(Mandatory_Docs__c > 0, Mandatory_Docs__c = Mandatory_Docs_Verified__c)` |

**Also:** on the Application Document layout, add the *Files* related list; on the Loan Application layout, add the *Documents* related list (Document Type, Mandatory, Status, Verified By).

## Steps

1. Create `Application_Document__c` with the Master-Detail field first, then the other fields.
2. Create the two roll-ups on Loan_Application__c, then the formula.
3. Update both page layouts.
4. Retrieve:
   `sf project retrieve start --metadata CustomObject:Application_Document__c CustomField:Loan_Application__c.Mandatory_Docs__c CustomField:Loan_Application__c.Mandatory_Docs_Verified__c CustomField:Loan_Application__c.Docs_Complete__c "Layout:Application_Document__c-Application Document Layout" "Layout:Loan_Application__c-Loan Application Layout"`
5. Test by hand with the four cases under *Done when*.
6. Commit: `feat(data-model): Application_Document__c, roll-ups and Docs_Complete__c [LAMS-010]`.

## Learn

- **Roll-up summaries need Master-Detail.** COUNT with a filter turns child rows into numbers the parent can test without Apex.
- **Formula fields are not reliable flow triggers:** a formula changes without a DML on the parent, so no record-triggered flow fires. That is why the Document Verified flow (LAMS-046) triggers on the child row, not on Docs_Complete__c.
- **Empty-set logic:** "all verified" is vacuously true for zero rows; the `> 0` guard makes "complete" mean at least one mandatory item exists.
- Master-Detail children have no owner; access follows the parent, and deleting the application deletes its documents.

## Done when

- [ ] Object, fields and both roll-ups exist in the org and in source
- [ ] Application with no documents: Docs_Complete__c = false
- [ ] Two mandatory + one optional row, one mandatory Verified: `Mandatory_Docs__c` = 2, `Mandatory_Docs_Verified__c` = 1, Docs_Complete__c = false
- [ ] Both mandatory Verified (optional still Requested): Docs_Complete__c = true
- [ ] Changing a verified mandatory row to Rejected makes Docs_Complete__c false again; deleting the application deletes its rows
- [ ] A PDF uploaded in the Files related list of a row shows on that row only
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.3 (Mandatory_Docs__c, Docs_Complete__c), §10.4 Application_Document__c; §13.2 Document Verified flow; Appendix #4; BR-16, BR-17, BR-18, BR-19

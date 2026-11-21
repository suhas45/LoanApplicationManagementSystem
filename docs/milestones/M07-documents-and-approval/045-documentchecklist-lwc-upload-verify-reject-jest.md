# LAMS-045 · documentChecklist LWC (upload, verify, reject) + Jest

**Milestone:** [M07 – Documents and approval](README.md) · **Size:** L (5–10h) · **Delivers:** BR-16 – BR-18

**Depends on:** LAMS-038 (checklist rows created at submission), LAMS-010 (Application_Document__c, roll-ups), LAMS-027 (borrowers have no FLS edit on Application_Document__c.Status__c), LAMS-032 (rejection-reason rule), LAMS-021 (labels)

## Goal

One component shows the application's checklist to staff and borrowers: anyone with access uploads a PDF, JPG or PNG up to 10 MB against an item (Requested → Uploaded, BR-17); only staff verify or reject, and a rejection needs a reason and allows a re-upload (BR-18). Verification is what later moves the application on (BR-19, LAMS-046).

## Build

**Apex `DocumentChecklistController`** (proposed name) — `public with sharing class`; every query `WITH USER_MODE`, so a borrower only ever sees their own rows.

| Method | Signature | Does |
| --- | --- | --- |
| Read | `@AuraEnabled(cacheable=true) static List<DocumentRow> getChecklist(Id applicationId)` | Rows ordered Mandatory first, then Document_Type__c: Id, Document_Type__c, Mandatory__c, Status__c, Rejection_Reason__c, Verified_By__r.Name, Verified_Date__c, latest file (ContentDocumentId, Title, FileExtension) from ContentDocumentLink |
| Staff? | `@AuraEnabled(cacheable=true) static Boolean canVerify()` | `UserInfo.getUserType() == 'Standard'` and edit access on Application_Document__c.Status__c |
| Upload | `@AuraEnabled static void markUploaded(Id documentId, List<Id> contentDocumentIds)` | Checks each file: FileExtension in pdf/jpg/jpeg/png and ContentSize ≤ 10,485,760 bytes; a bad file is deleted and `AuraHandledException(Label.LAMS_Doc_Invalid_File)` thrown. Sets the link `Visibility = 'AllUsers'` (staff and borrower both see the file). Then Status__c = Uploaded (from Requested or Rejected), Rejection_Reason__c cleared, parent Last_Activity_Date__c = now |
| Verify | `@AuraEnabled static void verifyDocument(Id documentId)` | Staff only (else `AuraHandledException`); requires Status Uploaded; Status__c = Verified, Verified_By__c = current user, Verified_Date__c = now |
| Reject | `@AuraEnabled static void rejectDocument(Id documentId, String reason)` | Staff only; blank reason → error (label `LAMS_VR_Doc_Rejection_Reason`); Status__c = Rejected, Rejection_Reason__c = reason |

**Status writes in system mode, narrowly** (borrowers have no FLS edit on Status__c): `markUploaded`, `verifyDocument` and `rejectDocument` first re-read the row with `WITH USER_MODE` (proves the caller can see it), then do the status update through a private `without sharing` inner class `StatusWriter` with one method `update(List<Application_Document__c>)`. Nothing else runs in system mode.

**LWC `documentChecklist`**

| API | Type | Purpose |
| --- | --- | --- |
| `@api recordId` | Id | Loan_Application__c Id (record page, portal record page) |
| `@api readOnly` | Boolean | Hide upload and verify/reject buttons (used inside the Secured Loan Review screens, LAMS-050) |
| Event `checklistchange` | CustomEvent, `detail: { documentId, status }` | Fired after every successful upload, verify or reject so a parent can react |

- Layout: `lightning-datatable` or a list of cards — type, Mandatory badge, status badge, file link (`/sfc/servlet.shepherd/document/download/{ContentDocumentId}` or `lightning/navigation` to the file preview), rejection reason.
- Upload: `lightning-file-upload` per row with `record-id={row.Id}`, `accept=".pdf,.jpg,.jpeg,.png"`, `onuploadfinished` → `markUploaded`. Shown when status is Requested or Rejected.
- Verify / Reject buttons: only when `canVerify` and status Uploaded. Reject opens `c-document-reject-modal` (proposed, extends `LightningModal`) with a required `lightning-textarea`.
- After any change: `refreshApex(this.wiredChecklist)` and `notifyRecordUpdateAvailable([{ recordId: this.recordId }])` so the record page's roll-ups and Docs_Complete__c refresh; toast via `ShowToastEvent` (label text).
- Labels (proposed): `LAMS_Doc_Title`, `LAMS_Doc_Upload`, `LAMS_Doc_Verify`, `LAMS_Doc_Reject`, `LAMS_Doc_Reason`, `LAMS_Doc_Mandatory`, `LAMS_Doc_Invalid_File`, `LAMS_Doc_Saved`; status values shown with their picklist labels (translated).
- Targets: `lightning__RecordPage` (Loan_Application__c), `lightningCommunity__Page`, `lightningCommunity__Default`.
- Accessibility: buttons carry `alternative-text` with the document type; modal traps focus (LightningModal does this).

## Steps

1. `sf apex generate class --name DocumentChecklistController --output-dir force-app/main/default/classes` and `DocumentChecklistControllerTest`.
2. `sf lightning generate component --type lwc --name documentChecklist --output-dir force-app/main/default/lwc`; same for `documentRejectModal`.
3. Write Jest tests in `__tests__/documentChecklist.test.js`; run `npm run test:unit -- --testPathPattern documentChecklist`.
4. Deploy: `sf project deploy start --source-dir force-app/main/default/classes --source-dir force-app/main/default/lwc`
5. Put the component on the application Lightning record pages (all four record types).
6. `sf apex run test --class-names DocumentChecklistControllerTest --code-coverage --result-format human --wait 10`
7. Commit: `feat(lwc): documentChecklist with upload, verify and reject [LAMS-045]`.

## Learn

- **`lightning-file-upload` with a child record Id** links the ContentDocument to that checklist row, not to the application; the link's **Visibility** (`AllUsers` vs `InternalUsers`) decides whether portal users can see the file.
- The upload component has no size limit attribute; enforce type and size on the server after upload (ContentVersion.ContentSize, FileExtension).
- **`WITH USER_MODE` + a tiny `without sharing` writer** is the pattern for "user may trigger this change but not edit the field directly".
- **Refreshing other components:** `notifyRecordUpdateAvailable` tells LDS the record changed, so roll-ups and formula fields elsewhere on the page update without a reload.

## Done when

- [ ] Staff and borrower both see the checklist; a borrower sees no Verify/Reject buttons and `verifyDocument` called as a portal user throws (Apex test with `System.runAs(portalUser)`)
- [ ] Uploading a 2 MB PDF moves the row to Uploaded; a .docx or an 11 MB file is refused and deleted
- [ ] Reject without a reason fails; with a reason → Rejected, the borrower can upload again and the row returns to Uploaded with the reason cleared
- [ ] Verify sets Verified_By__c and Verified_Date__c; the application's Mandatory_Docs_Verified__c updates on the page without reload
- [ ] A borrower calling `getChecklist` for another borrower's application gets no rows
- [ ] Jest: rows render from mocked `getChecklist`; buttons follow `canVerify` and status; reject modal requires text; `onuploadfinished` calls `markUploaded`; error shows a toast; `checklistchange` fires
- [ ] Apex: getChecklist with 200 rows; coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-16, BR-17, BR-18, BR-19, BR-59, §10.4 Application\_Document\_\_c, §13.1 document rule, §15 documentChecklist, NFR-11

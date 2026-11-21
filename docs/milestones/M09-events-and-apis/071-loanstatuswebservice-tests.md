# LAMS-071 · LoanStatusWebService + tests

**Milestone:** [M09 – Events and APIs](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-67

**Depends on:** LAMS-068 (Integration User, token), LAMS-012 / LAMS-013 (Loan__c with roll-ups and formulas), LAMS-059 (Days_Past_Due__c set nightly), LAMS-039 (IntegrationLogger)

## Goal

The legacy servicing system looks up a loan's status and outstanding amount by loan number over SOAP (BR-67), using the same Integration User as the REST APIs.

## Build

**Class** `global with sharing class LoanStatusWebService`

```apex
global class LoanStatusResult {
    webservice String  loanNumber;
    webservice Boolean found;
    webservice String  status;               // Loan__c.Status__c
    webservice Decimal outstandingPrincipal; // Outstanding_Principal__c
    webservice Decimal overdueAmount;        // Overdue_Amount__c
    webservice Date    nextDueDate;          // Next_Due_Date__c
    webservice Integer daysPastDue;          // Days_Past_Due__c
    webservice String  overdueBucket;        // Overdue_Bucket__c
    webservice String  errorMessage;
}
webservice static LoanStatusResult getLoanStatus(String loanNumber)
```

| Input | Result |
| --- | --- |
| Known loan number (`LN-000045`) | `found = true`, fields filled |
| Unknown number | `found = false`, `errorMessage` = label `LAMS_Loan_Not_Found` (proposed); no SOAP fault |
| Blank | `found = false`, `errorMessage` = label `LAMS_Loan_Number_Required` (proposed) |

Outstanding principal and overdue amount are returned separately; the caller adds them if it needs a payoff figure.

**Endpoint and auth**

| Item | Value |
| --- | --- |
| WSDL | Setup → Apex Classes → LoanStatusWebService → *Generate WSDL* (or `https://<mydomain>.my.salesforce.com/services/wsdl/class/LoanStatusWebService`) |
| Endpoint | `POST https://<mydomain>.my.salesforce.com/services/Soap/class/LoanStatusWebService` |
| Headers | `Content-Type: text/xml; charset=UTF-8`, `SOAPAction: ""` |
| Auth | `<SessionHeader><sessionId>` = the client credentials access token (LAMS-068) |

Request body (short):

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:lam="http://soap.sforce.com/schemas/class/LoanStatusWebService">
  <soapenv:Header><lam:SessionHeader><lam:sessionId>{{accessToken}}</lam:sessionId></lam:SessionHeader></soapenv:Header>
  <soapenv:Body><lam:getLoanStatus><lam:loanNumber>LN-000045</lam:loanNumber></lam:getLoanStatus></soapenv:Body>
</soapenv:Envelope>
```

**Logging:** Integration__c `Loan Status SOAP`, Direction__c `Inbound`, Related_Record_Id__c = loan Id when found.

**Access:** the Integration User reads any loan through View All (read) on `Loan__c` (§11); add the class to `LAMS_Integration` Apex Class Access.

## Steps

1. Write the class; keep the query to the fields above (`WITH USER_MODE`).
2. Add it to `LAMS_Integration` Apex Class Access; deploy.
3. Write `LoanStatusWebServiceTest` calling `LoanStatusWebService.getLoanStatus(...)` directly: found (Active loan with one overdue instalment), unknown, blank, log row written; run once as a user with only `LAMS_Integration` (`System.runAs`) to prove access.
4. Generate the WSDL and save it as `postman/LoanStatusWebService.wsdl` for the legacy team; add the SOAP request to Postman (LAMS-073).
5. `sf apex run test --class-names LoanStatusWebServiceTest --code-coverage --result-format human`
6. Commit: `feat(api): LoanStatusWebService SOAP lookup [LAMS-071]`.

## Learn

- **`webservice` keyword:** methods must be `webservice static` in a `global` class; fields of a returned inner class are exposed only when marked `webservice`. Salesforce generates the WSDL for you.
- Inbound SOAP uses the standard SOAP session header; any valid OAuth access token with `api` scope works as the session Id.
- A business "not found" as a normal response (`found=false`) is easier for legacy clients than a SOAP fault, which most of them treat as a transport error.
- Changing a `webservice` signature breaks the WSDL contract for existing clients; add a new method instead of changing one.

## Done when

- [ ] Postman SOAP request for a demo loan returns status, outstanding principal and overdue amount (BR-67)
- [ ] An unknown loan number returns `found=false`, not a fault
- [ ] Each call writes a Loan Status SOAP log row
- [ ] WSDL saved in `postman/`
- [ ] `LoanStatusWebServiceTest` passes with ≥ 90% coverage
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §14 LoanStatusWebService, §16 Legacy servicing row, §10.5 Loan__c, §11 `LAMS_Integration`, BR-65, BR-67

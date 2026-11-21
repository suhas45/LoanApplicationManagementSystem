# LAMS-016 · Seed data plans: 4 products, checklists, demo borrowers

**Milestone:** [M02 – Data model](README.md) · **Size:** S (≤ 2h) · **Delivers:** §5

**Depends on:** LAMS-007 (products and checklist objects), LAMS-008 (Contact fields), LAMS-094 (Account record types Individual Borrower / Business Borrower); LAMS-011 for the AC-09 check at the end

## Goal

Any org can be loaded with the four products from §5, their document checklists and a set of demo borrowers by two `sf data import tree` commands. That is build step 2's done-when, and it gives every later milestone the same test data, with borrowers built to trigger the mock failure rules from LAMS-006.

## Build

**Files under `data/`**

| File | Contents |
| --- | --- |
| `data/products-plan.json` | Plan: `Loan_Product__c` then `Product_Document__c` |
| `data/Loan_Product__c.json` | 4 products, `referenceId` = product code |
| `data/Product_Document__c.json` | 21 checklist rows, `Loan_Product__c` = `@PL`, `@HL`, … |
| `data/borrowers-plan.json` | Plan: `Account` then `Contact` |
| `data/Account.json` | 7 Accounts, one per borrower: 6 with record type Individual Borrower (Account Name = the person's full name) and 1 business Account *Iyer Traders* (record type Business Borrower) |
| `data/Contact.json` | 7 Contacts, one per Account, `AccountId` = `@ACC1`, …; the borrower fields from LAMS-008 live here |
| `scripts/load-borrowers.sh` (proposed) | Looks up the two Account record type Ids, writes copies of the files with the placeholders replaced, and runs the import (record type Ids differ per org, and import tree cannot look them up by name) |

**Products** (§5; percent values are written as whole numbers, so `14` means 14%)

| Name | Code | Min–Max amount | Tenure | Rate | Min score | Min income | Max EMI/income | Max LTV | Max age | Fee | Late fee | Grace | Field verif. | Record type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Personal Loan | PL | 50000 – 1000000 | 12–60 | 14 | 700 | 25000 | 50 | – | 60 | 2 | 2 | 5 | false | Personal |
| Home Loan | HL | 1000000 – 50000000 | 60–360 | 9 | 720 | 50000 | 55 | 80 | 70 | 0.5 | 2 | 5 | true | Home |
| Auto Loan | AL | 100000 – 5000000 | 12–84 | 11 | 680 | 30000 | 50 | 85 | 65 | 1 | 2 | 5 | false | Auto |
| Small-Business Loan | BL | 200000 – 10000000 | 12–60 | 15 | 700 | 75000 | 60 | – | 65 | 2 | 2 | 5 | true | Business |

All four: `Active__c` true. `Auto_Approve_Eligible__c` true for PL only (BRD v2.1).

**Checklists** (proposed: the BRD lists the document types but not which product needs which). M = Mandatory__c true, O = optional.

| Document type | PL | HL | AL | BL |
| --- | --- | --- | --- | --- |
| PAN Card | M | M | M | M |
| Address Proof | M | M | M | M |
| Salary Slips | M | M | M | – |
| Bank Statement | M | M | O | M |
| ITR | O | O | – | M |
| GST Certificate | – | – | – | M |
| Property Papers | – | M | – | – |
| Vehicle Quotation | – | – | M | – |
| **Rows** | 5 | 6 | 5 | 5 |

**Demo borrowers** (proposed; fictitious PANs in valid format; emails use `example.com`). The 9th PAN character drives the mocks from LAMS-006.

| Ref | Account / Contact | PAN | Birthdate | Employment | Monthly income | Existing EMI | Language | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ACC1 | Aarav Sharma | AAAPS1001A | 1990-04-12 | Salaried | 80000 | 0 | English | PL happy path, AC-01, AC-09; portal borrower 1 |
| ACC2 | Priya Nair | AAAPN1002B | 1985-09-30 | Salaried | 150000 | 10000 | Hindi | HL ₹60 lakh, AC-03; Hindi emails; portal borrower 2 |
| ACC3 | Rohan Mehta | AAAPM1003C | 1992-01-15 | Salaried | 60000 | 5000 | English | Auto loan, LTV and dealer payout |
| ACC4 | Iyer Traders / Kavya Iyer | AAAPI1004D | 1980-06-05 | Business | 200000 | 15000 | English | Small-Business loan, field verification |
| ACC5 | Arjun Rao | AAAPR1007G | 1988-11-20 | Salaried | 55000 | 0 | English | KYC Rejected → Fail (BR-13) |
| ACC6 | Neha Gupta | AAAPG1008F | 1993-03-08 | Self-Employed | 45000 | 3000 | English | Bureau score 685 → Refer (BR-12) |
| ACC7 | Vikram Singh | AAAPS1009E | 1987-07-25 | Salaried | 70000 | 0 | English | Bureau 503 → manual override (BR-15, AC-05) |

ACC4 is the only business borrower: Account *Iyer Traders* (Business Borrower) with director Contact *Kavya Iyer*, whose Contact gets the PAN and the other borrower fields and becomes Borrower__c on the Small-Business application (§10.1). Each of the others is an Individual Borrower Account named after the person, with that person as its one Contact.

Every Contact: `KYC_Status__c` Pending, `Email` `firstname.lastname@example.com`, `MobilePhone` `+919000000001` … `+919000000007`.

Borrower records file shapes (`data/Account.json`, `data/Contact.json`, first records shown; `RT_INDIVIDUAL_BORROWER` and `RT_BUSINESS_BORROWER` are the placeholders the load script replaces):

```json
{
  "records": [
    {
      "attributes": { "type": "Account", "referenceId": "ACC1" },
      "RecordTypeId": "RT_INDIVIDUAL_BORROWER",
      "Name": "Aarav Sharma"
    },
    {
      "attributes": { "type": "Account", "referenceId": "ACC4" },
      "RecordTypeId": "RT_BUSINESS_BORROWER",
      "Name": "Iyer Traders"
    }
  ]
}
```

```json
{
  "records": [
    {
      "attributes": { "type": "Contact", "referenceId": "CON1" },
      "AccountId": "@ACC1",
      "FirstName": "Aarav",
      "LastName": "Sharma",
      "Birthdate": "1990-04-12",
      "Email": "aarav.sharma@example.com",
      "MobilePhone": "+919000000001",
      "PAN__c": "AAAPS1001A",
      "Employment_Type__c": "Salaried",
      "Monthly_Income__c": 80000,
      "Existing_EMI__c": 0,
      "Preferred_Language__c": "English",
      "KYC_Status__c": "Pending"
    },
    {
      "attributes": { "type": "Contact", "referenceId": "CON4" },
      "AccountId": "@ACC4",
      "FirstName": "Kavya",
      "LastName": "Iyer",
      "Birthdate": "1980-06-05",
      "Email": "kavya.iyer@example.com",
      "MobilePhone": "+919000000004",
      "PAN__c": "AAAPI1004D",
      "Employment_Type__c": "Business",
      "Monthly_Income__c": 200000,
      "Existing_EMI__c": 15000,
      "Preferred_Language__c": "English",
      "KYC_Status__c": "Pending"
    }
  ]
}
```

Example product records file shape:

```json
{
  "records": [
    {
      "attributes": { "type": "Loan_Product__c", "referenceId": "PL" },
      "Name": "Personal Loan",
      "Product_Code__c": "PL",
      "Min_Amount__c": 50000,
      "Max_Amount__c": 1000000,
      "Interest_Rate__c": 14,
      "Requires_Field_Verification__c": false,
      "Auto_Approve_Eligible__c": true,
      "Record_Type_Name__c": "Personal",
      "Active__c": true
    }
  ]
}
```

Plan file shape (`data/products-plan.json`):

```json
[
  { "sobject": "Loan_Product__c", "files": ["Loan_Product__c.json"] },
  { "sobject": "Product_Document__c", "files": ["Product_Document__c.json"] }
]
```

Current CLI versions resolve `@` references between plan steps automatically; older ones needed `"saveRefs": true` on the parent step and `"resolveRefs": true` on the child.

## Steps

1. Optional shortcut: create one product and its rows by hand, then generate the file shape with
   `sf data export tree --query "SELECT Name, Product_Code__c, (SELECT Document_Type__c, Mandatory__c FROM Product_Documents) FROM Loan_Product__c" --plan --output-dir data`
   and delete those records before importing.
2. Write the six files in `data/` and the load script.
3. Load: `sf data import tree --plan data/products-plan.json --target-org Lams`
4. Load borrowers: `bash scripts/load-borrowers.sh Lams`. The script runs `sf data query --query "SELECT Id, DeveloperName FROM RecordType WHERE SobjectType = 'Account' AND DeveloperName IN ('Individual_Borrower', 'Business_Borrower')" --json`, replaces the placeholders in copies under `data/.tmp/` (git-ignored), then runs `sf data import tree --plan data/.tmp/borrowers-plan.json --target-org Lams`.
5. Check counts:
   `sf data query --query "SELECT Loan_Product__r.Product_Code__c code, COUNT(Id) n FROM Product_Document__c GROUP BY Loan_Product__r.Product_Code__c"`,
   `sf data query --query "SELECT COUNT() FROM Contact WHERE PAN__c != null"` (7) and
   `sf data query --query "SELECT RecordType.DeveloperName, COUNT(Id) n FROM Account GROUP BY RecordType.DeveloperName"` (Individual_Borrower 6, Business_Borrower 1).
6. AC-09 by hand: new Personal application for Aarav Sharma, PL, ₹1,00,000, 12 months → EMI ₹8,979.
7. To reload, delete first (import tree only inserts): `delete [SELECT Id FROM Loan_Product__c];` in Execute Anonymous removes products and, through Master-Detail, their rows. Delete the borrower Accounts the same way; deleting an Account also deletes its Contacts.
8. Commit: `feat(data): seed plans for products, checklists and demo borrowers [LAMS-016]`.

## Learn

- **`sf data import tree`** inserts parent and child records in one plan, linking them by `referenceId`; it never updates, so re-running fails on unique fields (Product_Code__c, PAN__c). That is a useful guard against double loads.
- **Percent fields through the API** take whole numbers (14), while formulas see 0.14.
- **Seed data is data, not metadata:** CI never deploys it, so each new org needs these commands (list them in the README in LAMS-092).
- The PAN duplicate rule and unique field also apply to API inserts, so two demo borrowers can never share a PAN.
- **One Account per borrower:** each individual gets their own Individual Borrower Account rather than sharing one, which avoids account data skew and lets the Contact inherit its sharing from the Account (Controlled by Parent, LAMS-026).

## Done when

- [ ] `data/` holds the six files, the load script exists and both loads succeed on the org
- [ ] SOQL shows 4 active products and checklist counts PL 5, HL 6, AL 5, BL 5
- [ ] 6 Individual Borrower Accounts and 1 Business Borrower Account (Iyer Traders) exist, each with one Contact carrying the PAN above
- [ ] Running the products plan a second time fails on the unique Product_Code__c
- [ ] The AC-09 application shows EMI ₹8,979 (M02 exit criterion)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §5 Products (seed values); §10.1 Borrower (Individual Borrower and Business Borrower Accounts); §10.2 Product_Document__c; §16 mock behaviour; §19 Seed data row; §20 step 2 done-when; BR-02, BR-12, BR-13, BR-15, BR-16; AC-01, AC-03, AC-05, AC-09

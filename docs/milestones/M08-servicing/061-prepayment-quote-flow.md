# LAMS-061 · Prepayment Quote flow

**Milestone:** [M08 – Servicing](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-44

**Depends on:** LAMS-014 (Case record type Loan Service Request, Prepayment_Quote_Amount__c), LAMS-058 (payoff rule the quote must match), LAMS-062 (Send Notification and template `LAMS_Prepayment_Quote`; build LAMS-062 first)

## Goal

When a borrower asks for a prepayment quote, the payoff amount is calculated, written to the Case and emailed to the borrower. Paying exactly that amount closes the loan through allocation (BR-44).

## Build

**Flow `Prepayment_Quote`** (label *Prepayment Quote*), record-triggered, after save, on `Case`.

| Setting | Value |
| --- | --- |
| Trigger | A record is created or updated |
| Entry conditions | `RecordType.DeveloperName` = Loan_Service_Request AND `Request_Type__c` = Prepayment Quote AND `Loan__c` is not null |
| When to run | Only when a record is updated to meet the condition requirements |

Elements:

1. **Get Records** `Loan__c` = `{!$Record.Loan__c}` (Status__c, Name, Borrower__c, Outstanding_Principal__c).
2. **Decision:** Status__c ≠ Active → leave the amount blank and finish. An officer answers by hand.
3. **Get Records** (all) `EMI_Instalment__c` where Loan__c = loan, `Due_Date__c` ≤ `{!$Flow.CurrentDate}`, Status__c not in (Paid, Cancelled). These are the rows already due.
4. **Loop** them. Add each row's unpaid late fee + interest to `dues`:
   `MAX(0, Late_Fee__c + Interest_Component__c − Amount_Paid__c)`. Amount_Paid__c pays the fee and interest first, so this is the unpaid part.
5. **Formula** `payoff` = `Outstanding_Principal__c + dues`. This is outstanding principal plus dues (BR-44), and it is the same number PaymentAllocationService uses as payoff(D) for a payment made today.
6. **Update Records** on the triggering Case: `Prepayment_Quote_Amount__c` = payoff.
7. **Subflow** `Send_Notification`: templateName = `LAMS_Prepayment_Quote`, recipientId = `{!$Record.ContactId}` (or Loan.Borrower__c when ContactId is blank), recordId = `{!$Record.Id}`.

§13.2 writes the payoff as Outstanding_Principal + Overdue_Amount. Overdue_Amount__c already contains the overdue rows' unpaid principal, which is also inside Outstanding_Principal__c, so that version counts it twice. This flow adds only the unpaid fee and interest of due rows. Record the change in the BRD.

The quote is valid until the next due date or the next nightly late fee, whichever comes first. Say so in the email template (LAMS-062).

## Steps

1. Build the flow. Debug it on a Case for the AC-09 loan after 3 EMIs are paid → quote ₹76,289.
2. Debug again with row 4 Overdue and a ₹180 late fee, unpaid → quote = ₹76,289 + ₹180 + ₹890 (row 4 interest) = ₹77,359.
3. Add a Flow test (Flow Builder → View Tests; record-triggered flows support them): create a Case with Request_Type Prepayment Quote and assert Prepayment_Quote_Amount__c.
4. End-to-end check: insert a Payment__c for exactly the quoted amount → loan Closed, Closure_Type Prepaid, future rows Cancelled (LAMS-058).
5. Retrieve: `sf project retrieve start --metadata Flow:Prepayment_Quote`
6. Commit: `feat(flow): Prepayment Quote record-triggered flow [LAMS-061]`.

## Learn

- **Before-save vs after-save:** a before-save flow could set the amount faster, but it cannot call a subflow or send email. One after-save flow that updates `$Record` is simpler here.
- **Bulkification in record-triggered flows:** Get Records inside one interview is batched across the interviews of the same transaction, so 200 Cases inserted together do not use 200 queries.
- Keep one definition of "payoff". If the quote and the allocation use different formulas, a borrower who pays the quote is left with a ₹1 balance and an open loan.

## Done when

- [ ] Creating a Prepayment Quote Case on an Active loan fills Prepayment_Quote_Amount__c with outstanding principal + unpaid fee and interest on due rows (₹76,289 in the 3-EMIs-paid example)
- [ ] The borrower receives the Prepayment Quote email in their language
- [ ] A payment of the quoted amount closes the loan as Prepaid and cancels future instalments
- [ ] A Case on a non-Active loan gets no amount and no email
- [ ] The Flow test passes
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.7 BR-44, §6.10 BR-57, §10.5 Outstanding_Principal__c, Overdue_Amount__c, §10.8 Case Prepayment_Quote_Amount__c, §13.2 Prepayment Quote, §15 email template Prepayment Quote

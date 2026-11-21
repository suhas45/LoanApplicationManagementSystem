# LAMS-006 · Create public mock endpoints (Beeceptor/Postman) with success and failure responses

**Milestone:** [M01 – Org and repo](README.md) · **Size:** M (2–5h) · **Delivers:** D2, §16

**Depends on:** LAMS-002 (`docs/ORG_NOTES.md` exists to record the URLs). Independent of LAMS-003 – LAMS-005.

## Goal

Each of the five outbound systems (Credit Bureau, KYC, Payout, SMS, Core Banking) has a mock reachable from the internet that returns a success and at least one failure chosen by a request value (dependency D2, assumption A4). Retries, *Gave Up* and the manual-override path (BR-15, BR-36, BR-66, BR-69) can then be demonstrated without real systems.

## Build

**Tool:** Beeceptor (proposed), one endpoint per integration, because its rules can match on the request body; a failure can then be triggered by data such as the PAN. If a free-plan cap (rules per endpoint, requests per day) is too low, move that integration to a Postman mock server, where the failure is chosen with the `x-mock-response-code` header instead of the body. Mockoon only counts if exposed through a public tunnel (§16).

**Endpoints and contracts (all proposed; add a suffix to a subdomain if it is taken)**

| Integration (Named Credential in LAMS-040) | Base URL | Method + path | Request (JSON unless noted) | Success |
| --- | --- | --- | --- | --- |
| Credit_Bureau | `https://lams-bureau.free.beeceptor.com` | `POST /v1/credit-score` | `pan`, `fullName`, `dateOfBirth`, `correlationId` | `200 {"pan":"…","score":790,"reportId":"CB-1001","status":"OK"}` |
| KYC_Service (SOAP 1.1) | `https://lams-kyc.free.beeceptor.com` | `POST /kyc`, `Content-Type: text/xml`, `SOAPAction: verifyKyc` | `verifyKycRequest`: `pan`, `fullName`, `dateOfBirth`, `correlationId` | `200` envelope with `status` = Verified, `referenceId` = KYC-1001 |
| Payout_Service | `https://lams-payout.free.beeceptor.com` | `POST /v1/payouts` | `loanNumber`, `amount`, `accountNumber`, `ifsc`, `beneficiaryName`, `correlationId` | `200 {"status":"SUCCESS","utr":"UTR2026000001"}` |
| SMS_Gateway | `https://lams-sms.free.beeceptor.com` | `POST /v1/messages` | `messages`: array of `{to, text}` (up to 100, matching SmsService chunks) | `202 {"accepted":<n>}` |
| Core_Banking | `https://lams-corebank.free.beeceptor.com` | `POST /v1/postings` | `type` (DISBURSEMENT or PAYMENT), `reference`, `loanNumber`, `amount`, `valueDate`, `correlationId` | `201 {"postingId":"CBS-1001","status":"POSTED"}` |

Every mock echoes the `X-Correlation-Id` request header in its response headers (proposed), so log rows (BR-65) can be matched.

**Failure rules** (evaluated before the success rule). PAN format is `AAAAA9999A`, so "the 9th character" is the last digit. The demo borrowers in LAMS-016 are built around these values.

| Mock | Condition | Response | Demonstrates |
| --- | --- | --- | --- |
| Bureau | PAN 9th character `9` (body regex `"pan"\s*:\s*"[A-Z]{5}[0-9]{3}9[A-Z]"`) | `503 {"error":"SERVICE_UNAVAILABLE"}` | Retries → Gave Up → manual override (BR-15, AC-05) |
| Bureau | PAN 9th character `8` | `200` with `score` 685 | Refer result for PL (15 points under 700, BR-12) |
| Bureau (optional) | PAN 9th character `5` | `200` success after a 30 s delay, if the plan allows delays | Slow bureau (AC-04) |
| KYC | PAN 9th character `7` | `200` with `status` = Rejected, `reason` = NAME_MISMATCH | KYC Rejected → Fail (BR-13) |
| KYC | PAN 9th character `6` | `500` SOAP Fault (`faultcode` soap:Server) | SOAP error handling and retry |
| Payout | `accountNumber` ends in `9` | `503 {"status":"FAILED","error":"BANK_UNAVAILABLE"}` | Retryable payout failure (BR-36, AC-08) |
| Payout | `accountNumber` ends in `8` | `422 {"status":"FAILED","error":"INVALID_ACCOUNT"}` | Non-retryable failure → task |
| SMS | any `to` ending in `9` | `500 {"error":"GATEWAY_ERROR"}` | Fire-and-forget failure is logged |
| Core Banking | `reference` ends in `9` | `503 {"error":"CBS_DOWN"}` | Retry to Gave Up (M09 exit) |

**KYC WSDL** (dependency D3; proposed, document/literal, one operation so WSDL2Apex in LAMS-042 can parse it). Save as `mocks/kyc/KycService.wsdl`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<definitions name="KycService" targetNamespace="http://lams.example.com/kyc"
  xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  xmlns:tns="http://lams.example.com/kyc" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <types>
    <xsd:schema targetNamespace="http://lams.example.com/kyc" elementFormDefault="qualified">
      <xsd:element name="verifyKycRequest">
        <xsd:complexType><xsd:sequence>
          <xsd:element name="pan" type="xsd:string"/>
          <xsd:element name="fullName" type="xsd:string"/>
          <xsd:element name="dateOfBirth" type="xsd:date"/>
          <xsd:element name="correlationId" type="xsd:string"/>
        </xsd:sequence></xsd:complexType>
      </xsd:element>
      <xsd:element name="verifyKycResponse">
        <xsd:complexType><xsd:sequence>
          <xsd:element name="status" type="xsd:string"/>
          <xsd:element name="referenceId" type="xsd:string"/>
          <xsd:element name="reason" type="xsd:string" minOccurs="0"/>
        </xsd:sequence></xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </types>
  <message name="verifyKycInput"><part name="parameters" element="tns:verifyKycRequest"/></message>
  <message name="verifyKycOutput"><part name="parameters" element="tns:verifyKycResponse"/></message>
  <portType name="KycPortType">
    <operation name="verifyKyc"><input message="tns:verifyKycInput"/><output message="tns:verifyKycOutput"/></operation>
  </portType>
  <binding name="KycBinding" type="tns:KycPortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="verifyKyc">
      <soap:operation soapAction="verifyKyc"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
  </binding>
  <service name="KycService">
    <port name="KycPort" binding="tns:KycBinding">
      <soap:address location="https://lams-kyc.free.beeceptor.com/kyc"/>
    </port>
  </service>
</definitions>
```

The success response body the KYC mock returns:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:kyc="http://lams.example.com/kyc">
  <soapenv:Body>
    <kyc:verifyKycResponse>
      <kyc:status>Verified</kyc:status>
      <kyc:referenceId>KYC-1001</kyc:referenceId>
    </kyc:verifyKycResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

**In the repo:** `mocks/<integration>/` holds one example file per response (`success.json`, `failure-503.json`, … ; `.xml` for KYC) so the mocks can be rebuilt and the same bodies reused as `Mock_Response__c` values in LAMS-018. Base URLs and plan limits go in a *Mock endpoints* section of `docs/ORG_NOTES.md`. No credentials: the mocks are open, and External Credentials (LAMS-040) get dummy values.

## Steps

1. Create the five Beeceptor endpoints. For each, add the failure rules first, then a catch-all success rule for the same method and path; set `Content-Type` on every response.
2. Write `mocks/kyc/KycService.wsdl` and the example response files.
3. Test each rule from PowerShell with `curl.exe` (plain `curl` is an alias for `Invoke-WebRequest` in Windows PowerShell 5.1):
   `curl.exe -i -X POST https://lams-bureau.free.beeceptor.com/v1/credit-score -H "Content-Type: application/json" -d '{\"pan\":\"AAAPS1001A\"}'` → 200, score 790
   Same with `AAAPS1009E` → 503; `AAAPG1008F` → 200, score 685. If PowerShell mangles the quotes, put the body in a file and send `--data-binary "@mocks/credit-bureau/request.json"`.
4. Repeat for KYC (send the SOAP envelope from a file with `--data-binary "@mocks/kyc/request.xml"`), Payout, SMS and Core Banking.
5. Record base URLs, paths, rule list and free-plan limits in `docs/ORG_NOTES.md`.
6. Commit: `chore(mocks): public mock endpoints and response contracts [LAMS-006]`.

## Learn

- **Salesforce calls out from its own servers**, so `localhost` or a laptop-only Mockoon is unreachable; the endpoint must be public HTTPS (D2).
- **Contract first:** fixing paths and JSON shapes now lets LAMS-018 (`Path__c`, `Mock_Response__c`), LAMS-040 (Named Credentials) and the HttpCalloutMock tests in LAMS-041 share one definition.
- **Data-driven failures** (a PAN digit, an account suffix) let one demo walk both the success and the failure path without editing the mock.
- WSDL2Apex supports a limited subset of WSDL: no imports, one binding style, simple types. Keep the WSDL small and document/literal.

## Done when

- [ ] Five public endpoints respond over HTTPS from outside your network (test once from your phone's browser or a second network)
- [ ] Every row of the failure-rules table returns the stated status code, checked with `curl.exe`, and the default request returns the success response
- [ ] `mocks/kyc/KycService.wsdl` and the example response files are committed
- [ ] `docs/ORG_NOTES.md` lists base URLs, paths and plan limits
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §16 Integrations (mock behaviour); §10.11 Integration_Setting__mdt; §8 A4, D2, D3; BR-12, BR-13, BR-15, BR-36, BR-65, BR-66, BR-69; AC-04, AC-05, AC-08

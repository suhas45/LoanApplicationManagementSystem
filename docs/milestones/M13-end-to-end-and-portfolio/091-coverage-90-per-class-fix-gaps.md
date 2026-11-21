# LAMS-091 · Coverage ≥ 90% per class; fix gaps

**Milestone:** [M13 – End to end and portfolio](README.md) · **Size:** M (2–5h) · **Delivers:** NFR-10

**Depends on:** LAMS-090 (fixes from the end-to-end run are in), LAMS-004 (CI)

## Goal

Every Apex class and trigger has at least 90% coverage. Each class's tests include bulk, negative, toggle on/off and callout-mock cases where they apply (NFR-10). The success metric "Apex test coverage ≥ 90% per class" (§9) is then measured, not assumed.

## Build

**Measure**

| What | Command |
| --- | --- |
| Full run with per-class coverage | `sf apex run test --test-level RunLocalTests --code-coverage --detailed-coverage --result-format human --output-dir test-results --wait 30` |
| Per class or trigger, from the org | `sf data query --use-tooling-api --query "SELECT ApexClassOrTrigger.Name, NumLinesCovered, NumLinesUncovered FROM ApexCodeCoverageAggregate ORDER BY ApexClassOrTrigger.Name" --result-format csv > test-results/coverage.csv` |
| Org-wide | `sf data query --use-tooling-api --query "SELECT PercentCovered FROM ApexOrgWideCoverage"` |
| LWC (Jest) | `npm run test:unit:coverage` |

Coverage % = NumLinesCovered ÷ (NumLinesCovered + NumLinesUncovered). `ApexCodeCoverageAggregate` keeps results from earlier runs. Before the final measurement, clear test history (Setup → Apex Test Execution → Options / Clear All Test History, or as your release names it), then do one full run.

**Coverage report** `docs/COVERAGE.md` (proposed). One row per class and trigger in §14, plus every other class in `force-app`: controllers, agent actions, grounding and parsers. `@isTest` classes such as TestDataFactory are not counted. The first row shows how to fill it in:

| Class | Coverage | Bulk 200 | Negative | Toggle on/off | Callout mock | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| CreditBureauService (example) | 94% | ✔ | ✔ | ✔ (Bureau_Mock_Mode__c) | HttpCalloutMock | |
| … | | | | | | |

Mark a column "n/a" only when it really does not apply (for example, no callout in OwnerAssignmentService).

**Common gaps and how to close them**

| Uncovered code | Fix |
| --- | --- |
| `catch` blocks after callouts | HttpCalloutMock or WebServiceMock that returns 500, times out (throws `CalloutException`) or returns malformed JSON |
| Toggle-off branches | Set the LAMS_Settings__c org default (or user-level for Agentforce_Enabled__c) in the test, then assert the skip and the fallback (BR-80) |
| Queueable chains | `Test.startTest()` / `Test.stopTest()` runs one level; test each queueable alone and assert that it enqueued the next (`Limits.getQueueableJobs()`) |
| Batch `finish` and Schedulable `execute` | Run the batch inside start/stop; call `System.schedule` with a cron string and assert the CronTrigger |
| @future (SmsService) | 200 recipients → assert 2 future calls (chunks of 100) |
| REST and SOAP endpoints | Build `RestContext.request` / `response` for 400, 503 (toggle off), duplicate; call the SOAP method directly with an unknown loan number |
| Sharing paths | `System.runAs` with users from TestDataFactory: owner, manager, Operations, portal |
| Agent actions calling ConnectApi | Use the `SummaryGenerator` stub (LAMS-084); keep the real ConnectApi call to a few lines |
| Triggers | One insert, one update and one 200-record test per trigger; the trigger body only calls the handler |
| Dead code | Delete it rather than write a test for it |

Do not chase coverage with assert-free tests. Each new test asserts an outcome.

**Keep it enforced (proposed).** Add a CI step after the validate deploy that fails the build when any class is below 90%. For example, a small script reads the `--detailed-coverage` JSON output from `sf apex run test --result-format json` and checks each class. Platform deploys only enforce 75%.

## Steps

1. Clear test history, then run the full test command and the tooling query. Save `test-results/coverage.csv` (keep `test-results/` out of git, or add it to `.gitignore`).
2. List every class under 90%, and every class whose tests miss a bulk, negative, toggle or mock case.
3. For each gap, open the class's uncovered lines (`--detailed-coverage` output, or the Developer Console coverage view) and add tests from the table above. Fix any bug the new tests expose. If the fix is larger than the test, give it its own item number.
4. Rerun until every class is at 90% or above and all tests pass. Run the suite twice to catch flaky tests (timing, `Datetime.now()`, unordered queries).
5. Write `docs/COVERAGE.md` with the final numbers, the org-wide figure and the Jest coverage summary.
6. Optional: add the CI coverage gate and confirm it fails on a deliberately low class, then passes.
7. Commit: `test(apex): raise every class to 90% coverage, add coverage report [LAMS-091]`.

## Learn

- **Coverage ≠ quality:** the platform counts executed lines, so a test with no asserts can still reach 100%. NFR-10's bulk, negative, toggle and mock cases are what make the tests mean something.
- **Aggregate vs per-run:** the org keeps the best coverage seen per class across runs until you clear history. Measure on a clean, full run.
- **Testability is designed in:** seams like the SummaryGenerator interface, `@TestVisible` hooks and callout mocks make the hard-to-reach branches reachable.

## Done when

- [ ] A clean full run of `sf apex run test --test-level RunLocalTests --code-coverage` passes with every class and trigger at ≥ 90%
- [ ] `docs/COVERAGE.md` lists each class with its coverage and the bulk, negative, toggle and mock cases, with no unexplained gaps
- [ ] The suite passes twice in a row (no flaky tests)
- [ ] Jest tests pass for every LWC
- [ ] CI is green on `main`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §7 NFR-10, §9 success metric "Apex test coverage ≥ 90% per class", §14 Tests paragraph and class list, §12 toggle testing rule, BR-80, §19 CI, §20 step 13

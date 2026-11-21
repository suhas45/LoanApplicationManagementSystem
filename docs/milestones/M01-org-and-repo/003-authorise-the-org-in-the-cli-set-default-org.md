# LAMS-003 · Authorise the org in the CLI; set default org and API version

**Milestone:** [M01 – Org and repo](README.md) · **Size:** S (≤ 2h) · **Delivers:** §19

**Depends on:** LAMS-002 (the org exists)

## Goal

The Salesforce CLI on this machine is logged in to the LAMS org under a fixed alias and is the project's default, and the project's API version matches the org. Every later `retrieve`, `deploy` and `data` command then runs against the right org without extra flags (§19).

**Already done:** the org is authorised in the CLI under the alias `Lams` and is already the project's default target-org. What remains is the checks below (steps 1 and 3–8); skip the login in step 2 unless the connection has expired.

## Build

| Item | Value |
| --- | --- |
| CLI | Salesforce CLI v2 (`sf`), latest stable; `sf --version` shows `@salesforce/cli/2.x` |
| Alias | `Lams` (already set) |
| Default org | `target-org = Lams` (already set), **local** (project) config in `.sf/config.json`, which `.gitignore` already excludes |
| Login URL | `https://login.salesforce.com` (matches `sfdcLoginUrl` in `sfdx-project.json`) |
| API version | `sourceApiVersion` in `sfdx-project.json` = the org's API version from `sf org display` (`68.0` in the file and in the org, LAMS-002; change it only if the org differs) |
| VS Code | Salesforce Extension Pack; status bar shows `Lams` as the default org |

## Steps

1. Update the CLI: `npm install --global @salesforce/cli` (or `sf update`), then `sf --version`.
2. Already done; only if `sf org list` shows the connection as expired, log in again from the project folder `C:\Users\Suhas\Desktop\LAMS`:
   `sf org login web --alias Lams --set-default`
   The browser opens; log in and click *Allow*.
3. Check the connection and read the API version:
   `sf org display --target-org Lams`
   (Do not paste this output anywhere: it includes an access token.)
4. If *Api Version* differs from `sourceApiVersion`, edit `sfdx-project.json`. If the CLI's own default is newer than the org (common during release previews), also run `sf config set org-api-version=<org version>`.
5. Confirm config: `sf config list` shows `target-org Lams` (Location: Local); `sf org list` shows `Lams` with a connected status.
6. Smoke test without metadata:
   `sf data query --query "SELECT Name, OrganizationType, InstanceName FROM Organization"`
7. Add the alias, API version and CLI version to the *Org* section of [ORG_NOTES.md](ORG_NOTES.md).
8. Commit (only `sfdx-project.json` and `docs/milestones/M01-org-and-repo/ORG_NOTES.md`; `git status` must not list `.sf/` or `.sfdx/`):
   `chore(config): confirm Lams org connection and API version [LAMS-003]`.

## Learn

- **Alias vs username:** commands accept either; aliases keep usernames out of scripts. `--set-default` writes local (project) config; `--global` would affect every project on the machine.
- **Where auth lives:** the refresh token is stored in your home folder (`~/.sfdx`/`~/.sf`), not in the project. That is why the repo can be public and why CI needs its own credential (LAMS-004).
- **`sourceApiVersion` vs `org-api-version`:** the first sets the metadata format of the source files; the second sets the API version the CLI calls. Keep both at or below the org's version.

## Done when

- [ ] `sf org list` shows `Lams` as the default org
- [ ] The SOQL smoke test returns the org row with `OrganizationType` = Developer Edition
- [ ] `sourceApiVersion` equals the org API version shown by `sf org display`
- [ ] `git status` shows no `.sf/` or `.sfdx/` files
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §19 Source control and deployment (Project, Deploy rows)

# LAMS-075 · lamsPortalTheme Aura theme layout

**Milestone:** [M10 – Portal](README.md) · **Size:** M (2–5h) · **Delivers:** BR-60

**Depends on:** LAMS-074 (site), LAMS-021 (custom labels + Hindi)

## Goal

Give every portal page one accessible LAMS header and footer through a custom Aura theme layout, `lamsPortalTheme`, so navigation, the profile menu and language choice look the same on every page (BR-60, NFR-11, NFR-12).

## Build

**Aura bundle `force-app/main/default/aura/lamsPortalTheme/`**

| File | Content |
| --- | --- |
| `lamsPortalTheme.cmp` | `<aura:component implements="forceCommunity:themeLayout" access="global">` |
| `lamsPortalTheme.design` | Design attributes shown in Builder → Theme |
| `lamsPortalTheme.css` | Layout and brand styles (`.THIS` scoped) |
| `lamsPortalTheme.svg` | Icon shown in Builder (optional) |

**Attributes** (`Aura.Component[]` regions are filled in Builder; names `search`, `profileMenu`, `navBar` are the ones Builder recognises)

| Attribute | Type | Default | Use |
| --- | --- | --- | --- |
| `navBar` | `Aura.Component[]` | – | Navigation Menu component (LAMS-076 menu) |
| `profileMenu` | `Aura.Component[]` | – | User Profile Menu (My Profile, Logout) |
| `search` | `Aura.Component[]` | – | Left empty (proposed); no global search for borrowers |
| `languagePicker` | `Aura.Component[]` | – | Custom region (proposed) for Builder's Language Selector component |
| `logoUrl` | String | `$Resource.LAMS_Logo` (proposed static resource) | Header logo |
| `showFooter` | Boolean | true | Hide footer on the login layout if needed |

**Markup outline**

```
<a class="skip-link" href="#main-content">{!$Label.c.LAMS_Portal_Skip_To_Content}</a>
<header role="banner">  logo (alt = $Label.c.LAMS_Portal_Logo_Alt) · {!v.navBar} · {!v.languagePicker} · {!v.profileMenu}  </header>
<main id="main-content" role="main">  {!v.body}  </main>
<footer role="contentinfo">  $Label.c.LAMS_Portal_Footer_Text · help phone · privacy link  </footer>
```

Labels (all proposed names, EN + HI): `LAMS_Portal_Skip_To_Content`, `LAMS_Portal_Logo_Alt`, `LAMS_Portal_Footer_Text`, `LAMS_Portal_Help_Phone`, `LAMS_Portal_Privacy_Link`.

**Design file** exposes `logoUrl` and `showFooter` as `<design:attribute>` so the admin can change them without code.

**Theme assignment** (Builder → Settings → Theme → *Configure* theme layout types):

| Theme layout type | Layout |
| --- | --- |
| Default | lamsPortalTheme |
| Home | lamsPortalTheme |
| Login | Template default (proposed; registration from LAMS-074 keeps its own look) |

**Accessibility (WCAG 2.1 AA):** landmarks as above; skip link visible on focus; text contrast ≥ 4.5:1 (check brand colours in Builder → Theme → Colors); keyboard focus visible on every link; header collapses to a menu button below 768 px.

## Steps

1. Create the bundle: `sf lightning generate component --type aura --name lamsPortalTheme --output-dir force-app/main/default/aura`
2. Write the `.cmp`, `.design` and `.css`; add the static resource `LAMS_Logo` and the labels with Hindi translations.
3. Deploy: `sf project deploy start --metadata AuraDefinitionBundle:lamsPortalTheme StaticResource:LAMS_Logo CustomLabels`
4. In Builder → Theme, assign the layout to Default and Home; place Navigation Menu, Language Selector and User Profile Menu in the regions; publish.
5. Check with a screen reader or the axe browser extension: no landmark or contrast errors; switch language to Hindi and see translated footer text.
6. Retrieve the ExperienceBundle (theme assignment is stored there): `sf project retrieve start --metadata ExperienceBundle`
7. Commit: `feat(portal): lamsPortalTheme Aura theme layout [LAMS-075]`.

## Learn

- **`forceCommunity:themeLayout`** marks an Aura component as a theme layout; attributes of type `Aura.Component[]` become drop regions in Builder, and `{!v.body}` is where each page renders.
- **Theme layout types** let different pages (home, inner, login) use different layouts without new code.
- Aura still matters: LWC cannot be a theme layout in Aura templates, which is why the BRD keeps an Aura piece here.
- Accessibility is designed in the layout once (landmarks, skip link, focus order), not fixed page by page.

## Done when

- [ ] Every portal page except Login/Register shows the LAMS header and footer
- [ ] Navigation, profile menu and the English/Hindi switch work; footer text changes language
- [ ] Keyboard-only use reaches the skip link, menu and footer links; axe shows no AA violations in the layout
- [ ] Bundle, static resource, labels and the theme assignment are in source
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §15 lamsPortalTheme and Portal paragraph, §21 Aura row, BR-54, BR-60, NFR-11, NFR-12

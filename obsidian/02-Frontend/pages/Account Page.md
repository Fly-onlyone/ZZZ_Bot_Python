---
tags: [frontend, pages]
---

# Account Page

> Two-tab page for HoYoLab + Apprise credentials and the manual browser launcher.

## How it works
Tab 1 (**Credentials**) mounts a [[ValueAdapter]] with two custom sections: **HoYo Account** (`hoyo_username`, `hoyo_password`) iconed with a bundled `Hoyo.png` from [[Asset Endpoints]], and **Apprise Notification** (`username`, `app_password`). Field-level icons (Person/Password) are passed via `customIcons` — see [[Dynamic Form ValueAdapter Pattern]].

Tab 2 (**Manual Browser**) embeds [[Manual Login Page]] directly. Tab switching uses `auroraPanelVariants` from [[Aurora Tab Styles]] with directional slide based on previous index.

## Source
- `frontend/src/pages/AccountPage.jsx` — primary

## Depends on
- [[ValueAdapter]] — credential form
- [[Manual Login Page]] — embedded panel
- [[Account Endpoints]] — backend
- [[Asset Endpoints]] — Hoyo.png

## See also
- [[_index]]
- [[Notification Sender]]

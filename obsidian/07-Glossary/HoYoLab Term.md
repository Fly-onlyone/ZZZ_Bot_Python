---
tags: [glossary]
---

# HoYoLab

> HoYoverse's community portal and event website where players claim daily rewards, redeem codes, and enter prize draws for games like Zenless Zone Zero.

## How it works
HoYoLab (`hoyolab.com`) is the web surface ZZZ Bot automates. It hosts daily check-ins, web events with shops and prize wheels, and code redemption pages. The UI is dynamic and changes between events, which is why the bot leans on [[Image Comparison State Detection Pattern]] instead of brittle CSS selectors.

A logged-in HoYoLab session — persisted via Playwright [[Storage State Store]] — covers every event page, so authentication only needs to happen once per device.

## See also
- [[_index]]
- [[ZZZ Term]]
- [[HoYoLab]]

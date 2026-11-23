# Copy-Cat: Project Instructions and Skill Index

Copy-Cat is an app reverse-engineering and cloning workbench built on the Replica Skill foundation by Jake Schincariol, extended with Android Debug Bridge (ADB) device automation and native Google Antigravity support.

## Core Methodology

Copy-Cat follows a strict **clean-room reverse-engineering** workflow:
- Rebuild functionality and UX patterns only.
- Never copy proprietary source code, private APIs, trademarks, or copyrighted assets.
- Read only public sources and the developer's own account.
- Screenshots stored in `replica/screens/` serve as layout references and are never shipped in the cloned product.
- Always rebrand and sweep before launch.

## Skills Pipeline

Execute skills in this sequence:

1. `copycat-recon`: Maps screens, flows, components, and data model into `replica/recon.md` and `replica/features.csv`.
2. `copycat-architect`: Plans architecture, stack, database schema, and build order.
3. `copycat-design`: Extracts design tokens (colors, typography, spacing) into `replica/design/tokens.json`.
4. `copycat-build`: Rebuilds application screens and state machines.
5. `copycat-backend`: Implements auth, databases, payments, and external integrations.
6. `copycat-test`: Builds comprehensive test plans and logs bug tickets.
7. `copycat-diff`: Computes parity scores against original specifications and layout diffs.
8. `copycat-entrepreneur`: Analyzes user reviews and pain points to establish a unique market angle.
9. `copycat-brand`: Names and rebrands the clone, sweeping the repo for remnant names.
10. `copycat-launch`: Prepares landing page copy, pricing tiers, and app store listings.
11. `copycat-deploy`: Runs deployment preflight checks and ships to production.

## ADB Extension

Located in `adb/`:
- Controller: `python adb/adb_controller.py <command>`
- Skill: `copycat-adb` (declared in `.agents/skills/copycat-adb/SKILL.md`)
- Use for live device reconnaissance, real-phone screenshot capture, and automated mobile flow testing.

## Workspace Customization Configuration

- Skills registration: `.agents/skills.json`
- Supports standard Python 3.8+ tools without third-party dependencies.

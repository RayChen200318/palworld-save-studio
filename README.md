<p align="center">
  <img src="frontend/public/brand/palworld-save-studio-lockup.svg" width="420" alt="Palworld Save Studio">
</p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">简体中文</a>
</p>

# Palworld Save Studio

Palworld Save Studio is a Windows save editor for Palworld 1.0. It targets
Windows 10/11 x64 and supports Steam and dedicated-server saves.

[Download the latest Windows release](https://github.com/RayChen200318/palworld-save-studio/releases/latest)

## Guides

- [Using Save Studio with a dedicated server](https://github.com/RayChen200318/palworld-save-studio/blob/main/docs/dedicated-server-guide.md)

## Editing features

- Browse every player Pal, base worker, object outside a container, and human NPC.
- Create, duplicate, edit, retrieve, heal, and delete Pals or human NPCs.
- Edit species, nickname, gender, level, friendship, IVs, condensation, souls,
  work suitability, passive traits, active skills, and special flags.
- Search species by Chinese or English name, internal ID, or Paldeck number
  when creating a Pal, changing an existing species, or choosing an egg Pal.
- Edit innate work suitability through level 10 using Palworld 1.0 condensation
  rules, with server-side validation of each species' legal minimum.
- Browse bilingual passive-trait effects and active-skill descriptions, element,
  power, and cooldown; verified mutation-exclusive traits have a dedicated filter.
- Edit player nickname, level, technology points, Boss technology points, and
  viewing-cage access.
- Browse technology by level and toggle normal or Boss technology.
- Manage player inventory, key items, food pouches, weapons, equipment,
  temporary drops, durability, ammunition, rarity, and eggs.
- Version `0.3.0` introduces the original Save Studio brand, comfortable type
  sizes, compact layouts, and a consistent editor interface.
- Version `0.3.1` removes release checking and remote WebUI mode. The packaged
  application listens only on `127.0.0.1` for its desktop interface and makes
  no external network requests.
- Version `0.4.0` adds searchable species selectors, level-10 work suitability,
  bilingual skill details, and a verified mutation-exclusive trait category.
- Version `0.4.1` enlarges the create-Pal species picker and prevents Pal Gear
  key items from being written with invalid stacked quantities.
- Version `0.4.2` adds navigation across available Windows drives and direct
  entry of absolute drive or UNC network-share paths in the save browser.
- Keep all changes in one in-memory draft and save them to the currently opened
  world in one operation.

## Interface

![Open save screen](docs/screenshots/start-1536x864.jpg)

![Dashboard](docs/screenshots/dashboard-1536x864.jpg)

![Item management](docs/screenshots/items-1536x864.jpg)

## Supported scope

Version `0.4.2` supports the Windows GUI, Palworld 1.0 data, Steam saves, and
dedicated-server saves. Item management is currently validated with a Steam
save only; it does not claim dedicated-server item validation. Item management
excludes base storage, world containers,
cross-player transfers, virtual progress records, and out-of-range values. The
application also does not include Xbox/Game Pass, raw JSON editing, Save As,
bulk field editing, multi-level undo, installers, update checks, telemetry,
external network access, a remote WebUI mode, a light theme, or other desktop
platforms.

## Development

Requirements: Python 3.11+, Node.js 20+, and Windows for the packaged GUI.

```powershell
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm test
corepack pnpm build
```

The complete Windows pipeline is:

```powershell
.\build_executable.ps1
```

For the exact release source, pinned dependencies, and a clean Windows build
procedure, see the [full source and build guide](SOURCE_BUILD_GUIDE.md).

It runs Python tests, Vitest, TypeScript, Vite, PyInstaller, an executable smoke
test, ZIP packaging, and SHA-256 generation. The executable and Nexus-ready
archive are `dist\Palworld-Save-Studio.exe` and
`dist\Palworld-Save-Studio-Windows-x64.zip`; application configuration and logs
are stored under `%LOCALAPPDATA%\PalworldSaveStudio`.

## Acknowledgements

Special thanks to [KrisCris](https://github.com/KrisCris) for open-sourcing
[Palworld-Pal-Editor](https://github.com/KrisCris/Palworld-Pal-Editor).
Palworld Save Studio references that project and contains modified source code
derived from it. This open-source work provided an important foundation for
the independent editor. See [NOTICE](NOTICE) for the complete provenance.

## License and provenance

This project is licensed under GPL-3.0. See [NOTICE](NOTICE) for source
attribution and the independent import baseline. Palworld Save Studio is an
unofficial fan tool and is provided without warranty.

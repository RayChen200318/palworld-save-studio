<p align="center">
  <img src="frontend/public/brand/palworld-save-studio-lockup.svg" width="420" alt="Palworld Save Studio">
</p>

# Palworld Save Studio

Palworld Save Studio is a Windows save editor for Palworld 1.0. It targets
Windows 10/11 x64 and supports Steam and dedicated-server saves.

[Download the latest Windows release](https://github.com/RayChen200318/palworld-save-studio/releases/latest)

> `0.1.0-beta.1` is a public beta. Use a copy of your save while evaluating it
> and report reproducible problems through GitHub Issues.

## Editing features

- Browse every player Pal, base worker, object outside a container, and human NPC.
- Create, duplicate, edit, retrieve, heal, and delete Pals or human NPCs.
- Edit species, nickname, gender, level, friendship, IVs, condensation, souls,
  work suitability, passive traits, active skills, and special flags.
- Edit player nickname, level, technology points, Boss technology points, and
  viewing-cage access.
- Browse technology by level and toggle normal or Boss technology.
- The `0.2.0-beta.1` preview branch adds player inventory, key-item, food-pouch,
  weapon, equipment, temporary-drop, durability, ammunition, rarity, and egg
  management. Preview builds are supplied only through pull-request CI artifacts.
- The `0.3.0-beta.1` preview refreshes the original brand, increases UI type
  sizes, reduces unused space, and reorganizes every editor screen without
  changing save behavior or API contracts.
- Keep all changes in one in-memory draft and save them to the currently opened
  world in one operation.

## Interface preview

![Open save screen](docs/screenshots/start-1536x864.jpg)

![Dashboard](docs/screenshots/dashboard-1536x864.jpg)

![Item management](docs/screenshots/items-1536x864.jpg)

## Supported scope

The published first release supports the Windows GUI, Palworld 1.0 data, Steam
saves, and dedicated-server saves. Item management on the preview branch is
currently validated with a Steam save only; it does not claim dedicated-server
item validation. Item management excludes base storage, world containers,
cross-player transfers, virtual progress records, and out-of-range values. The
application also does not include Xbox/Game Pass, raw JSON editing, Save As,
bulk field editing, multi-level undo, installers, automatic updates, telemetry,
a light theme, or other desktop platforms.

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

It runs Python tests, Vitest, TypeScript, Vite, PyInstaller, an executable smoke
test, and SHA-256 generation. The executable output is
`dist\Palworld-Save-Studio.exe`; application configuration and logs are stored
under `%LOCALAPPDATA%\PalworldSaveStudio`.

## License and provenance

This project is licensed under GPL-3.0. See [NOTICE](NOTICE) for source
attribution and the independent import baseline. Palworld Save Studio is an
unofficial fan tool and is provided without warranty.

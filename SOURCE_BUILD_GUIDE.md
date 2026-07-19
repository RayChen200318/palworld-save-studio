# Full Source Code and Reproducible Windows Build Guide

This document identifies the complete source corresponding to the published
Palworld Save Studio `0.4.2` release and explains how to build and verify the
Windows application from a clean checkout.

Palworld Save Studio is a standalone desktop save editor. It is not injected
into Palworld, does not replace game files, and is not an in-game DLL, plugin,
or script mod. The application runs locally and edits a user-selected save.

## Canonical source for version 0.4.2

- Repository: <https://github.com/RayChen200318/palworld-save-studio>
- Release tag: [`0.4.2`](https://github.com/RayChen200318/palworld-save-studio/tree/0.4.2)
- Exact release commit: [`945813a221a335f5d894f0d18fa4ed1682a14883`](https://github.com/RayChen200318/palworld-save-studio/commit/945813a221a335f5d894f0d18fa4ed1682a14883)
- Complete source ZIP: <https://github.com/RayChen200318/palworld-save-studio/archive/refs/tags/0.4.2.zip>
- Complete source tarball: <https://github.com/RayChen200318/palworld-save-studio/archive/refs/tags/0.4.2.tar.gz>
- Published binaries: <https://github.com/RayChen200318/palworld-save-studio/releases/tag/0.4.2>

GitHub generates the ZIP and tarball directly from the tagged commit. They
contain all project-owned source code and assets used to build the release.
This guide was added after the `0.4.2` tag as documentation only; use the tag
and commit above when reviewing or reproducing the released executable.

## Source layout

| Path | Contents |
| --- | --- |
| `src/palworld_save_studio/` | Python application, Flask API, save-editing services, desktop entry point, offline catalogs, and runtime assets |
| `frontend/src/` | Vue 3 and TypeScript user interface, Pinia stores, typed API client, styles, and frontend tests |
| `frontend/pnpm-lock.yaml` | Locked JavaScript dependency graph |
| `tests/` | Python unit, regression, save round-trip, and release checks |
| `build_executable.ps1` | Complete Windows test, build, PyInstaller, smoke-test, archive, and checksum pipeline |
| `.github/workflows/ci.yml` | Public Windows CI configuration using Node.js 20 and Python 3.12 |
| `.github/workflows/release.yml` | Tagged-release packaging workflow |
| `requirements.txt` | Pinned Python runtime and build dependencies |
| `LICENSE` | GPL-3.0 license text |
| `NOTICE` | Upstream attribution, imported-code provenance, and data-source notices |

The compiled frontend is generated during the build and copied to
`src/palworld_save_studio/webui/`; it is not an additional closed-source
component. There are no private source repositories, remote application
services, or proprietary build tools required to produce the application.

## Prerequisites

Build on Windows 10 or Windows 11 x64 with:

- Git
- PowerShell
- Python 3.11 or newer on `PATH` (`3.12` is recommended because public CI uses it)
- Node.js 20 or newer with the `corepack` command available
- Internet access while installing the pinned dependencies

The frontend declares `pnpm 9.15.9`, and Corepack selects that version from
`frontend/package.json`. No credentials, signing certificate, Palworld
installation, or game save are required to compile and test the application.

Confirm the tools are available from PowerShell:

```powershell
git --version
python --version
node --version
corepack --version
```

If the Python executable is named `python3`, the build script detects it
automatically.

## Clean build procedure

Run the following commands in PowerShell:

```powershell
git clone https://github.com/RayChen200318/palworld-save-studio.git
cd palworld-save-studio
git checkout --detach 0.4.2
git rev-parse HEAD
```

The last command must print:

```text
945813a221a335f5d894f0d18fa4ed1682a14883
```

Then run the complete build pipeline:

```powershell
.\build_executable.ps1
```

The script performs these steps without requiring manual source changes:

1. Installs the frontend dependency graph from `frontend/pnpm-lock.yaml` with
   `corepack pnpm install --frozen-lockfile`.
2. Runs the Vitest frontend tests and the TypeScript/Vite production build.
3. Copies the generated WebUI into the Python package.
4. Creates a fresh Python virtual environment in `venv` and installs the
   pinned Python dependencies.
5. Installs `pyooz` from commit
   `9af53d1faaa2f9a7dafe6d6caea117c762dc71d9` and
   `palworld-save-tools` from commit
   `790e0bcf7bacef47b048e110066617a8fbb40041`.
6. Runs the complete Python test suite with `unittest`.
7. Packages `src/palworld_save_studio/__main__.py` as a one-file Windows
   executable with PyInstaller.
8. Runs `Palworld-Save-Studio.exe --help` as an executable smoke test.
9. Creates the distribution ZIP and SHA-256 checksum files.

## Build outputs

After a successful build, `dist` contains:

```text
dist\Palworld-Save-Studio.exe
dist\Palworld-Save-Studio.exe.sha256
dist\Palworld-Save-Studio-Windows-x64.zip
dist\Palworld-Save-Studio-Windows-x64.zip.sha256
```

The ZIP contains the executable, its checksum, both English and Chinese
README files, `LICENSE`, and `NOTICE`.

Verify the locally built application and checksums with:

```powershell
.\dist\Palworld-Save-Studio.exe --help
Get-FileHash .\dist\Palworld-Save-Studio.exe -Algorithm SHA256
Get-Content .\dist\Palworld-Save-Studio.exe.sha256
Get-FileHash .\dist\Palworld-Save-Studio-Windows-x64.zip -Algorithm SHA256
Get-Content .\dist\Palworld-Save-Studio-Windows-x64.zip.sha256
```

The checksum recorded beside each local artifact must match the checksum
calculated for that artifact. A fresh PyInstaller build is not promised to be
byte-for-byte identical to the published binary because packaging metadata,
absolute build paths, and tool-environment details can differ. The tagged
source, locked dependencies, automated tests, and public Windows workflow are
the source-to-binary verification path.

## Independent frontend and test commands

The frontend can be checked independently:

```powershell
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm test
corepack pnpm build
```

For the complete Python environment and regression suite, use
`build_executable.ps1`; it recreates the same dependency installation and test
sequence used by public CI.

## License and third-party source

Palworld Save Studio is distributed under GPL-3.0. Project provenance and
third-party data attribution are documented in [`NOTICE`](NOTICE). Third-party
libraries are not copied into this repository; their exact package versions or
Git commits are pinned by the lockfile, `requirements.txt`, and the build
script so their corresponding upstream source can be audited.

Questions about the source or build can be filed at
<https://github.com/RayChen200318/palworld-save-studio/issues>.

<p align="center">
  <strong>English</strong> · <a href="dedicated-server-guide.zh-CN.md">简体中文</a>
</p>

# Dedicated Server Quick Guide

This guide applies to Palworld Save Studio `0.4.2` or later.

Palworld Save Studio can edit an existing Palworld 1.0 dedicated-server save
when you are the server owner, an administrator, or an authorized operator with
access to the server files. It is an offline save editor: it does not connect
to a running server through its IP address, RCON, or the Palworld REST API.
Regular players cannot use it to edit somebody else's server.

[Download the latest Windows release](https://github.com/RayChen200318/palworld-save-studio/releases/latest)

## Before you begin

- Run Studio on Windows 10/11 x64.
- Ask every player to disconnect, stop the server completely, and temporarily
  disable automatic restart.
- Copy the entire active world folder to a separate location outside the live
  `SaveGames/0` directory. Do not back up only `Level.sav`.
- Keep world and player files from the same point in time. Never mix
  `Level.sav` from one backup with `Players` files from another.

Do not copy, edit, or replace save files while the server is running.

## Find the active world folder

A typical Windows dedicated-server world is located at:

```text
<PalServer installation>\Pal\Saved\SaveGames\0\<WorldID>\
```

A typical Linux installation uses:

```text
<PalServer installation>/Pal/Saved/SaveGames/0/<WorldID>/
```

Docker and hosting providers may expose another host path. The folder selected
in Studio must directly contain both `Level.sav` and the `Players` directory:

```text
<WorldID>/
├── Level.sav
├── Players/
│   └── <PlayerID>.sav
├── LevelMeta.sav      (may be present)
└── WorldOption.sav    (may be present)
```

If several WorldID folders exist, identify the active one through the hosting
panel or its modification time after a clean shutdown. Do not guess.

## Make the save available to Studio

- **Same Windows computer:** open the stopped server's WorldID folder directly.
- **Remote Windows server:** download the complete WorldID folder, use a mapped
  drive, or enter an authorized UNC path such as
  `\\server\share\Pal\Saved\SaveGames\0\<WorldID>`.
- **Linux, Docker, or hosted server:** stop the server or container, then
  download the complete WorldID folder through SFTP or the hosting panel and
  edit that copy on Windows.

Editing a local copy is recommended even when a writable network share is
available, because an interrupted network write can leave remote files
incomplete.

## Edit and return the save

1. Open `Palworld-Save-Studio.exe` and choose the WorldID folder that directly
   contains `Level.sav` and `Players`.
2. Wait for the Dashboard and player list to load, then select the correct
   player by nickname.
3. Make the required Pal, player, or technology changes. Use the global Save
   button, confirm the target path, and wait for Studio to finish writing and
   reloading the save.
4. If you edited a downloaded copy, keep the server stopped and upload the
   edited `Level.sav` plus the complete contents of the edited `Players`
   directory. Keep the same WorldID folder name and do not add another nested
   WorldID folder.
5. Do not upload `Palworld-Save-Studio-Backup`. On Linux or Docker, preserve or
   restore the original file owner and permissions before starting the server.
6. Restart the server and confirm that the original world loads, existing
   players can join, and the intended changes are visible.

If the world fails to load, the wrong world appears, or existing players are
asked to create new characters, stop the server immediately and restore the
complete original WorldID backup. Check the selected WorldID, directory
nesting, file timestamps, and Linux permissions before trying again.

## Supported scope

The dedicated-server workflow officially covers Pal, human NPC, player, and
technology editing. Inventory and item management has currently been validated
with a Steam local save only, so dedicated-server item editing is not claimed
as tested or supported by this guide.

This guide does not cover:

- Editing a server without authorized file access
- Official servers or live editing while players are online
- Xbox/Game Pass local-save conversion
- Migrating a co-op world to a dedicated server
- Moving a world between servers or remapping player GUIDs

Only the administrator performing the offline edit needs Studio. Other players
do not need to install it.

## References

- [Palworld Save Studio repository](https://github.com/RayChen200318/palworld-save-studio)
- [Official Palworld 1.0 server guide](https://docs.palworldgame.com/getting-started/about-server/)
- [Official dedicated-server deployment guide](https://docs.palworldgame.com/getting-started/deploy-dedicated-server/)

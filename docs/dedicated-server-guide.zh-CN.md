<p align="center">
  <a href="dedicated-server-guide.md">English</a> · <strong>简体中文</strong>
</p>

# 专用服务器快速教程

本教程适用于 Palworld Save Studio `0.4.2` 或更高版本。

如果你是服主、管理员，或已获得授权并能访问服务器文件，就可以使用
Palworld Save Studio 编辑现有的《幻兽帕鲁》1.0 专用服务器存档。Studio
是离线存档编辑器，不会通过服务器 IP、RCON 或 Palworld REST API 连接
运行中的服务器。普通玩家无法用它修改别人的服务器。

[下载最新 Windows 版本](https://github.com/RayChen200318/palworld-save-studio/releases/latest)

## 操作前准备

- Studio 需要在 Windows 10/11 x64 上运行。
- 让所有玩家下线，彻底关闭服务器，并暂时停用自动重启。
- 把整个活动世界文件夹复制到 `SaveGames/0` 活动目录之外的独立位置。
  不要只备份 `Level.sav`。
- 世界文件和玩家文件必须来自同一时间点。不要混用不同备份中的
  `Level.sav` 与 `Players` 文件。

服务器运行期间不要复制、编辑或替换存档文件。

## 找到活动世界文件夹

Windows 专用服务器的常见路径为：

```text
<PalServer 安装目录>\Pal\Saved\SaveGames\0\<世界ID>\
```

Linux 的常见路径为：

```text
<PalServer 安装目录>/Pal/Saved/SaveGames/0/<世界ID>/
```

Docker 和服务器托管商显示的宿主机路径可能不同。Studio 所选择的文件夹
必须直接包含 `Level.sav` 和 `Players` 文件夹：

```text
<世界ID>/
├── Level.sav
├── Players/
│   └── <玩家ID>.sav
├── LevelMeta.sav      （可能存在）
└── WorldOption.sav    （可能存在）
```

如果存在多个世界 ID 文件夹，请通过服务器面板或正常关服后的修改时间确认
当前活动世界，不要猜测。

## 把存档交给 Studio

- **同一台 Windows 电脑：**关服后直接打开服务器的世界 ID 文件夹。
- **远程 Windows 服务器：**下载完整世界 ID 文件夹、使用映射盘，或输入
  已授权的 UNC 路径，例如
  `\\server\share\Pal\Saved\SaveGames\0\<世界ID>`。
- **Linux、Docker 或租用服务器：**停止服务器或容器，再通过 SFTP 或
  托管面板下载完整世界 ID 文件夹，并在 Windows 上编辑该副本。

即使网络共享具有写入权限，也建议先下载本地副本再编辑，避免网络中断
造成远程文件写入不完整。

## 编辑并放回服务器

1. 打开 `Palworld-Save-Studio.exe`，选择直接包含 `Level.sav` 与 `Players`
   的世界 ID 文件夹。
2. 等待 Dashboard 和玩家列表载入，再按昵称选择正确玩家。
3. 完成帕鲁、玩家或科技修改后，点击全局保存按钮，确认目标路径，并等待
   Studio 完成写入和重新载入。
4. 如果编辑的是下载副本，请继续保持关服，上传编辑后的 `Level.sav` 以及
   编辑后 `Players` 文件夹的完整内容。保留原世界 ID 文件夹名称，不要额外
   嵌套一层同名世界文件夹。
5. 不要上传 `Palworld-Save-Studio-Backup`。Linux 或 Docker 服务器开服前
   需要保留或恢复原来的文件所有者和权限。
6. 重启服务器，确认载入的是原世界、老玩家能够进入，并检查目标修改是否
   已经生效。

如果世界载入失败、出现错误世界，或老玩家被要求重新创建角色，请立即
关服并完整恢复原始世界 ID 备份。再次尝试前检查世界 ID、目录嵌套、文件
时间以及 Linux 权限。

## 支持范围

专服流程正式覆盖帕鲁、人类 NPC、玩家与科技编辑。物品管理目前只使用
Steam 本地存档完成验证，因此本教程不宣称专服物品编辑已经过测试或受到
正式支持。

本教程不包括：

- 在没有授权文件权限的情况下编辑服务器
- 官方服务器或玩家在线时的热修改
- Xbox/Game Pass 本地存档转换
- 把联机房主世界迁移为专用服务器
- 在服务器之间迁移世界或重新映射玩家 GUID

只有执行离线编辑的管理员需要安装 Studio，其他玩家无需安装。

## 参考资料

- [Palworld Save Studio 仓库](https://github.com/RayChen200318/palworld-save-studio)
- [Palworld 1.0 官方服务器说明](https://docs.palworldgame.com/getting-started/about-server/)
- [官方专用服务器部署说明](https://docs.palworldgame.com/getting-started/deploy-dedicated-server/)

<p align="center">
  <a href="dedicated-server-guide.md">English</a> · <strong>简体中文</strong>
</p>

# 专用服务器快速教程

本教程中的专服安全写入流程适用于 `0.4.3-beta.1`。`0.4.2` 仍是最新
稳定版，但不包含本教程所述的强制完整备份、源文件并发变更检测和仅变化
文件写入。`0.4.3-beta.1` 尚待真实 PalServer 验收，不应被视为稳定版。

如果你是服主、管理员，或已获得授权并能访问服务器文件，就可以使用
Palworld Save Studio 编辑现有的《幻兽帕鲁》1.0 专用服务器存档。Studio
是离线存档编辑器，不会通过服务器 IP、RCON 或 Palworld REST API 连接
运行中的服务器。普通玩家无法用它修改别人的服务器。

[下载 `0.4.3-beta.1` 预发布版](https://github.com/RayChen200318/palworld-save-studio/releases/tag/0.4.3-beta.1)

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

1. 打开 `Palworld-Save-Studio.exe`，明确选择“专用服务器存档”，再选择直接
   包含 `Level.sav` 与 `Players` 的世界 ID 文件夹。不要选择 `0`、压缩包
   外层目录或额外嵌套的同名文件夹。
2. 等待 Dashboard 和玩家列表载入，再按昵称选择正确玩家。
3. 完成修改后点击全局保存按钮，核对 WorldID、备份目录、拟写入文件和
   已确认无变化并跳过的文件。只有确认 PalServer 已完全停止后才能提交。
4. Studio 会先在 `Palworld-Save-Studio-Backup/<时间戳>/` 创建完整核心
   存档备份，再只替换真正发生变化的文件，并重新载入核验。备份失败、源
   文件已变化或复验失败时不会保留部分写入。
5. 如果编辑的是下载副本，请继续保持关服，只上传提交结果中
   `FilesChanged` 列出的文件，并保持它们相对于世界 ID 文件夹的原路径。
   不要重传 `FilesSkipped` 中未变化的玩家文件，也不要额外嵌套一层同名
   世界文件夹。
6. 不要上传 `Palworld-Save-Studio-Backup`。Linux 或 Docker 服务器开服前
   需要保留或恢复原来的文件所有者和权限。
7. 重启服务器，确认载入的是原世界、老玩家能够进入，并检查目标修改是否
   已经生效。

如果世界载入失败、出现错误世界，或老玩家被要求重新创建角色，请立即
关服并完整恢复原始世界 ID 备份。再次尝试前检查世界 ID、目录嵌套、文件
时间以及 Linux 权限。

## 支持范围

`0.4.3-beta.1` 已使用用户提供的事故前专服存档私有克隆完成结构、备份、
仅变化文件写入和重新载入回归，但尚未在真实 PalServer 上完成启动、玩家
身份与进度、再次保存和二次重启验收。因此本教程不宣称专服编辑已经获得
真实服务器兼容性验证。

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

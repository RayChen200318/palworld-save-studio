<p align="center">
  <img src="frontend/public/brand/palworld-save-studio-lockup.svg" width="420" alt="Palworld Save Studio">
</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong>
</p>

# Palworld Save Studio

Palworld Save Studio 是一款适用于《幻兽帕鲁》1.0 的 Windows 存档编辑器，
支持 Windows 10/11 x64、Steam 存档与专用服务器存档。

[下载最新 Windows 版本](https://github.com/RayChen200318/palworld-save-studio/releases/latest)

## 编辑功能

- 查看所有玩家帕鲁、基地工作帕鲁、容器外对象和人类 NPC。
- 新增、复制、编辑、取回、治疗和删除帕鲁或人类 NPC。
- 编辑种类、昵称、性别、等级、友好度、IV、浓缩、魂强化、工作适应性、
  被动词条、主动技能和特殊标记。
- 新增帕鲁、修改现有物种和选择蛋内帕鲁时，均可按中英文名称、内部 ID
  或图鉴编号搜索物种。
- 工作适应性按《幻兽帕鲁》1.0 规则支持至 10 级，并由服务端根据物种先天
  等级、额外强化和满凝聚加成校验合法最低值。
- 被动词条显示中英文效果；主动技能显示说明、属性、威力和冷却时间；
  已验证的突变专属词条提供独立筛选。
- 编辑玩家昵称、等级、科技点、Boss 科技点和观赏笼权限。
- 按等级浏览科技，并分别开关普通科技或 Boss 科技。
- 管理玩家背包、关键物品、食物袋、武器、装备、临时掉落物、耐久度、
  弹药、稀有度和蛋类物品。
- `0.3.0` 版本引入原创 Save Studio 品牌、舒适字号、紧凑布局和统一的编辑界面。
- `0.3.1` 版本移除版本检查与远程 WebUI 模式。发布版仅在 `127.0.0.1`
  上提供桌面界面所需的本地服务，不发起任何外部网络请求。
- `0.4.0` 版本新增物种搜索、10 级工作适应性、双语技能详情和已验证的
  突变专属词条分类。
- `0.4.1` 版本放大新增帕鲁物种选择器，并阻止帕鲁装备关键物品写入非法
  堆叠数量。
- `0.4.2` 版本在存档浏览器中增加 Windows 可用盘符切换，并支持直接输入
  盘符绝对路径或 UNC 网络共享路径。
- 所有修改先保存在同一份内存草稿中，确认后一次写回当前打开的世界存档。

## 界面

![打开存档界面](docs/screenshots/start-1536x864.jpg)

![仪表盘](docs/screenshots/dashboard-1536x864.jpg)

![物品管理](docs/screenshots/items-1536x864.jpg)

## 支持范围

`0.4.2` 版本支持 Windows 图形界面、《幻兽帕鲁》1.0 数据、Steam 存档和
专用服务器存档。物品管理目前仅使用 Steam 存档完成验证，因此不宣称已经
验证专用服务器存档中的物品编辑。物品管理不包括基地仓库、世界容器、
跨玩家转移、虚拟进度记录或超范围数值。本程序也不支持 Xbox/Game Pass、
原始 JSON 编辑、另存为、批量字段编辑、多级撤销、安装程序、版本检查、
遥测、外部网络访问、远程 WebUI 模式、浅色主题或其他桌面平台。

## 开发

开发环境需要 Python 3.11+、Node.js 20+；打包图形界面需要 Windows。

```powershell
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm test
corepack pnpm build
```

完整的 Windows 构建流程为：

```powershell
.\build_executable.ps1
```

该流程会依次运行 Python 测试、Vitest、TypeScript、Vite、PyInstaller、
可执行文件启动检查、ZIP 打包和 SHA-256 生成。生成的可执行文件与适合
Nexus 上传的归档分别位于 `dist\Palworld-Save-Studio.exe` 和
`dist\Palworld-Save-Studio-Windows-x64.zip`；应用配置和日志保存在
`%LOCALAPPDATA%\PalworldSaveStudio`。

## 致谢

特别感谢 [KrisCris](https://github.com/KrisCris) 开源
[Palworld-Pal-Editor](https://github.com/KrisCris/Palworld-Pal-Editor)。
Palworld Save Studio 参考了该项目，并包含在其源代码基础上修改的代码。
这项开源工作为本独立编辑器提供了重要基础。完整来源记录请参阅
[NOTICE](NOTICE)。

## 许可证与来源

本项目采用 GPL-3.0 许可证。源代码归属与独立导入基线记录请参阅
[NOTICE](NOTICE)。Palworld Save Studio 是非官方粉丝工具，不提供任何担保。

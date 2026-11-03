# 原神帧率解锁与帧生成 · v1.0.0

Windows 图形工具，提供帧率上限调整，以及独立安装的 Lossless Scaling 游戏配置联动。

**仅限非商业用途，禁止商用。当前未完成 Windows 实机与真实补帧验证。**

[下载 v1.0.0](https://github.com/iii-ai/Genshin_fps_unlocker-Frame_generation/releases/tag/v1.0.0) · [仓库内下载](downloads/) · [使用指南](USAGE.md) · [免责声明](DISCLAIMER.md) · [许可条款](LICENSE) · [更新记录](CHANGELOG.md)

## 功能

- 圆角卡片界面、可收起侧栏、浅色/深色/系统主题及多种语言。
- 调整目标帧率，启动/接管游戏进程并维持设定值。
- 帧生成设置按补帧、画质缩放、同步显示、设备、鼠标、裁切、启动联动和引擎分卡片显示，支持平滑滚动。
- 倍率滑条、自定义倍率、LSFG 模式、捕获方式、HDR/G-Sync 等配置与现有引擎 Profile 映射。
- 启动前备份引擎设置，停止时仅结束本工具启动的引擎；没有外部修改时恢复原配置。
- “关于”页直接访问本仓库。

## 快速开始

1. 下载 `GenshinFPSUnlocker-v1.0.0-windows-x64.zip` 并完整解压；可对照同目录 `SHA256SUMS.txt` 校验。
2. 阅读 `LICENSE` 与 `DISCLAIMER.md`，确认符合非商业用途及游戏服务条款要求。
3. 在 Windows x64 上以管理员身份运行 `原神帧率解锁-v1.0.0.exe`。
4. 在“配置”页选择 `YuanShen.exe` 或 `GenshinImpact.exe`，在“修改帧率”页设定目标值。
5. 默认关闭“帧生成”，点击仪表盘的启动开关即可按原流程启动并解锁。
6. 需要补帧时，按[补帧配置步骤](USAGE.md#补帧配置)准备官方引擎，再开启“帧生成”。

## 运行边界

- EXE 为 Windows x64 程序；macOS 预览只演示界面，不代表 Windows 运行验证。
- **不内置 Lossless Scaling、LSFG 模型、第三方授权绕过组件或游戏文件。** 独立引擎需由使用者自行合法安装。
- 补帧配置适配依据现有配置字段；不同引擎版本可能不兼容。缺少配置或所选字段不受支持时会停止并报错。
- 目标 FPS 是设定值，“预计输出”是计算结果；均不是实时测量值。引擎进程启动也不代表补帧已生效。
- 本工具会修改游戏进程内存，并在启用联动时修改引擎的 `Settings.xml`；它不是官方插件，也不保证游戏服务条款允许使用或账号安全。

## 源码与构建

使用 Windows + CPython 3.12，在源码目录运行：

```powershell
py -3.12 -m pip install -r requirements-ui-build.txt
powershell -ExecutionPolicy Bypass -File .\build_ui.ps1
```

构建输出位于 `dist_ui/`。构建过程不下载或内置补帧引擎。依赖版本以 `requirements-ui-build.txt` 为准。

当前分发 EXE 是保留已有 Windows 运行库、更新应用脚本后的封包，已检查归档、内嵌代码与 PE 校验和；这不等同于 Windows 端完整构建或实机测试。

## 许可与第三方

本项目自有部分采用[自定义非商业许可](LICENSE)，不应称为 OSI 认可的开源许可。禁止销售、付费分发、商业捆绑和营利服务使用。第三方代码、依赖、图形来源的原许可证保持有效，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本项目与 HoYoverse、原神、Lossless Scaling 及其开发者没有隶属、合作或背书关系。

## 反馈

请在 [Issues](https://github.com/iii-ai/Genshin_fps_unlocker-Frame_generation/issues) 中提供系统版本、显卡/显示器、应用版本、复现步骤及脱敏截图；勿上传账号凭据、私人路径或完整设置文件。参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

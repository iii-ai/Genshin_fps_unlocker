# 原神帧率解锁 · v1.0.0

Windows x64 原神帧率解锁工具。支持自定义目标帧率、游戏启动与进程接管、状态显示，以及浅色、深色、系统主题和多语言界面。

**[下载 Windows x64](https://github.com/iii-ai/Genshin_fps_unlocker/releases/download/v1.0.0/GenshinFPSUnlocker-v1.0.0-windows-x64.zip)** · [最新版本](https://github.com/iii-ai/Genshin_fps_unlocker/releases/latest) · [使用文档](USAGE.md) · [源文件](https://github.com/iii-ai/Genshin_fps_unlocker/releases/download/v1.0.0/GenshinFPSUnlocker-v1.0.0-source.zip)

[免责声明](DISCLAIMER.md) · [许可](LICENSE) · [第三方声明](THIRD_PARTY_NOTICES.md)

## 下载

| 文件 | 适用范围 | 说明 |
| --- | --- | --- |
| [Windows x64 程序包](https://github.com/iii-ai/Genshin_fps_unlocker/releases/download/v1.0.0/GenshinFPSUnlocker-v1.0.0-windows-x64.zip) | Windows 64 位 | 完整解压后运行，无需单独安装 Python |
| [源文件与构建脚本](https://github.com/iii-ai/Genshin_fps_unlocker/releases/download/v1.0.0/GenshinFPSUnlocker-v1.0.0-source.zip) | 源码运行与构建 | 包含源文件、依赖清单、构建脚本和文档 |
| [SHA256SUMS.txt](https://github.com/iii-ai/Genshin_fps_unlocker/releases/download/v1.0.0/SHA256SUMS.txt) | 文件校验 | 核对两个压缩包的 SHA-256 |

[查看全部版本](https://github.com/iii-ai/Genshin_fps_unlocker/releases) · [仓库下载目录](downloads/)

## 使用

1. 完整解压 Windows 压缩包。
2. 以管理员身份运行 `原神帧率解锁-v1.0.0.exe`。
3. 在“配置”选择 `YuanShen.exe` 或 `GenshinImpact.exe`。
4. 在“修改帧率”设置目标值，再点击仪表盘启动按钮。

## 从源码运行与构建

需要 Windows x64 和 CPython 3.12。在源码目录执行：

```powershell
py -3.12 -m pip install -r requirements-ui-build.txt
py -3.12 app.py
```

打包：

```powershell
powershell -File .\build_ui.ps1
```

输出目录为 `dist_ui/`。依赖包括 Pillow、PyInstaller 和 pyinstaller-hooks-contrib，版本见 `requirements-ui-build.txt`；Tcl/Tk 随 Python 提供。

## 使用限制

仅限非商业用途，禁止商用。本工具并非游戏官方产品，会访问并修改游戏进程内存；使用前请阅读免责声明并自行遵守游戏服务条款。目标帧率是设置值，实际性能取决于硬件、场景与游戏版本。

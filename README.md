# Cubic-Fedora

**Cubic-Fedora**（Cubic_fedora）是 [Cubic — Custom Ubuntu ISO Creator](https://github.com/PJ-Singh-001/Cubic) 的一个分支（fork），由 [maylog](https://github.com/mayloglog/cubic_fedora) 维护。

Cubic 原版由 PJ Singh 开发，用于定制基于 Ubuntu/Debian 的 Live ISO。Cubic-Fedora 在保留原版全部能力的基础上，扩展了对 **Fedora 系（Feidora）发行版 Live ISO** 的支持，并做了包名与界面品牌化处理，可与原版 `cubic` 并存安装。

> 致谢：本项目基于 PJ Singh 的 [Cubic](https://github.com/PJ-Singh-001/Cubic)（GPL-3.0），感谢原作者及社区的持续工作。

## 主要改动

### 1. Fedora 系（Feidora）Live ISO 支持

Cubic 原版仅支持 Debian 系（casper）布局。Fedora 的 Live 镜像使用 dracut dmsquash-live 体系，根文件系统存在多种不同的组织方式。Cubic-Fedora 引入“发行版家族（distro_family）”概念（`debian` / `fedora`），在提取阶段自动探测家族，并按镜像真实格式自动分派处理：

| 源镜像格式（自动识别） | 提取方式 | 生成阶段 |
|---|---|---|
| squashfs 直接含根目录树（Debian 系） | unsquashfs 到 custom-root | mksquashfs 重打包 |
| squashfs 内嵌 ext4 根镜像（`LiveOS/ext3fs.img` / `rootfs.img`，Fedora 经典） | 解包到 staging，内嵌 ext4 镜像以读写方式挂载到 custom-root | 卸载 → 从 staging 重新 mksquashfs |
| **EROFS 镜像内嵌 ext4 根镜像**（新版 Fedora） | 只读挂载 EROFS → 拷贝到 staging → 内嵌镜像读写挂载 | 同上 |
| **EROFS / squashfs 直接含根目录树**（Fedora 45 等新版布局） | 直接复制目录树到 custom-root（不挂载） | mksquashfs 重打包 |
| 裸 ext2/3/4 根镜像 | 拷贝到 staging 后读写挂载 | 原样回写（保持格式） |

其它适配：

- 引导目录探测支持 `images/pxeboot`、`isolinux`、`boot`，内核文件支持 `vmlinuz0`、`vmlinuz-*`、`initrd0.img`、`initramfs-*`
- 内核版本号解析兼容 Fedora 后缀（如 `6.12.4-300.fc45.x86_64`）
- 软件包清单查询按家族使用 `rpm --root`（Fedora 系）或 `dpkg-query`（Debian 系）
- 软件包页移除清单对 Fedora 系输出 Kickstart 排除片段（`%packages -pkg`）
- 生成时自动修正引导参数：SELinux 强制模式改为宽容（`enforcing=0`，Debian 宿主机无法保留 ext4 扩展属性中的 SELinux 标签，否则 PID1 因 Permission denied 中止）；自动移除 `rd.live.check` 避免误判媒体损坏；均幂等，不影响用户自定义参数
- 生成后自动植入媒体检查 MD5（`implantisomd5`）：Fedora live 默认引导项是 "Test this media"（`rd.live.check`），依赖嵌入 ISO 的校验区；仅重新压缩内容而不更新校验会导致校验失败 halt，本版本自动生成后重新植入
- 生成阶段自动纠正卷标：扫描引导配置中实际引用的 `root=live:CDLABEL/LABEL` 标签，将自定义卷标自动对齐（ESP 镜像 efiboot.img 内嵌的配置无法改写，因此以配置为准）。Fedora 系默认保留原卷标
- initramfs 支持 Zstandard（zstd）压缩格式
- 引导目录未识别（如 UKI 镜像）时保留原始引导文件与配置，不做改写
- 宿主机 SELinux 处于 Enforcing 时，进入 chroot 前自动切换 Permissive、退出后恢复
- 全部长时命令（rsync / unsquashfs / mksquashfs 等）显式指定工作目录，免疫启动目录被卸载导致的 `getcwd()` 失败

### 2. 与原版 cubic 并存安装

- 包名 `cubic-fedora`，安装路径 `/usr/share/cubic-fedora/`，命令 `/usr/bin/cubic-fedora`
- polkit 策略、desktop 文件、man 页、bash 补全、图标全部独立命名（action id 前缀 `cubic-fedora.`）
- 应用配置目录独立（`~/.config/cubic-fedora/`）

### 3. 界面与本地化

- 所有可见文本品牌化为 **Cubic-Fedora**，"Ubuntu" 相关文案改为 "Fedora"
- 新增轻量 i18n 机制：翻译以**明文**存储于 `cubic/i18n/zh_CN.txt`（`原文 = 译文`，一行一条），可手动编辑，无需编译
- 界面默认英文；`···` 菜单 → "Switch Language / 切换语言" 即时切换中英文（双向映射）
- About 对话框更新为 fork 仓库与作者信息（原作者 PJ Singh 一并致谢）

### 4. 稳定性改进

- 提取进度实时可见：unsquashfs 百分比 + rsync 百分比 + 每 3 秒的 MB 级监控输出；从命令行启动时所有日志实时回显
- 分析失败正确显示错误（原版会静默转圈）
- 跳过 Debian 专属产物（`README.diskdefines`、`.disk/info`、filesystem.size/manifest）

## 构建 .deb

```bash
sudo apt install debhelper dh-python python3-all
dpkg-buildpackage -us -uc -b
sudo apt install ../cubic-fedora_*.deb     # 会自动补齐 rpm 等依赖
```

生成的是 `Architecture: all` 包；与已安装的官方 `cubic` 互不覆盖，可共存。卸载：`sudo apt remove cubic-fedora`。

## 使用概要

```bash
cubic-fedora                                  # 或从应用菜单启动 "Cubic-Fedora"
```

1. 选择项目目录 → 选择原始 Feidora/Fedora/Ubuntu/Debian ISO
2. 提取（自动识别镜像格式）→ 定制（chroot 终端）
3. 生成（自动重打包对应格式）→ 完成

## 许可证

- 原项目代码遵循 GPL-3.0，版权归 PJ Singh 所有
- 本分支的修改同样以 GPL-3.0 发布，修改部分版权归 maylog 所有
- 详见 `debian/copyright`

# Cubic-Fedora

English documentation comes first; the Chinese documentation follows in [Part 2](#part-2--中文说明).

## Part 1 · English

### Overview

**Cubic-Fedora** (Cubic_fedora) is a fork of [Cubic — Custom Ubuntu ISO Creator](https://github.com/PJ-Singh-001/Cubic), maintained by [maylog](https://github.com/mayloglog/cubic_fedora).

The original Cubic, by PJ Singh, creates customized Live ISOs for Ubuntu/Debian based distributions. Cubic-Fedora keeps all of that and extends it with support for **Fedora-family (Feidora) Live ISOs**, plus package-name and user-interface branding, so it can be installed side by side with the original `cubic`.

> Credits: this project builds on PJ Singh's [Cubic](https://github.com/PJ-Singh-001/Cubic) (GPL-3.0). Thanks to the original author and the community for their continued work.

### Main changes

#### 1. Fedora-family (Feidora) Live ISO support

The original Cubic only handles Debian-family (casper) layouts. Fedora Live images use the dracut `dmsquash-live` scheme, where the root file system can be organized in several different ways. Cubic-Fedora introduces a "distribution family" (`distro_family`: `debian` / `fedora`) concept, detects the family automatically during extraction, and dispatches according to the real image layout:

| Source image format (auto-detected) | Extraction | Generation |
|---|---|---|
| squashfs containing the root tree directly (Debian family) | unsquashfs into custom-root | repack with mksquashfs |
| squashfs with an embedded ext4 root image (`LiveOS/ext3fs.img` / `rootfs.img`, classic Fedora) | unpack to staging, mount the embedded ext4 image read/write at custom-root | unmount → mksquashfs from staging |
| **EROFS with an embedded ext4 root image** (newer Fedora) | mount EROFS read-only → copy to staging → mount the embedded image read/write | same as above |
| **EROFS / squashfs containing the root tree directly** (Fedora 45 and similar) | copy the tree into custom-root (no mounting) | repack with mksquashfs |
| bare ext2/3/4 root image | copy to staging, then mount read/write | write back as-is (format preserved) |

Other adaptations:

- boot directory detection covers `images/pxeboot`, `isolinux` and `boot`; kernel files support `vmlinuz0`, `vmlinuz-*`, `initrd0.img` and `initramfs-*`
- kernel version parsing handles Fedora suffixes (for example `6.12.4-300.fc45.x86_64`)
- package manifest queries use `rpm --root` (Fedora family) or `dpkg-query` (Debian family)
- the removable-package list emits Kickstart exclusion snippets (`%packages -pkg`) for the Fedora family
- boot parameters are corrected automatically at generation time: SELinux enforcing is switched to permissive (`enforcing=0`, because a Debian host cannot preserve SELinux labels in ext4 extended attributes, otherwise PID 1 stops with Permission denied), and `rd.live.check` is removed to avoid false media failures; both are idempotent and never touch user-defined parameters
- the media-check MD5 is implanted (`implantisomd5`) after generation: the default Fedora live entry is "Test this media" (`rd.live.check`), which relies on the checksum area embedded in the ISO; repacking the content without updating it makes the check fail and the boot halt, so this version re-implants it automatically
- the volume label is corrected at generation time: the labels actually referenced by the boot configurations (`root=live:CDLABEL/LABEL`) are scanned and the custom label is aligned to them (the configuration embedded in the ESP image `efiboot.img` cannot be rewritten, so the configuration wins). For the Fedora family the original label is kept by default
- initramfs supports Zstandard (zstd) compression
- **kernel selection takes effect for Fedora**: at generation the selected vmlinuz / initramfs is written over the loader paths that the boot configurations actually reference (such as `/boot/x86_64/loader/linux|initrd`, `/images/pxeboot/vmlinuz|initrd.img`); the paths stay the same, so BIOS and UEFI (including the configuration embedded in `efiboot.img`) both point at the replaced files
- the "reuse the existing compressed Linux file system" fast mode only skips recompression; the boot files (kernel / initramfs) are still updated according to the Kernel tab, otherwise the generated ISO keeps the old kernel of the original image
- when the boot directory is not identified (for example a UKI image), the original boot files and configurations are kept and nothing is rewritten
- when the host runs SELinux in Enforcing mode, it is switched to Permissive before entering the chroot and restored afterwards
- every long-running command (rsync / unsquashfs / mksquashfs, etc.) is given an explicit working directory, so it is immune to `getcwd()` failures when the launch directory gets unmounted

#### 2. Side-by-side installation with upstream cubic

- package name `cubic-fedora`, install path `/usr/share/cubic-fedora/`, command `/usr/bin/cubic-fedora`
- polkit policy, desktop file, man page, bash completion and icons are all named independently (action ids prefixed with `cubic-fedora.`)
- separate application configuration directory (`~/.config/cubic-fedora/`)

#### 3. Interface and localization

- every visible string is branded **Cubic-Fedora**, and "Ubuntu" wording is changed to "Fedora"
- a lightweight i18n mechanism is added: translations are stored as **plain text** in `cubic/i18n/zh_CN.txt` (`original = translation`, one per line), editable by hand, no compilation needed
- the interface defaults to English; the `···` menu → "Switch Language / 切换语言" switches between English and Chinese instantly (bidirectional mapping)
- the About dialog points at the fork repository and author, with thanks to the original author PJ Singh

#### 4. Stability improvements

- extraction progress is live: unsquashfs percentage + rsync percentage + an MB-level monitor line every 3 seconds; when started from a command line, all log output is echoed in real time
- analysis failures are reported properly (the original silently kept spinning)
- Debian-only artifacts are skipped (`README.diskdefines`, `.disk/info`, filesystem.size / manifest)

### Building the .deb package (Debian / Ubuntu)

```bash
sudo apt install debhelper dh-python python3-all
dpkg-buildpackage -us -uc -b
sudo apt install ../cubic-fedora_*.deb     # pulls in rpm, isomd5sum, etc.
```

The result is an `Architecture: all` package; it does not overwrite the official `cubic` and can coexist with it. Remove with `sudo apt remove cubic-fedora`.

### Building the .rpm package (Fedora / openSUSE / RHEL)

On Fedora (or openSUSE/RHEL with the equivalents installed):

```bash
sudo dnf install -y rpm-build rpmdevtools   # on openSUSE: zypper in rpm-build
rpmdev-setuptree
cp cubic-fedora-2026.12.20-feidora1.tar.gz ~/rpmbuild/SOURCES/
```

Write `~/rpmbuild/SPECS/cubic-fedora.spec`:

```spec
Name:           cubic-fedora
Version:        2026.12.20
Release:        1%{?dist}
Summary:        Wizard to create customized Fedora / Ubuntu Live ISOs (Cubic fork)
License:        GPL-3.0-only
URL:            https://github.com/mayloglog/cubic_fedora
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Requires:       python3-gobject
Requires:       gtk3
Requires:       gtksourceview4
Requires:       vte2.91
Requires:       policykit-1
Requires:       rsync
Requires:       squashfs-tools
Requires:       xorriso
Requires:       systemd
Requires:       rpm
Requires:       isomd5sum
Requires:       binwalk

%description
Cubic-Fedora (Cubic_fedora) is the Fedora branch of Cubic. It supports
extracting, customizing in a chroot and repacking the many Live ISO layouts
of the Feidora/Fedora family, and can be installed alongside upstream cubic.

%prep
%setup -q -n %{name}-%{version}

%install
install -d -m 755 %{buildroot}%{_datadir}/%{name}
cp -a usr/share/%{name}/. %{buildroot}%{_datadir}/%{name}/
install -d -m 755 %{buildroot}%{_bindir}
ln -sf %{_datadir}/%{name}/cubic_wizard.py %{buildroot}%{_bindir}/%{name}
install -d -m 755 %{buildroot}%{_datadir}/applications
install -m 644 usr/share/applications/%{name}.desktop %{buildroot}%{_datadir}/applications/
install -d -m 755 %{buildroot}%{_datadir}/polkit-1/actions
install -m 644 usr/share/polkit-1/actions/%{name}.policy %{buildroot}%{_datadir}/polkit-1/actions/
cp -a usr/share/icons %{buildroot}%{_datadir}/
install -d -m 755 %{buildroot}%{_mandir}/man1
install -m 644 usr/share/man/man1/%{name}.1 %{buildroot}%{_mandir}/man1/

%files
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/polkit-1/actions/%{name}.policy
%{_datadir}/icons/hicolor/*/apps/%{name}.*
%{_datadir}/icons/hicolor/scalable/status/%{name}-*-symbolic.svg
%{_mandir}/man1/%{name}.1*

%changelog
* Wed Nov 25 2026 maylog <mayloglog@users.noreply.github.com> - 2026.12.20-1
- Keep the boot files (kernel / initramfs) updated in the "reuse squashfs" fast mode
```

Pack the source tree (without `debian/`) and build:

```bash
tar -czf ~/rpmbuild/SOURCES/cubic-fedora-2026.12.20-feidora1.tar.gz \
    --transform 's,^,cubic-fedora-2026.12.20/,' usr README.md
rpmbuild -bb ~/rpmbuild/SPECS/cubic-fedora.spec
sudo dnf install ~/rpmbuild/RPMS/noarch/cubic-fedora-*.rpm
```

> The same steps cross-build on a Debian host: `sudo apt install rpm rpm-build binutils`.
> `rpmbuild` requires the tarball directory name to match `%{name}-%{version}`, which the `--transform` above guarantees. If you ship the release tarball that unpacks to `cubic-fedora/`, add `-n cubic-fedora` to `%setup`.

### Building the Arch package (Arch / Manjaro / EndeavourOS)

```bash
sudo pacman -S --needed base-devel git
```

`PKGBUILD`:

```bash
pkgname=cubic-fedora
pkgver=2026.12.20
pkgrel=1
pkgdesc='Wizard to create customized Fedora / Ubuntu Live ISOs (Cubic fork)'
arch=('any')
url='https://github.com/mayloglog/cubic_fedora'
license=('GPL3')
depends=('python' 'python-gobject' 'gtk3' 'gtksourceview4' 'vte3'
         'polkit' 'rsync' 'squashfs-tools' 'libisoburn' 'systemd' 'rpm')
makedepends=()
optdepends=('isomd5sum: Fedora media-check support')
source=("cubic-fedora-$pkgver.tar.xz")
sha256sums=('SKIP')

package() {
  cd "$srcdir/cubic-fedora"
  install -d -m 755 "$pkgdir/usr/share/$pkgname"
  cp -a usr/share/$pkgname/. "$pkgdir/usr/share/$pkgname/"
  install -d -m 755 "$pkgdir/usr/bin"
  ln -sf /usr/share/$pkgname/cubic_wizard.py "$pkgdir/usr/bin/$pkgname"
  install -d -m 755 "$pkgdir/usr/share/applications"
  install -m 644 usr/share/applications/$pkgname.desktop "$pkgdir/usr/share/applications/"
  install -d -m 755 "$pkgdir/usr/share/polkit-1/actions"
  install -m 644 usr/share/polkit-1/actions/$pkgname.policy "$pkgdir/usr/share/polkit-1/actions/"
  cp -a usr/share/icons "$pkgdir/usr/share/"
  install -d -m 755 "$pkgdir/usr/share/man/man1"
  install -m 644 usr/share/man/man1/$pkgname.1 "$pkgdir/usr/share/man/man1/"
}
```

```bash
makepkg -si
```

> Replace the `source` line with `source=("git+${url}.git#branch=main")` to build straight from the repository; then `cd "$srcdir/cubic_fedora"` in `package()`.
> `isomd5sum` is not in the official Arch repositories (AUR only). When it is missing the program skips the implant step with a notice, and ISO generation still works.

### Usage

```bash
cubic-fedora                                  # or start "Cubic-Fedora" from the application menu
```

1. choose the project directory → choose the original Feidora/Fedora/Ubuntu/Debian ISO
2. extract (image layout is detected automatically) → customize (chroot terminal)
3. generate (repack in the matching format) → finish

> Tip: after installing a new kernel in the chroot terminal with something like `dnf install kernel-core`, the Fedora initramfs is built for an installed system and does not necessarily contain the live modules. If the live session does not start with the new kernel, rebuild it in the terminal:
> ```bash
> dracut --add dmsquash-live --force /boot/initramfs-$(uname -r).img $(uname -r)
> ```

### License

- the original project is licensed under GPL-3.0, copyright PJ Singh
- the modifications of this branch are released under GPL-3.0 as well, copyright maylog for the modified parts
- see `debian/copyright` for details

---

## Part 2 · 中文说明

### 项目简介

**Cubic-Fedora**（Cubic_fedora）是 [Cubic — Custom Ubuntu ISO Creator](https://github.com/PJ-Singh-001/Cubic) 的一个分支（fork），由 [maylog](https://github.com/mayloglog/cubic_fedora) 维护。

Cubic 原版由 PJ Singh 开发，用于定制基于 Ubuntu/Debian 的 Live ISO。Cubic-Fedora 在保留原版全部能力的基础上，扩展了对 **Fedora 系（Feidora）发行版 Live ISO** 的支持，并做了包名与界面品牌化处理，可与原版 `cubic` 并存安装。

> 致谢：本项目基于 PJ Singh 的 [Cubic](https://github.com/PJ-Singh-001/Cubic)（GPL-3.0），感谢原作者及社区的持续工作。

### 主要改动

#### 1. Fedora 系（Feidora）Live ISO 支持

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
- **内核选择对 Fedora 生效**：生成时把选定的 vmlinuz / initramfs 覆盖写入引导配置实际引用的 loader 路径（如 `/boot/x86_64/loader/linux|initrd`、`/images/pxeboot/vmlinuz|initrd.img`），路径不变 → BIOS 与 UEFI（含 efiboot.img 内嵌配置）都指向替换后的文件
- 「复用已压缩的 Linux 文件系统」快速模式只跳过重压缩这一步，引导文件（内核 / initramfs）仍按内核页的选择更新，否则生成的 ISO 会继续沿用原始镜像里的老内核
- 引导目录未识别（如 UKI 镜像）时保留原始引导文件与配置，不做改写
- 宿主机 SELinux 处于 Enforcing 时，进入 chroot 前自动切换 Permissive、退出后恢复
- 全部长时命令（rsync / unsquashfs / mksquashfs 等）显式指定工作目录，免疫启动目录被卸载导致的 `getcwd()` 失败

#### 2. 与原版 cubic 并存安装

- 包名 `cubic-fedora`，安装路径 `/usr/share/cubic-fedora/`，命令 `/usr/bin/cubic-fedora`
- polkit 策略、desktop 文件、man 页、bash 补全、图标全部独立命名（action id 前缀 `cubic-fedora.`）
- 应用配置目录独立（`~/.config/cubic-fedora/`）

#### 3. 界面与本地化

- 所有可见文本品牌化为 **Cubic-Fedora**，"Ubuntu" 相关文案改为 "Fedora"
- 新增轻量 i18n 机制：翻译以**明文**存储于 `cubic/i18n/zh_CN.txt`（`原文 = 译文`，一行一条），可手动编辑，无需编译
- 界面默认英文；`···` 菜单 → "Switch Language / 切换语言" 即时切换中英文（双向映射）
- About 对话框更新为 fork 仓库与作者信息（原作者 PJ Singh 一并致谢）

#### 4. 稳定性改进

- 提取进度实时可见：unsquashfs 百分比 + rsync 百分比 + 每 3 秒的 MB 级监控输出；从命令行启动时所有日志实时回显
- 分析失败正确显示错误（原版会静默转圈）
- 跳过 Debian 专属产物（`README.diskdefines`、`.disk/info`、filesystem.size/manifest）

### 构建 .deb（Debian / Ubuntu 系）

```bash
sudo apt install debhelper dh-python python3-all
dpkg-buildpackage -us -uc -b
sudo apt install ../cubic-fedora_*.deb     # 会自动补齐 rpm 等依赖
```

生成的是 `Architecture: all` 包；与已安装的官方 `cubic` 互不覆盖，可共存。卸载：`sudo apt remove cubic-fedora`。

### 构建 .rpm（Fedora / openSUSE / RHEL 系）

在 Fedora 上（openSUSE 装好对应的 rpm-build 后同理）：

```bash
sudo dnf install -y rpm-build rpmdevtools   # openSUSE：zypper in rpm-build
rpmdev-setuptree
cp cubic-fedora-2026.12.20-feidora1.tar.gz ~/rpmbuild/SOURCES/
```

`~/rpmbuild/SPECS/cubic-fedora.spec`：

```spec
Name:           cubic-fedora
Version:        2026.12.20
Release:        1%{?dist}
Summary:        Wizard to create customized Fedora / Ubuntu Live ISOs (Cubic fork)
License:        GPL-3.0-only
URL:            https://github.com/mayloglog/cubic_fedora
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Requires:       python3-gobject
Requires:       gtk3
Requires:       gtksourceview4
Requires:       vte2.91
Requires:       policykit-1
Requires:       rsync
Requires:       squashfs-tools
Requires:       xorriso
Requires:       systemd
Requires:       rpm
Requires:       isomd5sum
Requires:       binwalk

%description
Cubic-Fedora（Cubic_fedora）是 Cubic 的 Fedora 分支，支持 Feidora/Fedora 系
Live ISO 的多布局提取、chroot 定制与重打包，可与上游 cubic 包共存安装。

%prep
%setup -q -n %{name}-%{version}

%install
install -d -m 755 %{buildroot}%{_datadir}/%{name}
cp -a usr/share/%{name}/. %{buildroot}%{_datadir}/%{name}/
install -d -m 755 %{buildroot}%{_bindir}
ln -sf %{_datadir}/%{name}/cubic_wizard.py %{buildroot}%{_bindir}/%{name}
install -d -m 755 %{buildroot}%{_datadir}/applications
install -m 644 usr/share/applications/%{name}.desktop %{buildroot}%{_datadir}/applications/
install -d -m 755 %{buildroot}%{_datadir}/polkit-1/actions
install -m 644 usr/share/polkit-1/actions/%{name}.policy %{buildroot}%{_datadir}/polkit-1/actions/
cp -a usr/share/icons %{buildroot}%{_datadir}/
install -d -m 755 %{buildroot}%{_mandir}/man1
install -m 644 usr/share/man/man1/%{name}.1 %{buildroot}%{_mandir}/man1/

%files
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/polkit-1/actions/%{name}.policy
%{_datadir}/icons/hicolor/*/apps/%{name}.*
%{_datadir}/icons/hicolor/scalable/status/%{name}-*-symbolic.svg
%{_mandir}/man1/%{name}.1*

%changelog
* Wed Nov 25 2026 maylog <mayloglog@users.noreply.github.com> - 2026.12.20-1
- 复用压缩文件系统时仍更新引导文件（内核 / initramfs）
```

打包源码树（去掉 `debian/`）后构建：

```bash
tar -czf ~/rpmbuild/SOURCES/cubic-fedora-2026.12.20-feidora1.tar.gz \
    --transform 's,^,cubic-fedora-2026.12.20/,' usr README.md
rpmbuild -bb ~/rpmbuild/SPECS/cubic-fedora.spec
sudo dnf install ~/rpmbuild/RPMS/noarch/cubic-fedora-*.rpm
```

> Debian 宿主机上也可交叉构建：`sudo apt install rpm rpm-build binutils`，其余步骤相同。
> `rpmbuild` 要求压缩包顶层目录与 `%{name}-%{version}` 一致，上面的 `--transform` 已保证这一点；若直接使用解包后顶层为 `cubic-fedora/` 的发行包，请给 `%setup` 加 `-n cubic-fedora`。

### 构建 Arch 系包（Arch / Manjaro / EndeavourOS）

```bash
sudo pacman -S --needed base-devel git
```

`PKGBUILD`：

```bash
pkgname=cubic-fedora
pkgver=2026.12.20
pkgrel=1
pkgdesc='Wizard to create customized Fedora / Ubuntu Live ISOs (Cubic fork)'
arch=('any')
url='https://github.com/mayloglog/cubic_fedora'
license=('GPL3')
depends=('python' 'python-gobject' 'gtk3' 'gtksourceview4' 'vte3'
         'polkit' 'rsync' 'squashfs-tools' 'libisoburn' 'systemd' 'rpm')
makedepends=()
optdepends=('isomd5sum: Fedora media-check support')
source=("cubic-fedora-$pkgver.tar.xz")
sha256sums=('SKIP')

package() {
  cd "$srcdir/cubic-fedora"
  install -d -m 755 "$pkgdir/usr/share/$pkgname"
  cp -a usr/share/$pkgname/. "$pkgdir/usr/share/$pkgname/"
  install -d -m 755 "$pkgdir/usr/bin"
  ln -sf /usr/share/$pkgname/cubic_wizard.py "$pkgdir/usr/bin/$pkgname"
  install -d -m 755 "$pkgdir/usr/share/applications"
  install -m 644 usr/share/applications/$pkgname.desktop "$pkgdir/usr/share/applications/"
  install -d -m 755 "$pkgdir/usr/share/polkit-1/actions"
  install -m 644 usr/share/polkit-1/actions/$pkgname.policy "$pkgdir/usr/share/polkit-1/actions/"
  cp -a usr/share/icons "$pkgdir/usr/share/"
  install -d -m 755 "$pkgdir/usr/share/man/man1"
  install -m 644 usr/share/man/man1/$pkgname.1 "$pkgdir/usr/share/man/man1/"
}
```

```bash
makepkg -si
```

> 也可把 `source` 换成 `source=("git+${url}.git#branch=main")` 直接从仓库构建，此时 `package()` 里改为 `cd "$srcdir/cubic_fedora"`。
> Arch 官方仓库无 `isomd5sum`（媒体检查用的 `implantisomd5`，仅 AUR 提供）；缺失时程序会自动跳过并给出提示，不影响生成 ISO。

### 使用概要

```bash
cubic-fedora                                  # 或从应用菜单启动 "Cubic-Fedora"
```

1. 选择项目目录 → 选择原始 Feidora/Fedora/Ubuntu/Debian ISO
2. 提取（自动识别镜像格式）→ 定制（chroot 终端）
3. 生成（自动重打包对应格式）→ 完成

> 提示：在 chroot 终端里用 `dnf install kernel-core` 等方式装了新内核之后，Fedora 生成的 initramfs 默认是「已安装系统」用的，不一定包含 live 模块。如果换了内核后 live 起不来，请在终端内重建：
> ```bash
> dracut --add dmsquash-live --force /boot/initramfs-$(uname -r).img $(uname -r)
> ```

### 许可证

- 原项目代码遵循 GPL-3.0，版权归 PJ Singh 所有
- 本分支的修改同样以 GPL-3.0 发布，修改部分版权归 maylog 所有
- 详见 `debian/copyright`

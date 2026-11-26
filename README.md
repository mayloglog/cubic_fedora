# Cubic-Fedora

> Languages: **English** | [中文](#中文文档)

---

## English

**Cubic-Fedora** (Cubic_fedora) is a fork of [Cubic — Custom Ubuntu ISO Creator](https://github.com/PJ-Singh-001/Cubic), maintained by [maylog](https://github.com/mayloglog/cubic_fedora).

The original Cubic was written by PJ Singh to customize Ubuntu/Debian based Live ISOs. Cubic-Fedora keeps every capability of the original and adds support for **Fedora family Live ISOs**. It also has its own package name and branding, so it can be installed side by side with the original `cubic` package.

> Credits: this project is based on PJ Singh's [Cubic](https://github.com/PJ-Singh-001/Cubic) (GPL-3.0). Thanks to the original author and the community for their continued work.

### Main changes

#### 1. Fedora family Live ISO support

The original Cubic only supports the Debian family (casper) layout. Fedora live images use the dracut `dmsquash-live` scheme, and the root file system can be organized in several different ways. Cubic-Fedora introduces the concept of a "distribution family" (`debian` / `fedora`), detects the family automatically during extraction, and dispatches the work according to the real format of the image:

| Source image format (auto detected) | Extraction | Generation |
|---|---|---|
| squashfs that directly contains the root tree (Debian family) | unsquashfs into custom-root | repack with mksquashfs |
| squashfs with an embedded ext4 root image (`LiveOS/ext3fs.img` / `rootfs.img`, classic Fedora) | unpack into staging, mount the embedded ext4 image read-write onto custom-root | unmount → new mksquashfs from staging |
| **EROFS image with an embedded ext4 root image** (newer Fedora) | read-only mount EROFS → copy into staging → mount the embedded image read-write | same as above |
| **EROFS / squashfs that directly contains the root tree** (newer layouts such as Fedora 45) | copy the directory tree into custom-root (no mounting) | mksquashfs |
| bare ext2/3/4 root image | copy into staging, then mount read-write | written back unchanged (format preserved) |

Other adaptations:

- Boot directory probing supports `images/pxeboot`, `isolinux` and `boot`; kernel file names support `vmlinuz0`, `vmlinuz-*`, `initrd0.img` and `initramfs-*`
- Kernel version parsing is compatible with Fedora suffixes (for example `6.12.4-300.fc45.x86_64`); the complete release is preserved so that dracut finds the matching `/lib/modules` directory
- Package list queries use `rpm --root` (Fedora family) or `dpkg-query` (Debian family), depending on the detected family
- The package page removal list emits Kickstart exclusion snippets (`%packages -pkg`) for the Fedora family
- Boot parameters are corrected automatically during generation: SELinux enforcing mode is switched to permissive (`enforcing=0`, because a Debian host cannot keep the SELinux labels stored in the ext4 extended attributes and PID 1 would abort with "Permission denied"), and `rd.live.check` is removed to avoid false "media damaged" results. Both changes are idempotent and do not affect user-defined parameters
- The media check MD5 (`implantisomd5`) is embedded again after generation: the default Fedora live boot entry is "Test this media" (`rd.live.check`), which relies on the checksum area embedded in the ISO; recompressing the content without updating the checksum makes the machine halt with a checksum error, so this version re-embeds it automatically
- The volume label is corrected automatically during generation: the `root=live:CDLABEL/LABEL` labels actually referenced by the boot configurations are scanned and the custom label is aligned with them (the configuration embedded in the ESP image `efiboot.img` cannot be rewritten, so the configuration wins). The Fedora family keeps the original label by default
- initramfs files compressed with Zstandard (zstd) are supported
- **Kernel selection now works for Fedora**: the selected vmlinuz / initramfs are copied over the loader paths that the boot configurations actually reference (for example `/boot/x86_64/loader/linux|initrd` and `/images/pxeboot/vmlinuz|initrd.img`). The paths stay the same, so both BIOS and UEFI (including the configuration embedded in `efiboot.img`) point at the replaced files
- **Manually choose the ISO kernel or the chroot kernel**: the Options → Kernel page now has a source selector and a "Refresh list" button; the kernels found in the original ISO and in the chroot `/boot` are listed separately, and the selection of each source is remembered independently. When scanning a Fedora ISO, unconventional kernel file names referenced by the boot configurations (such as `/boot/x86_64/loader/linux`) are parsed, and the relative `initrd=initrd.img` form used by isolinux is supported
- **Automatic live initramfs rebuild and verification**: when a chroot kernel is selected, Cubic first rebuilds a live initramfs with `dmsquash-live livenet` inside the chroot using dracut and only then copies it to the ISO. Before the rebuild the complete kernel release is restored from the vmlinuz file name (for example `7.3.4-300.fc45.x86_64`) and checked against `/lib/modules`, and a dracut failure is no longer reported as success. After writing, the gzip/xz/bzip2/zstd/lz4 compressed cpio archives are parsed directly to confirm that every initrd contains `dmsquash-live`; if not, generation is aborted and the commands needed to fix it are shown, so no ISO that stops in dracut is produced
- **Fast generation mode**: even when "reuse the compressed Linux file system" is selected, the Fedora family still applies the selected kernel to the boot files; note that `/usr/lib/modules` inside the squashfs still holds the old kernel module tree, so use the normal generation flow for a complete and usable ISO
- When the boot directory cannot be recognized (for example UKI images), the original boot files and configurations are kept and nothing is rewritten
- When SELinux on the host is Enforcing, it is switched to Permissive before entering the chroot and restored afterwards
- All long running commands (rsync / unsquashfs / mksquashfs and so on) specify a working directory explicitly, which immunizes them against `getcwd()` failures caused by an unmounted start directory

#### 2. Side by side installation with the original cubic

- Package name `cubic-fedora`, installation path `/usr/share/cubic-fedora/`, command `/usr/bin/cubic-fedora`
- The polkit policy, desktop file, man page, bash completion and icons all use their own names (action id prefix `cubic-fedora.`)
- Separate application configuration directory (`~/.config/cubic-fedora/`)

#### 3. User interface and localization

- All visible text is branded as **Cubic-Fedora**, and the wording about "Ubuntu" is changed to "Fedora"
- A lightweight i18n mechanism was added: the translations are stored as **plain text** in `cubic/i18n/zh_CN.txt` (`original = translation`, one entry per line), can be edited by hand and need no compilation
- The interface starts in English; the `···` menu → "Switch Language / 切换语言" switches between English and Chinese immediately (bidirectional mapping)
- The About dialog now shows the fork repository and author information (the original author PJ Singh is credited as well)

#### 4. Stability improvements

- Extraction progress is visible in real time: the unsquashfs percentage, the rsync percentage and an MB level monitor every 3 seconds; all logs are echoed live when the application is started from the command line
- Analysis failures are reported properly (the original version silently kept spinning)
- Debian specific artifacts are skipped (`README.diskdefines`, `.disk/info`, filesystem.size/manifest)

### Building the .rpm (Fedora / openSUSE / RHEL family)

```bash
sudo dnf install -y rpm-build rpmdevtools   # or: zypper in rpm-build
rpmdev-setuptree
cp cubic-fedora-2026.12.27-fedora1.tar.gz ~/rpmbuild/SOURCES/
```

`~/rpmbuild/SPECS/cubic-fedora.spec`:

```spec
Name:           cubic-fedora
Version:        2026.12.27
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
Cubic-Fedora (Cubic_fedora) is the Fedora branch of Cubic. It supports the
extraction of Fedora Live ISOs with multiple layouts, chroot based
customization and repacking, and it can be installed next to the upstream
cubic package.

%prep
%setup -q

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
* Thu Nov 26 2026 maylog <mayloglog@users.noreply.github.com> - 2026.12.27-1
- Kernel selection is written to the loader paths; the volume label, SELinux and the media checksum are corrected automatically
```

Package the source tree (without `debian/`) and build:

```bash
tar -czf ~/rpmbuild/SOURCES/cubic-fedora-2026.12.27-fedora1.tar.gz \
    --transform 's,^,cubic-fedora-2026.12.27/,' usr README.md
rpmbuild -bb ~/rpmbuild/SPECS/cubic-fedora.spec
sudo dnf install ~/rpmbuild/RPMS/noarch/cubic-fedora-*.rpm
```

> Cross building on a Debian host is possible as well: `sudo apt install rpm rpm-build binutils`, all other steps are identical.

### Building the Arch family package (Arch / Manjaro / EndeavourOS)

```bash
sudo pacman -S --needed base-devel git
```

`PKGBUILD`:

```bash
pkgname=cubic-fedora
pkgver=2026.12.27
pkgrel=1
pkgdesc='Wizard to create customized Fedora / Ubuntu Live ISOs (Cubic fork)'
arch=('any')
url='https://github.com/mayloglog/cubic_fedora'
license=('GPL3')
depends=('python' 'python-gobject' 'gtk3' 'gtksourceview4' 'vte3'
         'polkit' 'rsync' 'squashfs-tools' 'libisoburn' 'systemd' 'rpm')
makedepends=()
optdepends=('isomd5sum: Fedora media-check support')
source=("git+${url}.git#branch=main")
sha256sums=('SKIP')

package() {
  cd "$srcdir"
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

> The official Arch repositories do not provide `isomd5sum` (the `implantisomd5` tool used for the media check); when it is missing the program skips that step and shows a hint, which does not affect ISO generation.

### Building the .deb (Debian / Ubuntu family)

```bash
sudo apt install debhelper dh-python python3-all
dpkg-buildpackage -us -uc -b
sudo apt install ../cubic-fedora_*.deb     # the rpm dependency is pulled in automatically
```

The result is an `Architecture: all` package; it does not overwrite the official `cubic` package, so both can coexist. To uninstall it: `sudo apt remove cubic-fedora`.

### Usage overview

```bash
cubic-fedora                                  # or start "Cubic-Fedora" from the application menu
```

1. Choose the project directory → choose the original Fedora/Ubuntu/Debian ISO
2. Extract (the image format is detected automatically) → customize (chroot terminal)
3. Generate (repacked in the matching format automatically) → finish

> Tip: after installing a new kernel inside the chroot terminal (for example with `dnf install kernel-core`), go back to the Options → Kernel page and switch the source to "Chroot kernel (custom root /boot)". If the new kernel is not listed, click "Refresh list" to scan again, select the kernel version and generate again.
>
> When a chroot kernel is selected, Cubic automatically enters the chroot during the generation phase, rebuilds a live initramfs that contains `dmsquash-live livenet` with the target kernel release, and only then writes it to the ISO. There is no need to run dracut by hand, and the ISO no longer stops at `root=live:... is not handled` because the default "installed system" initramfs lacks the live modules.
>
> The live dracut modules must be installed in the chroot. If the generation reports that a module is missing, run the following inside the chroot terminal of the Terminal page:
> ```bash
> dnf install -y dracut dracut-live dracut-squash dracut-config-generic
> ```
> and generate again. After the rebuild, Cubic parses the initramfs contents directly to confirm that the `dmsquash-live` module is present (and verifies it again with `lsinitrd` when that tool is installed on the host).

### License

- The code of the original project is licensed under GPL-3.0 and is copyright PJ Singh
- The modifications of this branch are released under GPL-3.0 as well; the modified parts are copyright maylog
- See `debian/copyright` for details

---

## 中文文档

**Cubic-Fedora**（Cubic_fedora）是 [Cubic — Custom Ubuntu ISO Creator](https://github.com/PJ-Singh-001/Cubic) 的一个分支（fork），由 [maylog](https://github.com/mayloglog/cubic_fedora) 维护。

Cubic 原版由 PJ Singh 开发，用于定制基于 Ubuntu/Debian 的 Live ISO。Cubic-Fedora 在保留原版全部能力的基础上，扩展了对 **Fedora 系发行版 Live ISO** 的支持，并做了包名与界面品牌化处理，可与原版 `cubic` 并存安装。

> 致谢：本项目基于 PJ Singh 的 [Cubic](https://github.com/PJ-Singh-001/Cubic)（GPL-3.0），感谢原作者及社区的持续工作。

### 主要改动

#### 1. Fedora 系 Live ISO 支持

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
- 内核版本号解析兼容 Fedora 后缀（如 `6.12.4-300.fc45.x86_64`），并保留完整发布号，使 dracut 能找到对应的 `/lib/modules` 目录
- 软件包清单查询按家族使用 `rpm --root`（Fedora 系）或 `dpkg-query`（Debian 系）
- 软件包页移除清单对 Fedora 系输出 Kickstart 排除片段（`%packages -pkg`）
- 生成时自动修正引导参数：SELinux 强制模式改为宽容（`enforcing=0`，Debian 宿主机无法保留 ext4 扩展属性中的 SELinux 标签，否则 PID1 因 Permission denied 中止）；自动移除 `rd.live.check` 避免误判媒体损坏；均幂等，不影响用户自定义参数
- 生成后自动植入媒体检查 MD5（`implantisomd5`）：Fedora live 默认引导项是 "Test this media"（`rd.live.check`），依赖嵌入 ISO 的校验区；仅重新压缩内容而不更新校验会导致校验失败 halt，本版本自动生成后重新植入
- 生成阶段自动纠正卷标：扫描引导配置中实际引用的 `root=live:CDLABEL/LABEL` 标签，将自定义卷标自动对齐（ESP 镜像 efiboot.img 内嵌的配置无法改写，因此以配置为准）。Fedora 系默认保留原卷标
- initramfs 支持 Zstandard（zstd）压缩格式
- **内核选择对 Fedora 生效**：生成时把选定的 vmlinuz / initramfs 覆盖写入引导配置实际引用的 loader 路径（如 `/boot/x86_64/loader/linux|initrd`、`/images/pxeboot/vmlinuz|initrd.img`），路径不变 → BIOS 与 UEFI（含 efiboot.img 内嵌配置）都指向替换后的文件
- **手动选择 ISO 内核或 chroot 内核**：Options → Kernel 页新增来源切换与“Refresh list”；可分别查看原始 ISO 与 chroot `/boot` 中找到的内核，并独立记住每个来源的选择。扫描 Fedora ISO 时会解析引导配置中 `linux`/`initrd` 等非常规文件名（如 `/boot/x86_64/loader/linux`），并支持 isolinux 的 `initrd=initrd.img` 相对路径
- **Live initramfs 自动重建与校验**：选择 chroot 内核生成时，Cubic 会先在 chroot 内用 dracut 重建带 `dmsquash-live livenet` 的 live initramfs，再复制到 ISO；重建前会用 vmlinuz 文件名还原完整内核发布号（如 `7.3.4-300.fc45.x86_64`）并确认 `/lib/modules` 中存在对应目录，dracut 失败不再被误报为成功。写入后还会直接解析 gzip/xz/bzip2/zstd/lz4 压缩的 cpio，确认每个 initrd 都含 `dmsquash-live`，不含就中止生成并给出修复命令，避免产出停在 dracut 的 ISO
- **快速生成模式**：Fedora 系即使勾选“复用已压缩的 Linux 文件系统”，仍会应用所选内核到引导文件；但 squashfs 内的 `/usr/lib/modules` 仍是旧内核模块树，要得到完整可用的 ISO 请走正常生成流程
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

### 构建 .rpm（Fedora / openSUSE / RHEL 系）

```bash
sudo dnf install -y rpm-build rpmdevtools   # 或 zypper in rpm-build
rpmdev-setuptree
cp cubic-fedora-2026.12.27-fedora1.tar.gz ~/rpmbuild/SOURCES/
```

`~/rpmbuild/SPECS/cubic-fedora.spec`：

```spec
Name:           cubic-fedora
Version:        2026.12.27
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
Cubic-Fedora（Cubic_fedora）是 Cubic 的 Fedora 分支，支持 Fedora 系
Live ISO 的多布局提取、chroot 定制与重打包，可与上游 cubic 包共存安装。

%prep
%setup -q

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
* Thu Nov 26 2026 maylog <mayloglog@users.noreply.github.com> - 2026.12.27-1
- 内核选择写入 loader 路径；卷标/SELinux/媒体校验自动修正
```

打包源码树（去掉 `debian/`）后构建：

```bash
tar -czf ~/rpmbuild/SOURCES/cubic-fedora-2026.12.27-fedora1.tar.gz \
    --transform 's,^,cubic-fedora-2026.12.27/,' usr README.md
rpmbuild -bb ~/rpmbuild/SPECS/cubic-fedora.spec
sudo dnf install ~/rpmbuild/RPMS/noarch/cubic-fedora-*.rpm
```

> Debian 宿主机上也可交叉构建：`sudo apt install rpm rpm-build binutils`，其余步骤相同。

### 构建 Arch 系包（Arch / Manjaro / EndeavourOS）

```bash
sudo pacman -S --needed base-devel git
```

`PKGBUILD`：

```bash
pkgname=cubic-fedora
pkgver=2026.12.27
pkgrel=1
pkgdesc='Wizard to create customized Fedora / Ubuntu Live ISOs (Cubic fork)'
arch=('any')
url='https://github.com/mayloglog/cubic_fedora'
license=('GPL3')
depends=('python' 'python-gobject' 'gtk3' 'gtksourceview4' 'vte3'
         'polkit' 'rsync' 'squashfs-tools' 'libisoburn' 'systemd' 'rpm')
makedepends=()
optdepends=('isomd5sum: Fedora media-check support')
source=("git+${url}.git#branch=main")
sha256sums=('SKIP')

package() {
  cd "$srcdir"
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

> Arch 官方仓库无 `isomd5sum`（媒体检查用的 `implantisomd5`）；缺失时程序会自动跳过并给出提示，不影响生成 ISO。

### 构建 .deb（Debian / Ubuntu 系）

```bash
sudo apt install debhelper dh-python python3-all
dpkg-buildpackage -us -uc -b
sudo apt install ../cubic-fedora_*.deb     # 会自动补齐 rpm 等依赖
```

生成的是 `Architecture: all` 包；与已安装的官方 `cubic` 互不覆盖，可共存。卸载：`sudo apt remove cubic-fedora`。

### 使用概要

```bash
cubic-fedora                                  # 或从应用菜单启动 "Cubic-Fedora"
```

1. 选择项目目录 → 选择原始 Fedora/Ubuntu/Debian ISO
2. 提取（自动识别镜像格式）→ 定制（chroot 终端）
3. 生成（自动重打包对应格式）→ 完成

> 提示：在 chroot 终端里用 `dnf install kernel-core` 等方式装了新内核后，回到 Options → Kernel 页，把来源切换为 “Chroot kernel (custom root /boot)”；如果列表没有显示新内核，点击 “Refresh list” 重新扫描，然后选中该内核版本再生成。
>
> 选中 chroot 内核后，Cubic 会在生成阶段自动进入 chroot，用目标内核版本重建包含 `dmsquash-live livenet` 的 live initramfs，再写入 ISO。因此不需要再手动运行 dracut，也不会因为默认的「已安装系统」initramfs 缺少 live 模块而停在 `root=live:... is not handled`。
>
> 前提是 chroot 内已安装 live dracut 模块。如果生成时报缺少模块，请在 Terminal 页的 chroot 终端内执行：
> ```bash
> dnf install -y dracut dracut-live dracut-squash dracut-config-generic
> ```
> 然后重新生成。重建完成后 Cubic 会直接解析 initramfs 内容，确认其中含有 `dmsquash-live`（宿主机装有 `lsinitrd` 时还会再用它复核一次）。

### 许可证

- 原项目代码遵循 GPL-3.0，版权归 PJ Singh 所有
- 本分支的修改同样以 GPL-3.0 发布，修改部分版权归 maylog 所有
- 详见 `debian/copyright`

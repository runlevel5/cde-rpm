# Common Desktop Environment (CDE) RPM spec
#
# Configure with --prefix=/usr/dt (CDE's natural data namespace) and in
# %install relocate the FHS-relevant pieces (binaries, shared libraries,
# headers, man pages) into /usr/{bin,lib64,include,share/man}. The moved
# subdirs are replaced with compatibility symlinks under /usr/dt so the
# ~247 source files that hardcode /usr/dt/<...> paths keep resolving.
#
# Result for users:
#   - `which dtwm`, `man dtwm`, `ldconfig -p | grep DtSvc` all work
#   - `#include <Dt/Action.h>` works
#   - /usr/dt/{app-defaults,config,appconfig,infolib,share/{palettes,backdrops}}
#     remains as CDE's data namespace (not technically FHS-conventional but
#     unavoidable without massive source patching; documented in README.Fedora)
#   - /usr/dt/bin -> /usr/bin and /usr/dt/include -> /usr/include compat links

Name:           cde
Version:        2.5.3
Release:        1%{?dist}
Summary:        Common Desktop Environment

License:        LGPL-2.0-or-later
URL:            https://sourceforge.net/projects/cdesktopenv/
Source0:        %{name}-%{version}.tar.xz
Source1:        cde.pam
Source2:        dtlogin.service
Source3:        cde.desktop
Source4:        ld.so.conf-cde.conf
Source5:        README.Fedora
Source6:        rpc.cmsd.service

# Drop the K&R-era strstr() redeclaration in dthelp/htag2 that conflicts
# with glibc's _Generic-based <string.h> declaration.
Patch0:         0001-fproto-drop-strstr-redeclaration.patch
# Add an include/config.h stub that forwards to cde_config.h, so Motif's
# private headers (Xm/DisplayP.h etc.) can resolve <config.h>.
Patch1:         0002-include-config-h-stub-for-motif.patch
# Make CDE_INSTALLATION_TOP / CDE_CONFIGURATION_TOP / CDE_LOGFILES_TOP
# overridable via --with-cde-{config,state,libexec,data}-dir flags.
Patch2:         0003-configure-make-cde-paths-overridable.patch
# Convert raw "/usr/dt/...", "/etc/dt/...", "/var/dt/..." string literals
# in C/C++ source to CDE_*_TOP macros.
Patch3:         0004-cleanup-cc-literals-use-cde-macros.patch
# Equivalent cleanup for the .src files that go through tradcpp at build time.
Patch4:         0005-cleanup-src-files-use-cde-macros.patch
# Convert contrib/ templates to autoconf .in files.
Patch5:         0006-contrib-convert-to-autoconf-in-files.patch
# util/check-fhs.sh validation gate.
Patch6:         0007-util-add-check-fhs-validation.patch
# Split CDE_DATA_TOP from CDE_INSTALLATION_TOP; rename dt{mail,cm}.dt to .src.
Patch7:         0008-split-data-top-and-finish-dt-conversion.patch
# Dt: set *useColorObj:False globally to avoid the Motif 2.3.x color-object
# deadlock during widget Initialize. dtsession itself hangs (loading screen,
# no dtwm); every other CDE client survives but pays a 5s libXt selection
# timeout per Motif widget, making dtwm/dtfile/dtmail logins glacial.
Patch8:         0009-dt-disable-motif-color-object.patch
# Finish the FHS migration for dtinfo and the data-only directories:
# fix the second InfoLibSearchPath copy of /usr/dt missed by Patch0008,
# and drop the /share/ infix + legacy compat symlinks from
# backdrops/palettes so the install layout matches the compiled-in
# DT_BACKDROPSEARCHPATH/DTINFOLIBSEARCHPATH probes.
Patch9:         0010-fhs-finish-dtinfo-and-data-dirs.patch
# dtinfo ToolTalk ptypes hardcode legacy /usr/dt paths in their
# start-string. These strings are baked into the compiled types.xdr
# at build time, so configure flags do NOT redirect them. Without
# this patch DtInfo_LoadInfoLib comes back TT_ERR_PTYPE_START and
# dtinfo never opens from any desktop launch path.
Patch10:        0011-tttypes-fhs-dtinfo-ptype-paths.patch
# Plug two Makefile.am misses surfaced by util/check-fhs.sh:
# lib/DtSvc was missing -DCDE_LOGFILES_TOP (MsgLog.c / DtEncap/nls.c
# fell back to /var/dt/tmp), and dtspcd had -DCDE_CONFIGURATION_TOP=
# ${prefix} (a pre-existing upstream typo, pinned the SPC config dir
# to PREFIX/config instead of honoring --with-cde-config-dir).
Patch11:        0012-fhs-followup-makefile-defines.patch
# Application Manager entries (/usr/share/cde/appconfig/appmanager/.../Dtcalc
# etc.) must be executable for dtfile to treat them as actions. The upstream
# build copies programs/types/action (mode 0644) into each appmgr file and
# inherits the 0644 mode; without this dtfile opens them in dtpad instead of
# launching the action. Patches the appmgr.am template to chmod +x.
Patch12:        0013-appmgr-make-action-files-executable.patch
# Help Manager .hf families pointed *.bitmap at @prefix@/appconfig/help/...
# which with --prefix=/usr resolves to /usr/appconfig/help/.../cdelogo.pm
# (does not exist), so dthelpview renders "Missing Graphics" beside the
# "Common Desktop Environment" and "Overview and Basic Desktop Skills"
# section headers. Route the path through @CDE_DATA_TOP@ like every other
# data-tree reference.
Patch13:        0014-help-hf-bitmap-paths.patch

# Print Manager's (dtprintinfo) Help/About text pane should be white like every
# other CDE help viewer, but it inherits the desktop palette. The white help
# DisplayArea override lives in the shared Dt resources and is pulled into each
# app via #include "Dt" at the top of that app's app-defaults file. dtprintinfo
# has such a source app-defaults (programs/dtprintinfo/Dtprintinfo) but nothing
# builds or installs it -- it is missing from the app-defaults BUILT_SOURCES
# list -- so dtprintinfo loads no app-defaults, never #includes Dt, and its help
# pane falls back to the palette. (Upstream #197 misdiagnosed this as an
# XmDialogShell/TransientShell resource-scoping issue in Dt.ad; the shell is in
# fact XmDialogShell as in dtpad.) Fix wires Dtprintinfo into the app-defaults
# build with a string-free .tmsg per locale. SourceForge ticket #197.
Patch14:        0015-dtprintinfo-install-app-defaults.patch

# Build prerequisites: see configure.ac AC_CHECK_LIB / AC_PATH_PROG list
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  libtool
BuildRequires:  bison
BuildRequires:  flex
BuildRequires:  m4
BuildRequires:  perl-interpreter
BuildRequires:  ksh
BuildRequires:  ncompress
BuildRequires:  pkgconfig
BuildRequires:  motif-devel
BuildRequires:  libX11-devel
BuildRequires:  libXt-devel
BuildRequires:  libXmu-devel
BuildRequires:  libXinerama-devel
BuildRequires:  libXpm-devel
BuildRequires:  libXaw-devel
BuildRequires:  libXScrnSaver-devel
BuildRequires:  libXdmcp-devel
BuildRequires:  libXrender-devel
BuildRequires:  libXft-devel
BuildRequires:  libtirpc-devel
BuildRequires:  libutempter-devel
BuildRequires:  pam-devel
BuildRequires:  libjpeg-turbo-devel
BuildRequires:  lmdb-devel
BuildRequires:  tcl-devel
BuildRequires:  openssl-devel
BuildRequires:  rpcgen
BuildRequires:  libnsl2-devel
BuildRequires:  gettext-devel
BuildRequires:  bdftopcf
BuildRequires:  xorg-x11-fonts-misc
BuildRequires:  sessreg
BuildRequires:  xorg-x11-xbitmaps
# onsgmls (only needed if building docs)
BuildRequires:  opensp
BuildRequires:  systemd-rpm-macros

# Runtime
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Requires:       rpcbind
Requires:       ksh
Requires:       ncompress
# Some shipped scripts have `#!/usr/dt/bin/dtksh` shebangs. The actual binary
# is at /usr/bin/dtksh and /usr/dt/bin -> /usr/bin, but rpm's auto-Requires
# extractor doesn't follow that symlink, so advertise the path explicitly.
Provides:       /usr/dt/bin/dtksh
Requires:       sessreg
Requires:       xorg-x11-fonts-misc
# CDE fontaliases reference -adobe-{helvetica,times,courier}-*-iso8859-1
# bitmap PCFs. Fedora ships those families only as iso10646-1 by default;
# the ISO8859-1 re-encoded variants live in these subpackages, so pull
# them in explicitly. Without them, Motif text in dtinfo / dtfile / etc.
# renders as empty rectangles (no matching font for the requested XLFD).
Requires:       xorg-x11-fonts-ISO8859-1-100dpi
Requires:       xorg-x11-fonts-ISO8859-1-75dpi
# mkfontdir is invoked in %post to regenerate fonts.dir for the alias dirs.
Requires(post): xorg-x11-font-utils
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description
The Common Desktop Environment, the classic UNIX desktop developed by a
collaboration of HP, IBM, Sun, DEC, SCO, Fujitsu and Hitachi, open-sourced
by The Open Group in 2012. This package provides the full CDE session
including the dtlogin display manager, dtwm window manager, dtsession,
and the standard CDE applications (dtfile, dtterm, dtmail, dtcalc, dtcm,
dtpad, dtstyle, dthelp, dtinfo, dticon, dtcreate, dtprintinfo, etc.).

%package libs
Summary:        Shared libraries for CDE
# CDE libs link against motif at runtime
Requires:       motif

%description libs
Shared libraries used by the Common Desktop Environment: DtSvc, DtWidget,
DtHelp, DtPrint, DtTerm, DtMrm, DtMmdb, DtSearch, DtXinerama, ToolTalk
(libtt), and CSA (calendaring/scheduling API).

%package devel
Summary:        Development files for CDE
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Requires:       motif-devel

%description devel
Header files and library symlinks needed to build software against CDE
libraries (DtSvc, DtWidget, DtHelp, DtPrint, DtTerm, DtMrm, DtMmdb,
DtSearch, ToolTalk, CSA).

%package doc
Summary:        Documentation, online help and infolib for CDE
Requires:       %{name} = %{version}-%{release}

%description doc
User and programmer guides, dthelp volumes and dtinfo infolib content
for the Common Desktop Environment. (Not noarch — the infolib tree
contains the dtinfo_start helper binary.)

# ---- Locale subpackages (one per --enable-<lang>) ----

%package langpack-de
Summary:        German language support for CDE
BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}
Supplements:    (%{name} and langpacks-de)
%description langpack-de
German (de_DE.UTF-8) localization for CDE.

%package langpack-fr
Summary:        French language support for CDE
BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}
Supplements:    (%{name} and langpacks-fr)
%description langpack-fr
French (fr_FR.UTF-8) localization for CDE.

%package langpack-es
Summary:        Spanish language support for CDE
BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}
Supplements:    (%{name} and langpacks-es)
%description langpack-es
Spanish (es_ES.UTF-8) localization for CDE.

%package langpack-it
Summary:        Italian language support for CDE
BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}
Supplements:    (%{name} and langpacks-it)
%description langpack-it
Italian (it_IT.UTF-8) localization for CDE.

%package langpack-ja
Summary:        Japanese language support for CDE
BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}
Supplements:    (%{name} and langpacks-ja)
%description langpack-ja
Japanese (ja_JP.UTF-8) localization for CDE.

# -----------------------------------------------------------------------------
%prep
%autosetup -n %{name}-%{version} -p1


%build
./autogen.sh
# Full FHS layout. %configure forces bin/lib/include/man into the standard
# Fedora locations; the --with-cde-* flags (Patch0003) steer CDE's
# arch-independent data namespace into /usr/share/cde, configuration into
# /etc/cde, runtime state into /var/lib/cde, internal helpers into
# /usr/libexec/cde. Patch0008 makes the codebase actually honor those.
export CFLAGS="%{optflags} -Wno-error -Wno-format-truncation -Wno-write-strings -Wno-unused-result -fno-strict-aliasing -fcommon"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="%{?build_ldflags} -Wl,-z,notext"
%configure \
    --prefix=/usr \
    --sysconfdir=/etc \
    --localstatedir=/var \
    --with-pam-dir=/etc/pam.d \
    --with-cde-data-dir=%{_datadir}/cde \
    --with-cde-config-dir=%{_sysconfdir}/cde \
    --with-cde-state-dir=/var/lib/cde \
    --with-cde-libexec-dir=%{_libexecdir}/cde \
    --enable-german \
    --enable-french \
    --enable-spanish \
    --enable-italian \
    --enable-japanese
# Note: do NOT pass --enable-docs. configure.ac's AC_ARG_ENABLE has both
# action-if-given branches set disable_docs=yes, so passing either flag
# disables docs. The default (no flag) sets BUILD_DOCS=true.

%make_build

%install
%make_install

# Patch0008 migrated the CDE arch-independent data tree to $(CDE_DATA_TOP)
# but left the "config" subdir on $(CDE_INSTALLATION_TOP). With --prefix=/usr
# that puts config at /usr/config -- non-FHS. Move it to /etc/cde/config
# where CDE_CONFIGURATION_TOP already points.
if [ -d %{buildroot}/usr/config ]; then
    mkdir -p %{buildroot}%{_sysconfdir}/cde
    mv %{buildroot}/usr/config %{buildroot}%{_sysconfdir}/cde/config
fi

# Xsession is CDE's per-login bootstrap script (modeled after
# /etc/gdm/Xsession). FHS-idiomatic location is /etc/<dm>/Xsession; move
# it from /usr/bin/Xsession to /etc/cde/Xsession and leave a /usr/bin
# symlink behind for backwards-compat with the path baked into dtlogin's
# compiled binary.
if [ -e %{buildroot}%{_bindir}/Xsession ]; then
    mv %{buildroot}%{_bindir}/Xsession %{buildroot}%{_sysconfdir}/cde/Xsession
    ln -s %{_sysconfdir}/cde/Xsession %{buildroot}%{_bindir}/Xsession
fi

# CDE upstream drops CONTRIBUTORS/COPYING/HISTORY/README straight under
# $(CDE_INSTALLATION_TOP). With --prefix=/usr that's root-level pollution
# at /usr/CONTRIBUTORS etc. We ship the docs via %doc/%license. Drop them.
# (KEEP /usr/copyright -- dthello reads it as the CDE splash-screen text;
# deleting it breaks the loading screen.) The backdrops/palettes compat
# symlinks are dropped at the Makefile level by Patch0010.
rm -f %{buildroot}/usr/CONTRIBUTORS \
      %{buildroot}/usr/COPYING \
      %{buildroot}/usr/HISTORY \
      %{buildroot}/usr/README.md

# cde/doc/Makefile.am's install-data-hook creates /usr/man -> /usr/share/man
# (a relic of the /usr/dt layout where the symlink mapped /usr/dt/man into
# /usr/dt/share/man). Under FHS the destination is already /usr/share/man,
# so the symlink is pure pollution at /usr/man and confuses Fedora's
# brp-compress (it crawls into it and bails on permission errors).
rm -f %{buildroot}/usr/man

# Some .dt files embed shell commands inside sh -c '...' single quotes.
# tradcpp doesn't expand macros inside those quotes (it respects shell
# quoting), so CDE_INSTALLATION_TOP and XCOMM survive unsubstituted into
# the installed file. Post-process to fix.
for f in %{buildroot}%{_datadir}/cde/appconfig/types/*/*.dt; do
    [ -e "$f" ] && sed -i \
        -e 's|CDE_INSTALLATION_TOP/bin|%{_bindir}|g' \
        -e 's|CDE_INSTALLATION_TOP/|%{_datadir}/cde/|g' \
        -e 's|CDE_CONFIGURATION_TOP|%{_sysconfdir}/cde|g' \
        -e 's|CDE_LOGFILES_TOP|/var/lib/cde|g' \
        -e 's|XCOMM|#|g' \
        "$f"
done

# Tell the dynamic linker about /usr/lib64 (no-op; placeholder hook).
install -D -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/ld.so.conf.d/cde.conf

# systemd unit (display manager) and PAM file land in their FHS spots.
install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/dtlogin.service
install -D -m 0644 %{SOURCE6} %{buildroot}%{_unitdir}/rpc.cmsd.service
install -D -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pam.d/dtlogin
install -D -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/xsessions/cde.desktop
install -D -m 0644 %{SOURCE5} %{buildroot}%{_docdir}/%{name}/README.Fedora

# Runtime state directories under /var/lib/cde
install -d %{buildroot}/var/lib/cde
install -d %{buildroot}/var/lib/cde/appconfig
install -d %{buildroot}/var/lib/cde/tmp

# /var/spool/calendar must be daemon:daemon mode 3777 (sgid + sticky).
# rpc.cmsd refuses to start if perms are wrong (it tries chown but fails
# as non-root). %attr in %files re-applies the ownership at install time.
install -d -m 3777 %{buildroot}/var/spool/calendar

# Drop libtool .la files (Fedora policy)
find %{buildroot} -name '*.la' -delete

# Rewrite CDE's font aliases to target adobe-{times,helvetica,courier}
# bitmap fonts (which Fedora actually ships, in xorg-x11-fonts-ISO8859-1-*)
# instead of -b&h-lucida-* (proprietary, not available in any Fedora repo).
# Without this, Motif text in dtinfo / dtfile / dtwm renders as empty
# rectangles because every alias target resolves to a missing font.
for f in %{buildroot}%{_sysconfdir}/cde/fontaliases/fonts.alias \
         %{buildroot}%{_datadir}/cde/fontaliases/fonts.alias; do
    [ -e "$f" ] && sed -i \
        -e 's/-b&h-lucidabright-/-adobe-times-/g' \
        -e 's/-b&h-lucidatypewriter-/-adobe-courier-/g' \
        -e 's/-b&h-lucida-/-adobe-helvetica-/g' "$f"
done

%post
/sbin/ldconfig
%systemd_post dtlogin.service rpc.cmsd.service
# Regenerate fonts.dir for both CDE alias directories so the X server
# picks them up. Both dirs are on the X font path via /etc/X11/fontpath.d.
for d in %{_sysconfdir}/cde/fontaliases %{_datadir}/cde/fontaliases; do
    [ -d "$d" ] && mkfontdir "$d" >/dev/null 2>&1 || :
done
# Getting-started reminder (visible during interactive dnf install).
if [ $1 -eq 1 ]; then
cat <<'EOF'

=================================================================
 Common Desktop Environment (CDE) installed.

 1. Make sure rpcbind is running (required for ToolTalk and dtcm):
        sudo systemctl enable --now rpcbind.service

 2. To use dtcm (Calendar Manager), also enable the calendar daemon:
        sudo systemctl enable --now rpc.cmsd.service

 3. To use dtlogin as the system display manager (replaces gdm):
        sudo systemctl disable gdm.service
        sudo systemctl enable  dtlogin.service
        sudo reboot

 4. To start a CDE session from startx instead, drop in ~/.xinitrc:
        exec /etc/cde/Xsession
    and (optionally) copy /etc/cde/config/sys.dtprofile to ~/.dtprofile.

 See /usr/share/doc/cde/README.Fedora for the full layout, font
 dependency notes, and troubleshooting tips.
=================================================================

EOF
fi

%preun
%systemd_preun dtlogin.service rpc.cmsd.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart dtlogin.service rpc.cmsd.service

%post libs
/sbin/ldconfig

%postun libs
/sbin/ldconfig

# -----------------------------------------------------------------------------
%files
%license COPYING
%doc README.md HISTORY CONTRIBUTORS
%doc %{_docdir}/%{name}/README.Fedora
# Binaries, libexec, etc. — FHS standard locations.
# /usr/bin/Xsession is a symlink → /etc/cde/Xsession (which is the
# real file). FHS-idiomatic: matches /etc/gdm/Xsession convention.
%{_bindir}/*
# dtmail needs setgid mail so it can read /var/spool/mail/<user>.
# dtappgather needs setuid root for its per-user app-manager population.
# Upstream's install-exec-hook tries to set these via chgrp/chown but
# fails silently in unprivileged rpm builds, so re-apply the modes here.
%attr(2755, root, mail) %{_bindir}/dtmail
%attr(4755, root, root) %{_bindir}/dtappgather
# Splash-screen content displayed by dthello at session login.
/usr/copyright
# CDE man pages (dt*, tt*, dtinfo, dtdocbook, etc.) — installed by
# cde/doc/<LANG>/man/ when the doc subtree is built.
%{_mandir}/man1/*
%{_mandir}/man3/*
%{_mandir}/man4/*
%{_mandir}/man5/*
%{_mandir}/man6/*
%{_mandir}/man1m/*
%config(noreplace) %{_sysconfdir}/cde/Xsession
%dir %{_libdir}/cde
%{_libdir}/cde/dtdocbook
%dir %{_libdir}/dtksh
%{_libdir}/dtksh/DtFuncs.dtsh
%dir %{_libexecdir}/cde
%{_libexecdir}/cde/dtdocbook
# CDE arch-independent data namespace at /usr/share/cde
%dir %{_datadir}/cde
%{_datadir}/cde/app-defaults
%{_datadir}/cde/appconfig
%{_datadir}/cde/backdrops
%{_datadir}/cde/dtdocbook
%{_datadir}/cde/fontaliases
# infolib is owned by the cde-doc subpackage
%{_datadir}/cde/palettes
# /usr/share/cde/share/{backdrops,palettes}/desc.<LANG> -- description files
# from a separate Makefile; the actual .pm/.bm and .dp data lives under the
# top-level backdrops/ and palettes/ dirs above.
%{_datadir}/cde/share
%dir %{_datadir}/cde/lib
%{_datadir}/cde/lib/nls
%exclude %{_datadir}/cde/app-defaults/de_DE.UTF-8
%exclude %{_datadir}/cde/app-defaults/fr_FR.UTF-8
%exclude %{_datadir}/cde/app-defaults/es_ES.UTF-8
%exclude %{_datadir}/cde/app-defaults/it_IT.UTF-8
%exclude %{_datadir}/cde/app-defaults/ja_JP.UTF-8
%exclude %{_datadir}/cde/appconfig/types/de_DE.UTF-8
%exclude %{_datadir}/cde/appconfig/types/fr_FR.UTF-8
%exclude %{_datadir}/cde/appconfig/types/es_ES.UTF-8
%exclude %{_datadir}/cde/appconfig/types/it_IT.UTF-8
%exclude %{_datadir}/cde/appconfig/types/ja_JP.UTF-8
%exclude %{_datadir}/cde/appconfig/appmanager/de_DE.UTF-8
%exclude %{_datadir}/cde/appconfig/appmanager/fr_FR.UTF-8
%exclude %{_datadir}/cde/appconfig/appmanager/es_ES.UTF-8
%exclude %{_datadir}/cde/appconfig/appmanager/it_IT.UTF-8
%exclude %{_datadir}/cde/appconfig/appmanager/ja_JP.UTF-8
%exclude %{_datadir}/cde/appconfig/icons/ja
%exclude %{_datadir}/cde/lib/nls/msg/de_DE.UTF-8
%exclude %{_datadir}/cde/lib/nls/msg/fr_FR.UTF-8
%exclude %{_datadir}/cde/lib/nls/msg/es_ES.UTF-8
%exclude %{_datadir}/cde/lib/nls/msg/it_IT.UTF-8
%exclude %{_datadir}/cde/lib/nls/msg/ja_JP.UTF-8
# Config under /etc/cde
%dir %{_sysconfdir}/cde
%config(noreplace) %{_sysconfdir}/cde/config
%{_sysconfdir}/cde/fontaliases
%exclude %{_sysconfdir}/cde/config/de_DE.UTF-8
%exclude %{_sysconfdir}/cde/config/fr_FR.UTF-8
%exclude %{_sysconfdir}/cde/config/es_ES.UTF-8
%exclude %{_sysconfdir}/cde/config/it_IT.UTF-8
%exclude %{_sysconfdir}/cde/config/ja_JP.UTF-8
# FHS integration files
%config(noreplace) %{_sysconfdir}/pam.d/dtlogin
%config(noreplace) %{_sysconfdir}/pam.d/dtsession
%{_sysconfdir}/ld.so.conf.d/cde.conf
%{_unitdir}/dtlogin.service
%{_unitdir}/rpc.cmsd.service
%{_datadir}/xsessions/cde.desktop
# Runtime state under /var/lib/cde (replaces /var/dt via --with-cde-state-dir)
%dir /var/lib/cde
%dir /var/lib/cde/appconfig
%dir /var/lib/cde/tmp
%attr(3777, daemon, daemon) %dir /var/spool/calendar

%files libs
%{_libdir}/lib*.so.*
%{_libdir}/lib*.so

%files devel
%{_includedir}/Dt
%{_includedir}/Tt
%{_includedir}/csa
%{_libdir}/lib*.a

%files doc
%{_datadir}/cde/infolib

%files langpack-de
%{_datadir}/cde/app-defaults/de_DE.UTF-8
%{_sysconfdir}/cde/config/de_DE.UTF-8
%{_datadir}/cde/appconfig/types/de_DE.UTF-8
%{_datadir}/cde/appconfig/appmanager/de_DE.UTF-8
%{_datadir}/cde/lib/nls/msg/de_DE.UTF-8
%{_datadir}/cde/share/backdrops/desc.de_DE.UTF-8
%{_datadir}/cde/share/palettes/desc.de_DE.UTF-8

%files langpack-fr
%{_datadir}/cde/app-defaults/fr_FR.UTF-8
%{_sysconfdir}/cde/config/fr_FR.UTF-8
%{_datadir}/cde/appconfig/types/fr_FR.UTF-8
%{_datadir}/cde/appconfig/appmanager/fr_FR.UTF-8
%{_datadir}/cde/lib/nls/msg/fr_FR.UTF-8
%{_datadir}/cde/share/backdrops/desc.fr_FR.UTF-8
%{_datadir}/cde/share/palettes/desc.fr_FR.UTF-8

%files langpack-es
%{_datadir}/cde/app-defaults/es_ES.UTF-8
%{_sysconfdir}/cde/config/es_ES.UTF-8
%{_datadir}/cde/appconfig/types/es_ES.UTF-8
%{_datadir}/cde/appconfig/appmanager/es_ES.UTF-8
%{_datadir}/cde/lib/nls/msg/es_ES.UTF-8
%{_datadir}/cde/share/backdrops/desc.es_ES.UTF-8
%{_datadir}/cde/share/palettes/desc.es_ES.UTF-8

%files langpack-it
%{_datadir}/cde/app-defaults/it_IT.UTF-8
%{_sysconfdir}/cde/config/it_IT.UTF-8
%{_datadir}/cde/appconfig/types/it_IT.UTF-8
%{_datadir}/cde/appconfig/appmanager/it_IT.UTF-8
%{_datadir}/cde/lib/nls/msg/it_IT.UTF-8
%{_datadir}/cde/share/backdrops/desc.it_IT.UTF-8
%{_datadir}/cde/share/palettes/desc.it_IT.UTF-8

%files langpack-ja
%{_datadir}/cde/app-defaults/ja_JP.UTF-8
%{_sysconfdir}/cde/config/ja_JP.UTF-8
%{_datadir}/cde/appconfig/types/ja_JP.UTF-8
%{_datadir}/cde/appconfig/appmanager/ja_JP.UTF-8
%{_datadir}/cde/appconfig/icons/ja
%{_datadir}/cde/lib/nls/msg/ja_JP.UTF-8
%{_datadir}/cde/share/backdrops/desc.ja_JP.UTF-8
%{_datadir}/cde/share/palettes/desc.ja_JP.UTF-8

%changelog
* Fri May 15 2026 Trung Lê <8@tle.id.au> - 2.5.3-1
- Initial Fedora packaging (--prefix=/usr/dt with FHS placement of
  binaries, libraries, headers and man pages under /usr/{bin,lib64,include,share/man}).

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

# Drop the K&R-era strstr() redeclaration in dthelp/htag2 that conflicts
# with glibc's _Generic-based <string.h> declaration.
Patch0:         0001-fproto-drop-strstr-redeclaration.patch
# Add an include/config.h stub that forwards to cde_config.h, so Motif's
# private headers (Xm/DisplayP.h etc.) can resolve <config.h>.
Patch1:         0002-include-config-h-stub-for-motif.patch
# Make CDE_INSTALLATION_TOP / CDE_CONFIGURATION_TOP / CDE_LOGFILES_TOP
# overridable via --with-cde-{config,state,libexec,data}-dir flags.
# Required to put /etc/cde and /var/lib/cde in proper FHS locations.
Patch2:         0003-configure-make-cde-paths-overridable.patch
# Phase 2: convert ~78 raw "/usr/dt/...", "/etc/dt/...", "/var/dt/..." string
# literals in 31 source files to use the CDE_*_TOP macros from Patch2 so the
# packager's --with-cde-* overrides actually flow into compiled binaries.
Patch3:         0004-cleanup-cc-literals-use-cde-macros.patch
# Phase 3: equivalent cleanup for the .src files that go through tradcpp at
# build time (programs/types/*.dt.src, programs/dtlogin/config/*.src, etc.).
Patch4:         0005-cleanup-src-files-use-cde-macros.patch
# Phase 4: convert contrib/ templates (cde.desktop, dtlogin.service, xinetd
# snippets, OS rc scripts, desktop2dt) to autoconf .in files.
Patch5:         0006-contrib-convert-to-autoconf-in-files.patch
# Phase 5: util/check-fhs.sh validation gate.
Patch6:         0007-util-add-check-fhs-validation.patch

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
# CDE keeps /usr/dt as its data namespace; move bin/lib/include/man into FHS in %install.
# PAM dir is forced to /etc/pam.d (configure heuristic only does that for /usr or /usr/local prefix).
# Warning-suppression flags must go through ./configure so that configure's
# own additions (e.g. -I/usr/include/tirpc for libtirpc) are preserved in the
# Makefiles. Overriding CFLAGS/CXXFLAGS at make-time would clobber them.
export CFLAGS="%{optflags} -Wno-error -Wno-format-truncation -Wno-write-strings -Wno-unused-result -fno-strict-aliasing -fcommon"
export CXXFLAGS="$CFLAGS"
# The bundled ksh93 has text relocations on ppc64le that conflict with
# Fedora's default `-Wl,-z,now`. Allow them with `-z,notext` (matches what
# the Fedora ksh package itself does).
export LDFLAGS="%{?build_ldflags} -Wl,-z,notext"
# Note: --prefix=/usr/dt sets CDE_INSTALLATION_TOP to /usr/dt (CDE's data
# namespace), but %configure also passes --bindir=/usr/bin, --libdir=/usr/lib64,
# --includedir=/usr/include, --mandir=/usr/share/man, etc. CDE's install hooks
# detect bindir != $prefix/bin and automatically create the /usr/dt/bin ->
# /usr/bin compat symlink so the ~247 hardcoded /usr/dt/bin/<...> paths still
# resolve. Same for include/man.
%configure \
    --prefix=/usr/dt \
    --sysconfdir=/etc \
    --localstatedir=/var \
    --with-pam-dir=/etc/pam.d \
    --with-cde-data-dir=/usr/dt \
    --with-cde-config-dir=/etc/dt \
    --with-cde-state-dir=/var/dt \
    --with-cde-libexec-dir=/usr/bin \
    --enable-german \
    --enable-french \
    --enable-spanish \
    --enable-italian \
    --enable-japanese \
    --enable-docs

%make_build

%install
%make_install

# CDE's own install hook creates a /usr/dt/bin -> /usr/bin compat symlink
# (because $bindir != $prefix/bin); same idea for include and man via
# install-data-hook. No manual relocation needed here.

# Drop the placeholder ld.so.conf.d entry (libs are in default /usr/lib64).
install -D -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/ld.so.conf.d/cde.conf

# systemd unit (display manager)
install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/dtlogin.service

# PAM configuration for dtlogin
install -D -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pam.d/dtlogin

# X session entry (so gdm/sddm/lightdm offer "CDE" at login)
install -D -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/xsessions/cde.desktop

# README explaining the FHS layout
install -D -m 0644 %{SOURCE5} %{buildroot}%{_docdir}/%{name}/README.Fedora

# /var/dt — runtime state directory
install -d %{buildroot}/var/dt
install -d %{buildroot}/var/dt/appconfig
install -d %{buildroot}/var/dt/tmp

# Drop libtool .la files (Fedora policy)
find %{buildroot} -name '*.la' -delete

%post
/sbin/ldconfig
%systemd_post dtlogin.service

%preun
%systemd_preun dtlogin.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart dtlogin.service

%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

# -----------------------------------------------------------------------------
%files
%license COPYING
%doc README.md HISTORY CONTRIBUTORS
%doc %{_docdir}/%{name}/README.Fedora
# Binaries (real, in /usr/bin)
%{_bindir}/*
# Compatibility symlink CDE itself creates: /usr/dt/bin -> /usr/bin
/usr/dt/bin
# CDE data namespace
%dir /usr/dt
/usr/dt/CONTRIBUTORS
/usr/dt/COPYING
/usr/dt/HISTORY
/usr/dt/README.md
/usr/dt/copyright
%dir /usr/dt/app-defaults
/usr/dt/app-defaults/C
/usr/dt/app-defaults/en_US.UTF-8
%dir /usr/dt/config
%config(noreplace) /usr/dt/config/C
/usr/dt/config/en_US.UTF-8
%config(noreplace) /usr/dt/config/Xaccess
%config(noreplace) /usr/dt/config/Xconfig
%config(noreplace) /usr/dt/config/Xfailsafe
%config(noreplace) /usr/dt/config/Xreset
%config(noreplace) /usr/dt/config/Xservers
/usr/dt/config/Xsession.d
%config(noreplace) /usr/dt/config/Xsetup
%config(noreplace) /usr/dt/config/Xstartup
%config(noreplace) /usr/dt/config/sys.dtprofile
/usr/dt/config/dtspcdenv
/usr/dt/config/dtterm.ti
/usr/dt/config/ims
/usr/dt/config/svc
%dir /usr/dt/appconfig
%dir /usr/dt/appconfig/types
/usr/dt/appconfig/types/C
/usr/dt/appconfig/types/en_US.UTF-8
/usr/dt/appconfig/tttypes
%dir /usr/dt/appconfig/icons
/usr/dt/appconfig/icons/C
%dir /usr/dt/appconfig/appmanager
/usr/dt/appconfig/appmanager/C
/usr/dt/appconfig/appmanager/en_US.UTF-8
%dir /usr/dt/share
%dir /usr/dt/share/backdrops
/usr/dt/share/backdrops/desc.C
/usr/dt/share/backdrops/desc.en_US.UTF-8
/usr/dt/share/backdrops/*.bm
/usr/dt/share/backdrops/*.pm
%dir /usr/dt/share/palettes
/usr/dt/share/palettes/desc.C
/usr/dt/share/palettes/desc.en_US.UTF-8
/usr/dt/share/palettes/*.dp
/usr/dt/backdrops
/usr/dt/palettes
%dir /usr/dt/lib
%dir /usr/dt/lib/nls
%dir /usr/dt/lib/nls/msg
/usr/dt/lib/nls/msg/C
/usr/dt/lib/nls/msg/en_US.UTF-8
# Auxiliary install dirs
%dir %{_libdir}/cde
%{_libdir}/cde/dtdocbook
%dir %{_libdir}/dtksh
%{_libdir}/dtksh/DtFuncs.dtsh
%dir %{_libexecdir}/cde
%{_libexecdir}/cde/dtdocbook
%dir %{_datadir}/cde
%{_datadir}/cde/dtdocbook
%{_datadir}/cde/fontaliases
%dir %{_sysconfdir}/cde
%{_sysconfdir}/cde/fontaliases
# Config + integration files we install
%config(noreplace) %{_sysconfdir}/pam.d/dtlogin
%config(noreplace) %{_sysconfdir}/pam.d/dtsession
%{_sysconfdir}/ld.so.conf.d/cde.conf
%{_unitdir}/dtlogin.service
%{_datadir}/xsessions/cde.desktop
# Variable state
%dir /var/dt
%dir /var/dt/appconfig
%dir /var/dt/tmp
%dir /var/spool/calendar

%files libs
%{_libdir}/lib*.so.*
%{_libdir}/lib*.so
# Move /usr/dt/CONTRIBUTORS etc. into main pkg (already listed there) so libs
# stays purely the .so* files.

%files devel
%{_includedir}/Dt
%{_includedir}/Tt
%{_includedir}/csa
%{_libdir}/lib*.a

%files doc
/usr/dt/infolib

%files langpack-de
/usr/dt/app-defaults/de_DE.UTF-8
/usr/dt/config/de_DE.UTF-8
/usr/dt/appconfig/types/de_DE.UTF-8
/usr/dt/appconfig/appmanager/de_DE.UTF-8
/usr/dt/lib/nls/msg/de_DE.UTF-8
/usr/dt/share/backdrops/desc.de_DE.UTF-8
/usr/dt/share/palettes/desc.de_DE.UTF-8

%files langpack-fr
/usr/dt/app-defaults/fr_FR.UTF-8
/usr/dt/config/fr_FR.UTF-8
/usr/dt/appconfig/types/fr_FR.UTF-8
/usr/dt/appconfig/appmanager/fr_FR.UTF-8
/usr/dt/lib/nls/msg/fr_FR.UTF-8
/usr/dt/share/backdrops/desc.fr_FR.UTF-8
/usr/dt/share/palettes/desc.fr_FR.UTF-8

%files langpack-es
/usr/dt/app-defaults/es_ES.UTF-8
/usr/dt/config/es_ES.UTF-8
/usr/dt/appconfig/types/es_ES.UTF-8
/usr/dt/appconfig/appmanager/es_ES.UTF-8
/usr/dt/lib/nls/msg/es_ES.UTF-8
/usr/dt/share/backdrops/desc.es_ES.UTF-8
/usr/dt/share/palettes/desc.es_ES.UTF-8

%files langpack-it
/usr/dt/app-defaults/it_IT.UTF-8
/usr/dt/config/it_IT.UTF-8
/usr/dt/appconfig/types/it_IT.UTF-8
/usr/dt/appconfig/appmanager/it_IT.UTF-8
/usr/dt/lib/nls/msg/it_IT.UTF-8
/usr/dt/share/backdrops/desc.it_IT.UTF-8
/usr/dt/share/palettes/desc.it_IT.UTF-8

%files langpack-ja
/usr/dt/app-defaults/ja_JP.UTF-8
/usr/dt/config/ja_JP.UTF-8
/usr/dt/appconfig/types/ja_JP.UTF-8
/usr/dt/appconfig/appmanager/ja_JP.UTF-8
/usr/dt/appconfig/icons/ja
/usr/dt/lib/nls/msg/ja_JP.UTF-8
/usr/dt/share/backdrops/desc.ja_JP.UTF-8
/usr/dt/share/palettes/desc.ja_JP.UTF-8

%changelog
* Fri May 15 2026 Trung Le <trung.le@ruby-journal.com> - 2.5.3-1
- Initial Fedora packaging (--prefix=/usr/dt with FHS placement of
  binaries, libraries, headers and man pages under /usr/{bin,lib64,include,share/man}).

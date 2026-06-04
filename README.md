cde-rpm — Fedora packaging for the Common Desktop Environment
==============================================================

This repo holds the RPM spec, helper sources, patches, and a build
driver for packaging the Common Desktop Environment (CDE) on Fedora.
The upstream source tree lives separately at
https://sourceforge.net/projects/cdesktopenv/ (or the git mirror).

Layout
------

    cde.spec                        # main RPM spec (8 subpackages)
    cde.pam                         # /etc/pam.d/dtlogin
    dtlogin.service                 # systemd unit (display-manager.service alias)
    rpc.cmsd.service                # systemd unit for the Calendar Manager RPC daemon
    cde.desktop                     # /usr/share/xsessions/ entry
    ld.so.conf-cde.conf             # placeholder ld.so.conf.d hook
    README.Fedora                   # installed in the doc subpackage
    0002-include-config-h-stub-for-motif.patch
    0003-configure-make-cde-paths-overridable.patch
    0004-cleanup-cc-literals-use-cde-macros.patch
    0005-cleanup-src-files-use-cde-macros.patch
    0006-contrib-convert-to-autoconf-in-files.patch
    0007-util-add-check-fhs-validation.patch
    0008-split-data-top-and-finish-dt-conversion.patch
    0010-fhs-finish-dtinfo-and-data-dirs.patch
    0011-tttypes-fhs-dtinfo-ptype-paths.patch
    0012-fhs-followup-makefile-defines.patch
    0013-appmgr-make-action-files-executable.patch
    0014-help-hf-bitmap-paths.patch
    build-srpm.sh                   # SRPM/RPM build driver

Subpackages produced
--------------------

    cde                  -- session, dtlogin, dtwm, all dt* programs
    cde-libs             -- shared libraries (DtSvc, DtWidget, DtHelp,
                            DtPrint, DtTerm, DtMrm, DtMmdb, DtSearch,
                            DtXinerama, ToolTalk, CSA)
    cde-devel            -- headers + static libraries
    cde-doc              -- dtinfo infolib (not noarch -- ships dtinfo_start)
    cde-langpack-{de,fr,es,it,ja}
                         -- per-locale data (noarch)

Filesystem layout
-----------------

The package follows FHS throughout — there is no `/usr/dt` namespace
anymore. CDE's content is split across the standard Fedora locations
plus a small set of CDE-owned subdirs under `/usr/share/cde`,
`/etc/cde`, `/var/lib/cde`, and `/usr/libexec/cde`:

    /usr/bin/dt*                    binaries
    /usr/bin/Xsession               symlink -> /etc/cde/Xsession
    /usr/lib64/libDt*.so*           shared libraries
    /usr/lib64/libtt*.so*           ToolTalk libraries
    /usr/lib64/{cde,dtksh}/         CDE-internal helpers
    /usr/libexec/cde/               CDE-internal libexec helpers
    /usr/include/{Dt,Tt,csa}/       development headers
    /usr/share/man/man{1,3,4,5,6}/  manual pages
    /usr/share/cde/                 arch-independent data
        app-defaults/               X resource defaults per locale
        appconfig/                  types, icons, help, appmanager
        backdrops/, palettes/       desktop visuals
        infolib/                    dtinfo content
        lib/nls/                    X/Open NLS message catalogues
        fontaliases/                CDE -> X11 font alias table
    /etc/cde/
        Xsession                    per-login bootstrap (the real file)
        config/                     Xsession.d, dtlogin scripts, sys.dtprofile
        fontaliases/                same alias table, different fontpath entry
    /etc/pam.d/{dtlogin,dtsession}  PAM configuration
    /var/lib/cde/                   runtime state (replaces /var/dt)
    /var/spool/calendar             rpc.cmsd data, mode 3777 daemon:daemon
    /usr/lib/systemd/system/{dtlogin,rpc.cmsd}.service
    /usr/share/xsessions/cde.desktop

The FHS migration is driven by Patches 0003–0008/0010/0011 — the
upstream source originally hardcodes `/usr/dt`, `/etc/dt`, and
`/var/dt` throughout. See README.Fedora for the user-facing summary.

Building
--------

You need a checkout of the CDE source tree separately:

    git clone https://github.com/.../cdesktopenv-code   # or SF mirror

Then from this repo:

    ./build-srpm.sh --source-dir /path/to/cdesktopenv-code/cde \
                    --installdeps --rpm

Options:
    --source-dir DIR   path to cdesktopenv-code/cde (required)
    --installdeps      run `sudo dnf builddep` first
    --rpm              build binary RPMs (default: SRPM only)

The script tries `make dist` first; if that fails (or the source tree
isn't autoreconf'd), it falls back to `git archive HEAD | xz` to produce
the source tarball.

Starting a CDE session
----------------------

There are two ways to log into CDE on Fedora. Before either, make sure
rpcbind is running (ToolTalk and the calendar daemon need it):

    sudo systemctl enable --now rpcbind.service
    sudo systemctl enable --now rpc.cmsd.service   # only if you use dtcm

### Option 1: `startx` from a TTY (no display manager change needed)

Drop in a `~/.xinitrc` that hands control to CDE's session bootstrap:

    cat > ~/.xinitrc <<'EOF'
    #!/bin/sh
    exec /etc/cde/Xsession
    EOF
    chmod +x ~/.xinitrc

If you don't already have one, copy CDE's user profile template:

    cp /etc/cde/config/sys.dtprofile ~/.dtprofile

Then from a text console:

    startx

`Xsession` performs the same bootstrap dtlogin would (sets `LANG`,
sources `~/.dtprofile`, applies X resources, starts ToolTalk) and then
execs `dtsession`, the actual session manager. Errors land in
`~/.xsession-errors` and `/var/lib/cde/Xerrors`.

### Option 2: `dtlogin` as the system display manager

This replaces gdm/sddm with CDE's own login screen. Reboot required.

    systemctl status dtlogin                 # currently disabled
    sudo systemctl disable gdm.service       # or sddm/lightdm
    sudo systemctl enable dtlogin.service
    sudo reboot

The package installs `/usr/lib/systemd/system/dtlogin.service` aliased
as `display-manager.service`, so only one display manager can be
enabled at a time. Logs go to `/var/lib/cde/`.

To go back to gdm:

    sudo systemctl disable dtlogin.service
    sudo systemctl enable gdm.service
    sudo reboot

Patches
-------

All fourteen patches apply on top of upstream master. The first two are
narrow build fixes; the rest implement and finish the FHS migration
plus a handful of first-boot fixups.

  * **0002** -- add `include/config.h` that forwards to
    `cde_config.h`. Fedora's motif-devel ships private headers
    (`Xm/DisplayP.h` etc.) that do `#ifdef HAVE_CONFIG_H #include
    <config.h>`; CDE compiles with `-DHAVE_CONFIG_H` so Motif's
    include needs a resolvable `config.h` on the search path.
  * **0003** -- make `CDE_INSTALLATION_TOP` / `CDE_CONFIGURATION_TOP`
    / `CDE_LOGFILES_TOP` / `CDE_DATA_TOP` / `CDE_LIBEXEC_TOP`
    overridable via `--with-cde-{data,config,state,libexec}-dir`
    configure flags.
  * **0004** -- convert raw `"/usr/dt/..."`, `"/etc/dt/..."`,
    `"/var/dt/..."` string literals in C/C++ source to the
    `CDE_*_TOP` macros plumbed through by Patch0003.
  * **0005** -- equivalent cleanup for the `.src` files that go
    through `tradcpp` at build time.
  * **0006** -- convert the `contrib/` templates to autoconf `.in`
    files so they pick up the same substitutions.
  * **0007** -- add `util/check-fhs.sh`, a validation gate that
    greps the build tree for stray hardcoded `/usr/dt|/etc/dt|/var/dt`
    references.
  * **0008** -- split `CDE_DATA_TOP` from `CDE_INSTALLATION_TOP`
    (arch-independent data goes to `/usr/share/cde`, binaries stay
    under `/usr`) and rename `dt{mail,cm}.dt` to `.src` so they get
    `tradcpp`-substituted.
  * **0010** -- finish the FHS migration for dtinfo and the data-only
    directories: fix the second `InfoLibSearchPath` copy of `/usr/dt`
    missed by Patch0008, and drop the `/share/` infix plus legacy
    compat symlinks from backdrops/palettes so the install layout
    matches the compiled-in `DT_BACKDROPSEARCHPATH` /
    `DTINFOLIBSEARCHPATH` probes.
  * **0011** -- rewrite the dtinfo ToolTalk ptype start-strings, which
    bake `/usr/dt` paths into the compiled `types.xdr` at build time
    and aren't reachable from configure flags. Without this,
    `DtInfo_LoadInfoLib` returns `TT_ERR_PTYPE_START` and dtinfo
    never opens from any desktop launch path.
  * **0012** -- plug two `Makefile.am` misses surfaced by a sweep with
    `util/check-fhs.sh`: `lib/DtSvc/Makefile.am` was missing
    `-DCDE_LOGFILES_TOP=` so `DtUtil2/MsgLog.c` and `DtEncap/nls.c`
    fell through to their `"/var/dt/tmp"` fallbacks; and
    `programs/dtspcd/Makefile.am` set
    `-DCDE_CONFIGURATION_TOP="${prefix}"` (a pre-existing upstream
    typo) which pinned dtspcd's SPC config dir to `PREFIX/config`
    instead of honoring `--with-cde-config-dir`.
  * **0013** -- make Application Manager action files executable. The
    upstream build copies `programs/types/action` (mode 0644) into
    each appmgr entry (e.g. `Desktop_Apps/Dtcalc`), and dtfile only
    treats the file as an action if the execute bit is set; without
    this, double-click opens it in dtpad instead of launching the
    action. Adds `chmod +x` to the build rule in
    `programs/localized/templates/appmgr.am`, and prepends a
    `#!/bin/sh` shebang to `programs/types/action` so Fedora's
    `brp-mangle-shebangs` doesn't strip the exec bit back off during
    rpm packaging.
  * **0014** -- route the Help Manager `.hf` family `*.bitmap:` paths
    through `@CDE_DATA_TOP@` instead of `@prefix@`. With `--prefix=/usr`
    the latter expands to `/usr/appconfig/help/.../cdelogo.pm` (which
    doesn't exist), so dthelpview shows "Missing Graphics" beside the
    "Common Desktop Environment" and "Overview and Basic Desktop
    Skills" section headers.

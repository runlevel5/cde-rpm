cde-rpm — Fedora packaging for the Common Desktop Environment
==============================================================

This repo holds the RPM spec, helper sources, patches, and a build
driver for packaging the Common Desktop Environment (CDE) on Fedora.
The upstream source tree lives separately at
https://sourceforge.net/projects/cdesktopenv/ (or the git mirror).

Layout
------

    cde.spec                        # main RPM spec (7 subpackages)
    cde.pam                         # /etc/pam.d/dtlogin
    dtlogin.service                 # systemd unit (display-manager.service alias)
    cde.desktop                     # /usr/share/xsessions/ entry
    ld.so.conf-cde.conf             # placeholder ld.so.conf.d hook
    README.Fedora                   # installed in the doc subpackage
    0001-fproto-drop-strstr-redeclaration.patch
    0002-include-config-h-stub-for-motif.patch
    build-srpm.sh                   # SRPM/RPM build driver

Subpackages produced
--------------------

    cde                  -- session, dtlogin, dtwm, all dt* programs
    cde-libs             -- 11 shared libraries (DtSvc, DtWidget, ...)
    cde-devel            -- headers + static libraries
    cde-doc              -- dtinfo infolib (not noarch -- ships dtinfo_start)
    cde-langpack-{de,fr,es,it,ja}
                         -- per-locale data (noarch)

Filesystem layout
-----------------

The package follows FHS for the parts users and the toolchain interact
with directly: binaries in /usr/bin, libraries in /usr/lib64, headers in
/usr/include, man pages in /usr/share/man, systemd unit in
/usr/lib/systemd/system, PAM config in /etc/pam.d, xsession entry in
/usr/share/xsessions.

CDE's own runtime data namespace stays under /usr/dt/ (palettes,
backdrops, types, app-defaults, config, infolib, lib/nls). Around 247
source files contain hardcoded /usr/dt/<...> paths; relocating that
content out from /usr/dt would require patching all of them. The
packaging compromise: install bin/include into FHS locations and let
CDE's own install hooks create /usr/dt/bin -> /usr/bin and
/usr/dt/include -> /usr/include compatibility symlinks so the hardcoded
references continue to resolve. See README.Fedora for details.

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

There are two ways to log into CDE on Fedora.

### Option 1: `startx` from a TTY (no display manager change needed)

Drop in a `~/.xinitrc` that hands control to CDE's session bootstrap:

    cat > ~/.xinitrc <<'EOF'
    #!/bin/sh
    # Launch the Common Desktop Environment session via CDE Xsession bootstrap.
    exec /usr/bin/Xsession
    EOF
    chmod +x ~/.xinitrc

If you don't already have one, copy CDE's user profile template:

    cp /usr/dt/config/sys.dtprofile ~/.dtprofile

Then from a text console:

    startx

`Xsession` performs the same bootstrap dtlogin would (sets `LANG`,
sources `~/.dtprofile`, applies X resources, starts ToolTalk) and then
execs `dtsession`, the actual session manager. Errors land in
`~/.xsession-errors` and `/var/dt/Xerrors`.

### Option 2: `dtlogin` as the system display manager

This replaces gdm/sddm with CDE's own login screen. Reboot required.

    systemctl status dtlogin                 # currently disabled
    sudo systemctl disable gdm.service       # or sddm/lightdm
    sudo systemctl enable dtlogin.service
    sudo reboot

The package installs `/usr/lib/systemd/system/dtlogin.service` aliased
as `display-manager.service`, so only one display manager can be
enabled at a time. Logs go to `/var/dt/`.

To go back to gdm:

    sudo systemctl disable dtlogin.service
    sudo systemctl enable gdm.service
    sudo reboot

Patches
-------

Both patches are needed against modern Fedora and apply on top of
upstream master:

  * **0001** -- removes a K&R-era redeclaration of `strstr()` in
    `programs/dthelp/parser/pass2/htag2/fproto.h`. Glibc declares
    `strstr` via `_Generic` in `<string.h>` and the redeclaration
    breaks parsing.
  * **0002** -- adds `include/config.h` that forwards to
    `cde_config.h`. Fedora's motif-devel ships private headers
    (`Xm/DisplayP.h` etc.) that do `#ifdef HAVE_CONFIG_H #include
    <config.h>`; CDE compiles with `-DHAVE_CONFIG_H` so Motif's
    include needs a resolvable `config.h` on the search path.

Both fixes are good upstream candidates; once merged upstream the
patches can be dropped.

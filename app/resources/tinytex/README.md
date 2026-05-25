# TinyTeX bundle

Drop the platform-appropriate TinyTeX distribution into this directory; it is
intentionally git-ignored. The PDF generator (Step 5, `app/tex/pdfgen.py`) will
shell out to `xelatex` from here in production builds.

| platform | bundle layout                                                    |
| -------- | ---------------------------------------------------------------- |
| macOS    | `mac/bin/x86_64-darwin/xelatex` (or `aarch64-darwin/`)           |
| Windows  | `win/bin/windows/xelatex.exe`                                    |
| Linux    | not bundled — runtime falls back to system `xelatex` on `PATH`.  |

Get TinyTeX from <https://yihui.org/tinytex/>. Install with the project's required
packages via `tlmgr install amsmath amsfonts amssymb caption graphicx fancyhdr
geometry enumitem circuitikz chemfig pgfplots mathtools stmaryrd ulem` (the spec's
fixed preamble; see §6.2 of `Files/AMPLIFY_BUILD_SPEC (3).md`).

This directory is gitignored except for this README — bundles are large and
platform-specific; ship them with installers, not in version control.

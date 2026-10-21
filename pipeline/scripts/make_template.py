"""Generate templates/app_template.tex from the app's real preamble.

The template is a faithful copy of what app/tex/pdfgen.py assembles: the fixed
preamble from app/tex/preamble.py, the fancyhdr block, and the display-style
setting, with two slots: <<IMAGE_PATH>> (the app's teximages folder) and
<<CONTENT>> (where a question's solution block is placed).

Re-run this whenever app/tex/preamble.py or app/tex/pdfgen.py changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_DIR, TEMPLATES_DIR, write_text  # noqa: E402

sys.path.insert(0, str(REPO_DIR))
from app.tex.preamble import PREAMBLE_TEMPLATE  # noqa: E402

FANCY = "\n".join(
    [
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        r"\fancyhead[L]{Pipeline check}",
        r"\fancyhead[R]{<<DATE>>}",
        r"\fancyfoot[C]{\thepage}",
        r"\renewcommand{\headrulewidth}{0.4pt}",
    ]
)


def main() -> None:
    import datetime

    pre = PREAMBLE_TEMPLATE.replace("<image_path>", "<<IMAGE_PATH>>")
    doc = (
        f"{pre}{FANCY}\n"
        "\\begin{document}\n"
        "\\everymath{\\displaystyle}\n"
        "<<CONTENT>>\n"
        "\\end{document}\n"
    ).replace("<<DATE>>", datetime.date.today().strftime("%d-%m-%Y"))
    out = TEMPLATES_DIR / "app_template.tex"
    write_text(out, doc)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

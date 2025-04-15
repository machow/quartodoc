import re
import tempfile
import subprocess
from pathlib import Path
from quartodoc.__main__ import build

p = Path("docs/get-started/overview.qmd")
overview = p.read_text()

indx = overview.index("<!-- Starter Template -->")
yml_blurb = overview[indx:]

match = re.search(r"```yaml\s*(.*?)```", yml_blurb, re.DOTALL)
if match is None:
    raise Exception()

template = match.group(1)

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    # Write the template to a file
    p_quarto = tmpdir / "_quarto.yml"
    p_quarto.write_text(template)

    try:
        build(["--config", str(p_quarto), "--filter", "quartodoc"])
    except SystemExit as e:
        if e.code != 0:
            raise Exception() from e
    subprocess.run(["quarto", "render", str(p_quarto.parent)])

    print("SITE RENDERED SUCCESSFULLY")

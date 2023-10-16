import pytest

from pathlib import Path
from quartodoc.__main__ import build


def test_cli_build_config_path(tmpdir):
    p_tmp = Path(tmpdir)
    p_config = Path(p_tmp, "_quarto.yml")
    p_config.write_text(
        """
        quartodoc:
          package: quartodoc
          sections:
            - contents:
              - get_object
    """
    )

    # calling click CLI objects directly is super cumbersome ---
    try:
        build(["--config", str(p_config)])
    except SystemExit:
        pass

    res = list(p_tmp.glob("reference/*"))

    assert len(res) == 2
    assert "get_object.qmd" in [p.name for p in res]

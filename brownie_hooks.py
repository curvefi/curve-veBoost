from pathlib import Path

from brownie._config import CONFIG
from jinja2 import Template


def brownie_load_source(path: Path, source: str) -> str:
    if path.stem != "VotingEscrowDelegation":
        return source

    template = Template(source, line_statement_prefix="#@", trim_blocks=True, lstrip_blocks=True)
    return template.render(mode=CONFIG.mode)

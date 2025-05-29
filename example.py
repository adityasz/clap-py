from pathlib import Path
from typing import Optional

import clap
from clap import flag, option, ColorChoice


@clap.arguments
class Cli(clap.Parser):
    x: int
    """hello"""
    y: Optional[int]
    y1: bool = False
    y2 = flag("-y")
    y2 = flag("-y", count=True)
    o0: int = option("-v", required=True)
    o2 = option(default="str")
    o3 = option(const="str")
    o4 = option(Path, default="foo", action="store")
    o5 = option(tuple[Path, Path], default="foo")
    color = option(ColorChoice, "-v")

args = Cli.parse_args()

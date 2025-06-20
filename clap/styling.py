import sys
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import Optional, Self


class ColorChoice(Enum):
    """Represents the color preferences for help output."""
    Auto = auto()
    Always = auto()
    Never = auto()


class AnsiColor(IntEnum):
    Black = 30
    Red = 31
    Green = 32
    Yellow = 33
    Blue = 34
    Magenta = 35
    Cyan = 36
    White = 37
    BrightBlack = 90
    BrightRed = 91
    BrightGreen = 92
    BrightYellow = 93
    BrightBlue = 94
    BrightMagenta = 95
    BrightCyan = 96
    BrightWhite = 97


@dataclass(slots=True)
class Style:
    color: Optional[AnsiColor] = None
    is_bold: bool = False
    is_dim: bool = False
    is_italic: bool = False
    is_underline: bool = False

    def bold(self) -> "Style":
        self.is_bold = True
        return self

    def dim(self) -> "Style":
        self.is_dim = True
        return self

    def italic(self) -> "Style":
        self.is_italic = True
        return self

    def underline(self) -> "Style":
        self.is_underline = True
        return self

    def fg_color(self, color: Optional[AnsiColor] = None) -> "Style":
        self.color = color
        return self

    def __str__(self) -> str:
        codes = []
        if self.color is not None:
            codes.append(str(self.color.value))
        if self.is_bold:
            codes.append("1")
        if self.is_dim:
            codes.append("2")
        if self.is_italic:
            codes.append("3")
        if self.is_underline:
            codes.append("4")
        return f"\033[{';'.join(codes)}m" if codes else ""


class Styles:
    def __init__(self):
        self.header_style = Style()
        self.literal_style = Style()
        self.usage_style = Style()
        self.placeholder_style = Style()

    @classmethod
    def styled(cls) -> "Styles":
        return (Styles().header(Style().bold().underline())
                    .literal(Style().bold())
                    .usage(Style().bold().underline())
                    .placeholder(Style()))

    def header(self, style: Style) -> Self:
        self.header_style = style
        return self

    def literal(self, style: Style) -> Self:
        self.literal_style = style
        return self

    def usage(self, style: Style) -> Self:
        self.usage_style = style
        return self

    def placeholder(self, style: Style) -> Self:
        self.placeholder_style = style
        return self


def determine_color_usage(color_choice: ColorChoice) -> bool:
    match color_choice:
        case ColorChoice.Never:
            return False
        case ColorChoice.Always:
            return True
        case ColorChoice.Auto:
            return sys.stdout.isatty()

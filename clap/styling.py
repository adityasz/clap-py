import sys
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import Optional


class ColorChoice(Enum):
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

    def bold(self) -> "ColorStyle":
        return ColorStyle(self, is_bold=True)

    def dim(self) -> "ColorStyle":
        return ColorStyle(self, is_dim=True)

    def italic(self) -> "ColorStyle":
        return ColorStyle(self, is_italic=True)

    def underline(self) -> "ColorStyle":
        return ColorStyle(self, is_underline=True)


@dataclass
class ColorStyle:
    color: Optional[AnsiColor] = None
    is_bold: bool = False
    is_dim: bool = False
    is_italic: bool = False
    is_underline: bool = False

    def bold(self) -> "ColorStyle":
        return ColorStyle(
            self.color,
            is_bold=True,
            is_dim=self.is_dim,
            is_italic=self.is_italic,
            is_underline=self.is_underline,
        )

    def dim(self) -> "ColorStyle":
        return ColorStyle(
            self.color,
            is_bold=self.is_bold,
            is_dim=True,
            is_italic=self.is_italic,
            is_underline=self.is_underline,
        )

    def italic(self) -> "ColorStyle":
        return ColorStyle(
            self.color,
            is_bold=self.is_bold,
            is_dim=self.is_dim,
            is_italic=True,
            is_underline=self.is_underline,
        )

    def underline(self) -> "ColorStyle":
        return ColorStyle(
            self.color,
            is_bold=self.is_bold,
            is_dim=self.is_dim,
            is_italic=self.is_italic,
            is_underline=True,
        )

    def to_ansi(self) -> str:
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


@dataclass
class HelpStyle:
    header_style: Optional[ColorStyle] = None
    option_style: Optional[ColorStyle] = None


def determine_color_usage(color_choice: ColorChoice) -> bool:
    match color_choice:
        case ColorChoice.Never:
            return False
        case ColorChoice.Always:
            return True
        case ColorChoice.Auto:
            return sys.stdout.isatty()

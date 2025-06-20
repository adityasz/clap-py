import sys
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import Optional, Self


class ColorChoice(Enum):
    """Represents the color preferences for help output."""
    Auto = auto()
    """Enables colored output only when the output is going to a terminal or TTY.

    Example:
    ```python
    import clap
    from clap import ColorChoice

    @clap.command(color=ColorChoice.Auto)
    class Cli:
        ...
    ```
    """
    Always = auto()
    """Enables colored output regardless of whether or not the output is going to a terminal/TTY.

    Example:
    ```python
    import clap
    from clap import ColorChoice

    @clap.command(color=ColorChoice.Always)
    class Cli:
        ...
    ```
    """
    Never = auto()
    """Disables colored output no matter if the output is going to a terminal/TTY, or not.

    Example:
    ```python
    import clap
    from clap import ColorChoice

    @clap.command(color=ColorChoice.Never)
    class Cli:
        ...
    ```
    """


class AnsiColor(IntEnum):
    """Available 4-bit ANSI color palette codes.

    The user’s terminal defines the meaning of the each palette code.
    """
    Black = 30
    """Black: #0 (foreground code `30`, background code `40`)."""
    Red = 31
    """Red: #1 (foreground code `31`, background code `41`)."""
    Green = 32
    """Green: #2 (foreground code `32`, background code `42`)."""
    Yellow = 33
    """Yellow: #3 (foreground code `33`, background code `43`)."""
    Blue = 34
    """Blue: #4 (foreground code `34`, background code `44`)."""
    Magenta = 35
    """Magenta: #5 (foreground code `35`, background code `45`)."""
    Cyan = 36
    """Cyan: #6 (foreground code `36`, background code `46`)."""
    White = 37
    """White: #7 (foreground code `37`, background code `47`)."""
    BrightBlack = 90
    """Bright black: #0 (foreground code `90`, background code `100`)."""
    BrightRed = 91
    """Bright red: #1 (foreground code `91`, background code `101`)."""
    BrightGreen = 92
    """Bright green: #2 (foreground code `92`, background code `102`)."""
    BrightYellow = 93
    """Bright yellow: #3 (foreground code `93`, background code `103`)."""
    BrightBlue = 94
    """Bright blue: #4 (foreground code `94`, background code `104`)."""
    BrightMagenta = 95
    """Bright magenta: #5 (foreground code `95`, background code `105`)."""
    BrightCyan = 96
    """Bright cyan: #6 (foreground code `96`, background code `106`)."""
    BrightWhite = 97
    """Bright white: #7 (foreground code `97`, background code `107`)."""


@dataclass(slots=True)
class Style:
    """ANSI Text styling.

    You can print a Style to render the corresponding ANSI code. Using the
    alternate flag `#` will render the ANSI reset code, if needed. Together,
    this makes it convenient to render styles using inline format arguments.

    Example:

    ```python
    style = Style().bold()
    value = 42
    print(f"{style}value{style:#}")
    ```
    """
    color: Optional[AnsiColor] = None
    is_bold: bool = False
    is_dimmed: bool = False
    is_italic: bool = False
    is_underline: bool = False

    def bold(self) -> "Style":
        """Apply `bold` effect."""
        self.is_bold = True
        return self

    def dimmed(self) -> "Style":
        """Apply `dimmed` effect."""
        self.is_dimmed = True
        return self

    def italic(self) -> "Style":
        """Apply `italic` effect."""
        self.is_italic = True
        return self

    def underline(self) -> "Style":
        """Apply `underline` effect."""
        self.is_underline = True
        return self

    def fg_color(self, color: Optional[AnsiColor] = None) -> "Style":
        """Set foreground color."""
        self.color = color
        return self

    def __str__(self) -> str:
        codes = []
        if self.color is not None:
            codes.append(str(self.color.value))
        if self.is_bold:
            codes.append("1")
        if self.is_dimmed:
            codes.append("2")
        if self.is_italic:
            codes.append("3")
        if self.is_underline:
            codes.append("4")
        return f"\033[{';'.join(codes)}m" if codes else ""

    def __format__(self, format_spec: str) -> str:
        if format_spec == '#':
            return "\033[0m"
        return str(self)


class Styles:
    """Terminal styling definitions."""

    def __init__(self):
        self.header_style = Style()
        self.literal_style = Style()
        self.usage_style = Style()
        self.placeholder_style = Style()

    @classmethod
    def styled(cls) -> "Styles":
        """Default terminal styling."""
        return (Styles().header(Style().bold().underline())
                    .literal(Style().bold())
                    .usage(Style().bold().underline())
                    .placeholder(Style()))

    def header(self, style: Style) -> Self:
        """General Heading style, e.g., `help_heading`."""
        self.header_style = style
        return self

    def literal(self, style: Style) -> Self:
        """Literal command-line syntax, e.g., `--help`."""
        self.literal_style = style
        return self

    def usage(self, style: Style) -> Self:
        """Usage heading."""
        self.usage_style = style
        return self

    def placeholder(self, style: Style) -> Self:
        """Descriptions within command-line syntax, e.g., `value_name`."""
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

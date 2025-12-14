import sys
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import Optional, override


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

    The user's terminal defines the meaning of the each palette code.
    """

    Black = auto()
    """Black: #0 (foreground code `30`, background code `40`)."""
    Red = auto()
    """Red: #1 (foreground code `31`, background code `41`)."""
    Green = auto()
    """Green: #2 (foreground code `32`, background code `42`)."""
    Yellow = auto()
    """Yellow: #3 (foreground code `33`, background code `43`)."""
    Blue = auto()
    """Blue: #4 (foreground code `34`, background code `44`)."""
    Magenta = auto()
    """Magenta: #5 (foreground code `35`, background code `45`)."""
    Cyan = auto()
    """Cyan: #6 (foreground code `36`, background code `46`)."""
    White = auto()
    """White: #7 (foreground code `37`, background code `47`)."""
    BrightBlack = auto()
    """Bright black: #0 (foreground code `90`, background code `100`)."""
    BrightRed = auto()
    """Bright red: #1 (foreground code `91`, background code `101`)."""
    BrightGreen = auto()
    """Bright green: #2 (foreground code `92`, background code `102`)."""
    BrightYellow = auto()
    """Bright yellow: #3 (foreground code `93`, background code `103`)."""
    BrightBlue = auto()
    """Bright blue: #4 (foreground code `94`, background code `104`)."""
    BrightMagenta = auto()
    """Bright magenta: #5 (foreground code `95`, background code `105`)."""
    BrightCyan = auto()
    """Bright cyan: #6 (foreground code `96`, background code `106`)."""
    BrightWhite = auto()
    """Bright white: #7 (foreground code `97`, background code `107`)."""


@dataclass(slots=True)
class Style:
    """ANSI text styling.

    You can print a `Style` to render the corresponding ANSI code. Using the
    alternate flag `#` will render the ANSI reset code, if needed. Together,
    this makes it convenient to render styles using inline format arguments.

    Example:

    ```python
    style = Style().bold()
    value = 42
    print(f"{style}value{style:#}")
    ```
    """

    color_fg: Optional[AnsiColor] = None
    color_bg: Optional[AnsiColor] = None
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
        self.color_fg = color
        return self

    def bg_color(self, color: Optional[AnsiColor] = None) -> "Style":
        """Set background color."""
        self.color_bg = color
        return self

    def render_fg(self) -> str:
        """Render the ANSI code for a foreground color."""
        match self.color_fg:
            case None: return ""
            case AnsiColor.Black: return "30"
            case AnsiColor.Red: return "31"
            case AnsiColor.Green: return "32"
            case AnsiColor.Yellow: return "33"
            case AnsiColor.Blue: return "34"
            case AnsiColor.Magenta: return "35"
            case AnsiColor.Cyan: return "36"
            case AnsiColor.White: return "37"
            case AnsiColor.BrightBlack: return "90"
            case AnsiColor.BrightRed: return "91"
            case AnsiColor.BrightGreen: return "92"
            case AnsiColor.BrightYellow: return "93"
            case AnsiColor.BrightBlue: return "94"
            case AnsiColor.BrightMagenta: return "95"
            case AnsiColor.BrightCyan: return "96"
            case AnsiColor.BrightWhite: return "97"

    def render_bg(self) -> str:
        """Render the ANSI code for a background color."""
        match self.color_bg:
            case None: return ""
            case AnsiColor.Black: return "40"
            case AnsiColor.Red: return "41"
            case AnsiColor.Green: return "42"
            case AnsiColor.Yellow: return "43"
            case AnsiColor.Blue: return "44"
            case AnsiColor.Magenta: return "45"
            case AnsiColor.Cyan: return "46"
            case AnsiColor.White: return "47"
            case AnsiColor.BrightBlack: return "100"
            case AnsiColor.BrightRed: return "101"
            case AnsiColor.BrightGreen: return "102"
            case AnsiColor.BrightYellow: return "103"
            case AnsiColor.BrightBlue: return "104"
            case AnsiColor.BrightMagenta: return "105"
            case AnsiColor.BrightCyan: return "106"
            case AnsiColor.BrightWhite: return "107"

    def render_reset(self) -> str:
        """Renders the ANSI reset code.

        Ellides the code if there is nothing to reset.
        """
        if self != Style():
            return "\033[0m"
        return ""

    @override
    def __str__(self) -> str:
        codes = []
        if self.color_fg is not None:
            codes.append(self.render_fg())
        if self.color_bg is not None:
            codes.append(self.render_bg())
        if self.is_bold:
            codes.append("1")
        if self.is_dimmed:
            codes.append("2")
        if self.is_italic:
            codes.append("3")
        if self.is_underline:
            codes.append("4")
        return f"\033[{';'.join(codes)}m" if codes else ""

    @override
    def __format__(self, format_spec: str) -> str:
        if format_spec == "#":
            return self.render_reset()
        return str(self)


class Styles:
    """Terminal styling definitions.

    Example:

    ```python
    from clap import AnsiColor, Style, Styles

    styles = (
        Styles()
            .header(Style().bold().underline())
            .literal(Style().fg_color(AnsiColor.Green).bold())
    )
    ```
    """

    def __init__(self):
        self.header_style = Style()
        self.literal_style = Style()
        self.usage_style = Style()
        self.placeholder_style = Style()

    @classmethod
    def styled(cls) -> "Styles":
        """Default terminal styling."""
        return (
            Styles()
                .header(Style().bold().underline())
                .literal(Style().bold())
                .usage(Style().bold().underline())
                .placeholder(Style())
        )

    def header(self, style: Style) -> "Styles":
        """General heading style, e.g., `Commands`."""
        self.header_style = style
        return self

    def literal(self, style: Style) -> "Styles":
        """Literal command-line syntax, e.g., `--help`."""
        self.literal_style = style
        return self

    def usage(self, style: Style) -> "Styles":
        """Usage heading."""
        self.usage_style = style
        return self

    def placeholder(self, style: Style) -> "Styles":
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

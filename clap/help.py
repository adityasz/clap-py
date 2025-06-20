import shutil
import textwrap
from dataclasses import dataclass
from typing import Optional, Union, cast

from .models import Arg, Command
from .styling import ColorChoice, Styles, determine_color_usage

INDENT = " " * 2
TAB = " " * 8
NEXT_LINE_INDENT = INDENT + TAB

DEFAULT_TEMPLATE = """\
{before-help}{about-with-newline}
{usage-heading} {usage}

{all-args}{after-help}\
"""


@dataclass(slots=True)
class Writer:
    s: str = ""

    def push_str(self, s: str):
        self.s += s

    def strip(self):
        self.s = self.s.strip()
        self.push_str("\n")

    def print(self):
        print(self.s, end="")


class HelpRenderer:
    def __init__(self, command: Command):
        self.command = command
        self.template = self.command.help_template or DEFAULT_TEMPLATE
        self.original_styles = self.command.styles or Styles.styled()
        self.set_color(self.command.color or ColorChoice.Auto)
        self.writer = Writer()
        self.term_width = shutil.get_terminal_size().columns
        if w := command.max_term_width:
            self.term_width = min(self.term_width, w)
        self.use_long = False

    # TODO: arg with type ColorChoice should override help output color also
    def set_color(self, color: ColorChoice):
        if determine_color_usage(color):
            self.active_styles = self.original_styles
            self.reset_ansi = "\033[0m"
        else:
            self.active_styles = Styles()
            self.reset_ansi = ""

    # TODO: when this library is no longer dependent on argparse, there wouldn't
    # be a need for this function because `HelpRender` will be instantiated when
    # printing help and `use_long` will be passed to the constructor
    def set_use_long(self, use_long: bool):
        self.use_long = use_long

    def style_header(self, text: str) -> str:
        return f"{self.active_styles.header_style}{text}{self.reset_ansi}"

    def style_literal(self, text: str) -> str:
        return f"{self.active_styles.literal_style}{text}{self.reset_ansi}"

    def style_placeholder(self, text: str) -> str:
        return f"{self.active_styles.placeholder_style}{text}{self.reset_ansi}"

    def style_usage(self, text: str) -> str:
        return f"{self.active_styles.usage_style}{text}{self.reset_ansi}"

    def render(self):
        self.write_templated_help()
        self.writer.strip()
        self.writer.print()

    def write_templated_help(self):
        cmd = self.command
        for part in self.template.split("{")[1:]:
            tag, rest = part.split("}", maxsplit=1)
            match tag:
                case "before-help":
                    self.writer.push_str(
                        self.get_about(cmd.before_help, cmd.before_long_help, False)
                    )
                case "about-with-newline":
                    self.writer.push_str(self.get_about(cmd.about, cmd.long_about, False))
                    self.writer.push_str("\n")
                case "usage-heading":
                    self.writer.push_str(self.style_header("Usage:"))
                case "usage":
                    self.writer.push_str(self.format_usage())
                case "all-args":
                    self.write_all_args()
                case "after-help":
                    self.writer.push_str(
                        self.get_about(cmd.before_help, cmd.before_long_help, False)
                    )
            self.writer.push_str(rest)

    def format_usage(self, command: Optional[Command] = None, usage_prefix: str = "") -> str:
        if command is None:
            command = self.command

        if command.usage is not None:
            return command.usage

        parts: list[str] = [usage_prefix] if usage_prefix else []
        parts.append(self.style_literal(command.name))
        if any(
            arg.required is not True and not arg.is_positional()
            for arg in command.args.values()
        ):
            parts.append("[OPTIONS]")
        for arg in command.args.values():
            if arg.required is True and not arg.is_positional():
                parts.append(self.style_literal(cast(str, arg.long or arg.short)))
                if arg.value_name:
                    parts.append(self.style_placeholder(arg.value_name))
        for mutex, args in command.mutexes.items():
            if mutex.required:
                mutex_usage = "<"
                mutex_usage += " | ".join(
                    f"{self.style_literal(cast(str, arg.short or arg.long))} {arg.value_name}"
                    for arg in args
                )
                mutex_usage += ">"
                parts.append(mutex_usage)
        for arg in command.args.values():
            if arg.is_positional():
                parts.append(cast(str, arg.value_name))
        usage = " ".join(parts)
        if command.contains_subcommands():
            for subcommand in command.subcommands.values():
                self.format_usage(subcommand, usage)
            if command.subcommand_required is True:
                subcommand_value_name = f"<{command.subcommand_value_name}>"
            else:
                subcommand_value_name = f"[{command.subcommand_value_name}]"
            usage += f" {subcommand_value_name}"
        command.usage = usage
        return usage

    def get_about(
        self, short: Optional[str], long: Optional[str], use_long_for_short: bool
    ) -> str:
        if self.use_long:
            return long or short or ""
        if use_long_for_short:
            return short or long or ""
        return short or ""

    def write_padding(self, padding: int):
        self.writer.push_str(" " * padding)

    def write_help(
        self,
        arg: Optional[Arg],
        about: str,
        spec_vals: list[str],
        next_line_help: bool,
        longest: int,
    ):
        if arg:
            arg_header = ""
            if arg.is_positional():
                value_name = cast(str, arg.value_name)
                arg_header = self.style_placeholder(value_name)
                padding = longest - len(value_name)
            else:
                length = 2
                if arg.short:
                    arg_header += self.style_literal(cast(str, arg.short))
                    if arg.long:
                        arg_header += ", "
                if arg.long:
                    if not arg.short:
                        arg_header = " " * 4
                    length += 2 + len(cast(str, arg.long))
                    arg_header += f"{self.style_literal(cast(str, arg.long))}"
                if arg.value_name:
                    length += 1 + len(arg.value_name)
                    arg_header += f" {self.style_placeholder(arg.value_name)}"
                padding = longest - length
            self.writer.push_str(INDENT)
            self.writer.push_str(arg_header)
            if next_line_help:
                self.writer.push_str("\n")
            else:
                self.write_padding(padding)

        if next_line_help:
            initial_indent = NEXT_LINE_INDENT
            subsequent_indent = NEXT_LINE_INDENT
            width = self.term_width - len(NEXT_LINE_INDENT)
        else:
            initial_indent = INDENT
            subsequent_indent = INDENT + " " * longest + INDENT
            width = self.term_width - 2 * len(INDENT) - longest

        if not next_line_help and spec_vals:
            about = f"{about} {" ".join(spec_vals)}"

        self.writer.push_str(
            "\n".join(
                "\n".join(
                    textwrap.wrap(
                        par,
                        width=width,
                        initial_indent=initial_indent,
                        subsequent_indent=subsequent_indent,
                    )
                )
                for par in about.splitlines()
            )
        )

        if next_line_help:
            if spec_vals:
                self.writer.push_str("\n")
                self.writer.push_str(f"\n{NEXT_LINE_INDENT}".join(spec_vals))
            self.writer.push_str("\n")
        self.writer.push_str("\n")

    def spec_vals(self, thing: Union[Arg, Command]) -> list[str]:
        if isinstance(arg := thing, Arg):
            spec_vals = []
            if arg.default_value:
                spec_vals.append(f"[default: {arg.default_value}")
            if arg.choices:
                spec_vals.append(f"[possible values: {", ".join(arg.choices)}]")
            if arg.aliases:
                spec_vals.append(f"[aliases: {", ".join(arg.aliases)}")
            return spec_vals
        else:
            cmd = thing
            if cmd.aliases:
                return [f"[aliases: {", ".join(cmd.aliases)}]"]
            return []

    def write_subcommands(self):
        self.writer.push_str(self.style_header(f"{self.command.subcommand_help_heading}:"))
        self.writer.push_str("\n")
        subcommands = self.command.subcommands

        longest = 1
        for name, _ in subcommands.items():
            longest = max(len(name), longest)

        next_line_help = any(
            (lambda about, spec:
                (taken := longest + 2 * len(INDENT)) <= self.term_width
                and taken / self.term_width > 0.40
                and taken + len(about + (" " + spec if about and spec else spec)) > self.term_width
            )(subcommand.about or subcommand.long_about or "",
              " ".join(self.spec_vals(subcommand)))
            for subcommand in subcommands.values()
        )

        for name, subcommand in subcommands.items():
            self.writer.push_str(INDENT)
            self.writer.push_str(self.style_literal(name))
            if not next_line_help:
                self.write_padding(longest - len(name))
            self.write_help(
                None,
                subcommand.about or subcommand.long_about or "",  # prefer about over long about
                self.spec_vals(subcommand),
                next_line_help,
                longest,
            )
        self.writer.push_str("\n")

    def write_arg_group(self, title: str, about: str, args: list[Arg]):
        self.writer.push_str(self.style_header(f"{title}:"))
        self.writer.push_str("\n")
        self.writer.push_str(
            "\n".join(
                "\n".join(textwrap.wrap(par, width=self.term_width))
                for par in about.splitlines()
            )
        )
        self.writer.push_str("\n\n")

        longest = 2
        for arg in args:
            if arg.is_positional():
                longest = max(longest, len(cast(str, arg.value_name)))
            else:
                length = 2
                if arg.long:
                    length += 2 + len(cast(str, arg.long))
                if arg.value_name:
                    length += 1 + len(arg.value_name)
                longest = max(longest, length)
        next_line_help = any(
            (lambda about, spec:
                (taken := longest + 2 * len(INDENT)) <= self.term_width
                and taken / self.term_width > 0.40
                and taken + len(about + (" " + spec if about and spec else spec)) > self.term_width
                or "\n" in about
            )(self.get_about(arg.help, arg.long_help, True), " ".join(self.spec_vals(arg)))
            for arg in args
        )
        for arg in args:
            self.write_help(
                arg,
                self.get_about(arg.help, arg.long_help, True),
                self.spec_vals(arg),
                next_line_help,
                longest,
            )
        self.writer.strip()

    def write_all_args(self):
        if self.command.contains_subcommands():
            self.write_subcommands()

        arguments: list[Arg] = []
        options: list[Arg] = []
        for arg in self.command.args.values():
            if arg.group or arg.mutex:
                continue
            if arg.is_positional():
                arguments.append(arg)
            else:
                options.append(arg)
        if arguments:
            self.write_arg_group("Arguments", "", arguments)
            self.writer.push_str("\n")
        if options:
            self.write_arg_group("Options", "", options)
            self.writer.push_str("\n")
        for group, args in self.command.groups.items():
            if self.use_long:
                about = group.long_about or group.about or ""
            else:
                about = group.about or ""
            self.write_arg_group(group.title, about, args)
            self.writer.push_str("\n")

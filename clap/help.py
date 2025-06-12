import textwrap
from collections.abc import Iterable
from string import Template
from typing import Optional, cast

from .models import Arg, Command
from .styling import ColorChoice, Styles, determine_color_usage

DEFAULT_TEMPLATE = """\
${before_help}${about_with_newline}
${usage_heading} ${usage}

${all_args}${after_help}\
"""


class HelpRenderer:
    TAB = 8
    SECTION_INDENT = 2
    COL_SEP = 2

    def __init__(
        self,
        command: Command,
        color: ColorChoice,
        template: Optional[str] = None,
        style: Optional[Styles] = None,
    ):
        self.command = command
        if template is None:
            template = DEFAULT_TEMPLATE
        self.template = Template(template)
        self.original_style = style or Styles.styled()
        self.set_color(color)
        import shutil
        self.width = min(shutil.get_terminal_size().columns, 100)

    # TODO: ColorChoice args should override help output color
    def set_color(self, color: ColorChoice):
        if determine_color_usage(color):
            self.active_style = self.original_style
            self.reset_ansi = "\033[0m"
        else:
            self.active_style = Styles()
            self.reset_ansi = ""

    def style_header(self, text: str) -> str:
        return f"{self.active_style.header_style}{text}{self.reset_ansi}"

    def style_literal(self, text: str) -> str:
        return f"{self.active_style.literal_style}{text}{self.reset_ansi}"

    def style_placeholder(self, text: str) -> str:
        return f"{self.active_style.placeholder_style}{text}{self.reset_ansi}"

    def style_usage(self, text: str) -> str:
        return f"{self.active_style.usage_style}{text}{self.reset_ansi}"

    def render(self, long: bool) -> str:
        ctx = self.build_context(long)
        return self.template.substitute(ctx).strip()

    def build_context(self, long: bool) -> dict[str, str]:
        if long:
            before_help = self.command.before_long_help or self.command.before_help or ""
        else:
            before_help = self.command.before_help or ""
        if long:
            after_help = self.command.after_long_help or self.command.after_help or ""
        else:
            after_help = self.command.after_help or ""
        return {
            "before_help": before_help,
            "about_with_newline": f"{self.command.about}\n" if self.command.about else "",
            "usage_heading": self.style_header("Usage:"),
            "usage": self.format_usage(self.command),
            "all_args": self.format_all_args(long),
            "after_help": after_help,
        }

    def format_usage(self, command: Command, usage_prefix: str = "") -> str:
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

    def format_section(
        self,
        title: str,
        rows: list[tuple[str, str, int]],
        max_arg_header_width: int
    ) -> str:
        lines: list[str] = [self.style_header(f"{title}:")]
        if max_arg_header_width > 0.3 * self.width:
            for row in rows:
                arg_header, help_string, _ = row
                lines.append(textwrap.indent(arg_header, " " * self.SECTION_INDENT))
                indent = self.TAB + self.SECTION_INDENT
                lines.extend(
                    textwrap.wrap(
                        help_string,
                        width=self.width,
                        initial_indent=" " * indent,
                        subsequent_indent=" " * indent,
                    )
                )
        else:
            for row in rows:
                arg_header, help_string, arg_header_width = row
                space = self.COL_SEP + max_arg_header_width - arg_header_width
                lines.extend(
                    textwrap.wrap(
                        f"{arg_header}{'': <{space}}{help_string}",
                        width=self.width,
                        initial_indent=" " * self.SECTION_INDENT,
                        subsequent_indent=(
                            " " * (self.SECTION_INDENT + max_arg_header_width + self.COL_SEP)
                        ),
                    )
                )
        return "\n".join(lines)

    def build_arg_header(self, arg: Arg) -> tuple[str, int]:
        if arg.is_positional():
            arg_header = cast(str, arg.value_name)
            return arg_header, len(arg_header)
        arg_header = ""
        width = 0
        if arg.short:
            arg_header += f"{self.style_literal(cast(str, arg.short))}, "
        else:
            arg_header += f"{'':<4}"
        width += 4
        if long_flag := cast(Optional[str], arg.long):
            arg_header += self.style_literal(long_flag)
            width += len(long_flag)
        if arg.value_name:
            arg_header += f" {self.style_placeholder(arg.value_name)}"
            width += 1 + len(arg.value_name)
        return arg_header, width

    def get_help_text(
        self, short_help: Optional[str], long_help: Optional[str], long: bool
    ) -> Optional[str]:
        if long:
            return long_help or short_help
        return short_help or long_help

    def build_arg_rows(self, args: list[Arg], long: bool) -> tuple[list, int]:
        rows: list[tuple[str, str, int]] = []
        max_width = 0

        for arg in args:
            arg_header, width = self.build_arg_header(arg)
            max_width = max(width, max_width)

            help_parts: list[str] = []
            if help_text := self.get_help_text(arg.help, arg.long_help, long):
                help_parts.append(help_text)
            if arg.default_value:
                help_parts.append(f"[default: {arg.default_value}]")
            if arg.choices:
                help_parts.append(f"[possible values: {", ".join(arg.choices)}]")
            if arg.aliases:
                help_parts.append(f"[aliases: {", ".join(arg.aliases)}]")

            rows.append((arg_header, " ".join(help_parts), width))

        return rows, max_width

    def format_subcommands(self, subcommands: Iterable[tuple[str, Command]], long: bool) -> str:
        rows: list[tuple[str, str, int]] = []
        max_name_width = 0
        for subcommand_name, subcommand in subcommands:
            help_parts: list[str] = []
            if help_text := self.get_help_text(subcommand.about, subcommand.long_about, long):
                help_parts.append(help_text)
            if subcommand.aliases:
                help_parts.append(f"[aliases: {", ".join(subcommand.aliases)}]")
            max_name_width = max(max_name_width, len(subcommand.name))
            rows.append((
                self.style_literal(subcommand_name),
                " ".join(help_parts),
                len(subcommand_name),
            ))
        return self.format_section(self.command.subcommand_help_heading, rows, max_name_width)

    def format_all_args(self, long: bool) -> str:
        output: list[str] = []

        arguments: list[Arg] = []
        options: list[Arg] = []

        if self.command.contains_subcommands():
            output.append(self.format_subcommands(self.command.subcommands.items(), long))

        for arg in self.command.args.values():
            if arg.group or arg.mutex:
                continue
            if arg.is_positional():
                arguments.append(arg)
            else:
                options.append(arg)

        if arguments:
            output.append(self.format_section("Arguments", *self.build_arg_rows(arguments, long)))
        if options:
            output.append(self.format_section("Options", *self.build_arg_rows(options, long)))
        for group, args in self.command.groups.items():
            if long:
                if group.long_about:
                    output.append(group.long_about)
                elif group.about:
                    output.append(group.about)
            else:
                if group.about:
                    output.append(group.about)
            output.append(self.format_section(group.title, *self.build_arg_rows(args, long)))

        return "\n\n".join(output)

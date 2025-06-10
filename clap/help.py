import textwrap
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
        if determine_color_usage(color):
            if style is None:
                style = Styles.styled()
            self.header_style = style.header_style
            self.literal_style = style.literal_style
            self.placeholder_style = style.placeholder_style
            self.usage_style = style.usage_style
            self.reset_ansi = "\033[0m"
        else:
            self.header_style = ""
            self.literal_style = ""
            self.placeholder_style = ""
            self.usage_style = ""
            self.reset_ansi = ""
        import shutil
        self.width = max(shutil.get_terminal_size().columns, 100)

    def style_header(self, text: str) -> str:
        return f"{self.header_style}{text}{self.reset_ansi}"

    def style_literal(self, text: str) -> str:
        return f"{self.literal_style}{text}{self.reset_ansi}"

    def style_placeholder(self, text: str) -> str:
        return f"{self.placeholder_style}{text}{self.reset_ansi}"

    def style_usage(self, text: str) -> str:
        return f"{self.usage_style}{text}{self.reset_ansi}"

    def render(self, long: bool) -> str:
        ctx = self.build_context(long)
        return self.template.substitute(ctx).strip()

    def build_context(self, long: bool) -> dict[str, str]:
        return {
            "before_help": self.command.before_help or "",
            "about_with_newline": f"{self.command.about}\n" if self.command.about else "",
            "usage_heading": self.style_header("Usage:"),
            "usage": self.format_usage(self.command),
            "all_args": self.format_all_args(long),
            "after_help": self.command.after_help or "",
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
                parts.append(cast(str, arg.long or arg.short))
                parts.append(cast(str, arg.value_name))
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
        left_column_width: int
    ) -> str:
        lines: list[str] = [self.style_header(f"{title}:")]
        if left_column_width > 0.3 * self.width:
            for row in rows:
                lines.append(textwrap.indent(row[0], " " * self.SECTION_INDENT))
                indent = self.TAB + self.SECTION_INDENT
                lines.extend(
                    textwrap.wrap(
                        row[1],
                        self.width - indent,
                        initial_indent=" " * indent,
                        subsequent_indent=" " * indent,
                    )
                )
        else:
            for row in rows:
                padding = self.COL_SEP + left_column_width - row[2]
                lines.extend(
                    textwrap.wrap(
                        f"{row[0]}{'': <{padding}}{row[1]}",
                        width=self.width - left_column_width - self.COL_SEP,
                        initial_indent=" " * self.SECTION_INDENT,
                        subsequent_indent=(
                            " " * (self.SECTION_INDENT + left_column_width + self.COL_SEP)
                        ),
                    )
                )
        return "\n".join(lines)

    def format_all_args(self, long: bool) -> str:
        output: list[str] = []

        arguments: list[Arg] = []
        options: list[Arg] = []

        if self.command.contains_subcommands():
            content: list[tuple[str, str, int]] = []
            left_column_width = 0
            for subcommand_name, subcommand in self.command.subcommands.items():
                help_parts: list[str] = []
                if long and subcommand.long_about is not None:
                    help_parts.append(subcommand.long_about)
                elif subcommand.about is not None:
                    help_parts.append(subcommand.about)
                if subcommand.aliases:
                    help_parts.append(f"[aliases: {", ".join(subcommand.aliases)}]")
                left_column_width = max(left_column_width, len(subcommand.name))
                content.append((
                    self.style_literal(subcommand_name),
                    " ".join(help_parts),
                    len(subcommand_name),
                ))
            output.append(
                self.format_section(
                    self.command.subcommand_help_heading, content, left_column_width
                )
            )

        for arg in self.command.args.values():
            if arg.group or arg.mutex:
                continue
            if arg.is_positional():
                arguments.append(arg)
            else:
                options.append(arg)

        def format_args_content(args: list[Arg]) -> tuple[list, int]:
            rows: list[tuple[str, str, int]] = []
            left_column_width = 0
            for arg in args:
                help_parts: list[str] = []
                if long and arg.long_about is not None:
                    help_parts.append(arg.long_about)
                elif arg.about is not None:
                    help_parts.append(arg.about)
                if arg.choices:
                    help_parts.append(f"[choices: {", ".join(arg.choices)}]")
                if arg.default_value:
                    help_parts.append(f"[default: {arg.default_value}]")
                if arg.aliases:
                    help_parts.append(f"[aliases: {", ".join(arg.aliases)}]")
                if arg.is_positional():
                    lhs = cast(str, arg.value_name)
                    width = len(lhs)
                    left_column_width = max(left_column_width, width)
                else:
                    lhs = f"{arg.short}, " if arg.short is not None else f'{"": <4}'
                    if arg.long is not None:
                        lhs += cast(str, arg.long)
                    width = len(lhs)
                    lhs = self.style_literal(lhs)
                    if arg.value_name:
                        lhs += f" {arg.value_name}"
                        width += 1 + len(arg.value_name)
                    left_column_width = max(left_column_width, width)
                rows.append((lhs, " ".join(help_parts), width))
            return rows, left_column_width

        if arguments:
            output.append(self.format_section("Arguments", *format_args_content(arguments)))
        if options:
            output.append(self.format_section("Options", *format_args_content(options)))
        for group, args in self.command.groups.items():
            if group.description:
                output.append(group.description)
            output.append(self.format_section(group.title, *format_args_content(args)))

        return "\n\n".join(output)


def generate_usage(command: Command, ansi_prefix: str, usage_prefix: str = ""):
    if command.usage is not None:
        return command.usage

    RESET = "\033[0m"
    command.usage = ""
    if usage_prefix:
        command.usage = usage_prefix + " "
    command.usage += usage_prefix + command.name
    command.usage += f"{usage_prefix}{ansi_prefix}{command.name}{RESET}"
    if any(arg.required is not True and not arg.is_positional() for arg in command.args.values()):
        command.usage += " [OPTIONS]"
    for arg in command.args.values():
        if arg.required is True and not arg.is_positional():
            command.usage += f" {ansi_prefix}{arg.long or arg.short}{RESET} {arg.value_name}"
    for mutex, args in command.mutexes.items():
        if mutex.required:
            command.usage += " <"
        command.usage += " | ".join(f"{arg.short or arg.long} {arg.value_name}" for arg in args)
        command.usage += ">"
    for arg in command.args.values():
        if arg.is_positional():
            command.usage += f" {arg.value_name}"
    if command.contains_subcommands():
        for subcommand in command.subcommands.values():
            generate_usage(subcommand, "", command.usage)
        if command.subcommand_required is True:
            value_name = f"<{command.subcommand_value_name}>"
        else:
            value_name = f"[{command.subcommand_value_name}]"
        command.usage += f" {value_name}"

    return command.usage

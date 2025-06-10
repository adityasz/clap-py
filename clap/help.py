from string import Template
from typing import Optional

from .models import Command
from .styling import AnsiColor, ColorChoice, HelpStyle, determine_color_usage

DEFAULT_TEMPLATE = """\
${before_help}${about_with_newline}
${usage_heading} ${usage}

${all_args}${after_help}\
"""


class HelpRenderer:
    def __init__(
        self,
        command: Command,
        color: ColorChoice,
        template: Optional[str] = None,
        style: Optional[HelpStyle] = None,
    ):
        self.command = command
        if template is None:
            template = DEFAULT_TEMPLATE
        self.template = Template(template)
        if style is None:
            style = HelpStyle(
                header_style=AnsiColor.Black.bold().underline(),
                option_style=AnsiColor.Black.bold()
            )
        if determine_color_usage(color):
            if style is None:
                self.header_ansi = AnsiColor.Black.bold().underline().to_ansi()
                self.option_ansi = AnsiColor.Black.bold().to_ansi()
            else:
                if style.header_style is not None:
                    self.header_ansi = style.header_style.to_ansi()
                if style.option_style is not None:
                    self.option_ansi = style.option_style.to_ansi()
            self.reset_ansi = "\033[0m"
        else:
            self.header_ansi = ""
            self.option_ansi = ""
            self.reset_ansi = ""

    def style_header(self, text: str) -> str:
        return self.header_ansi + text + self.reset_ansi

    def style_option(self, text: str) -> str:
        return self.option_ansi + text + self.reset_ansi

    def render(self, long: bool) -> str:
        ctx = self.build_context(long)
        return self.template.substitute(ctx).strip()

    def build_context(self, long: bool) -> dict[str, str]:
        return {
            "before_help": self.command.before_help or "",
            "about_with_newline": f"{self.command.about}\n" if self.command.about else "",
            "usage_heading": self.style_header("Usage:"),
            "usage": self.format_usage(),
            "all_args": self.format_all_args(long),
            "after_help": self.command.after_help or "",
        }

    def format_usage(self) -> str:
        return ""

    def format_all_args(self, long: bool) -> str:
        return ""


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

"""
This file was written by Claude 4.0 Sonnet in Cursor
(and then cleaned up by hand).

Parts of this file (or the entire script) may be completely incorrect. The only
test for this is to look at the help output at the bottom of the quickstart
guide and see if it makes sense (right now, it does).
"""

import os
import re
import subprocess
from io import StringIO

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from rich.console import Console
from rich.text import Text

TERM_WIDTH = 100


class InsertStdoutPlugin(BasePlugin):
    config_scheme = (
        ('root', config_options.Type(str, default='.')),
    )

    def on_page_markdown(self, markdown: str, **_) -> str:
        def replace_stdout_marker(match):
            command = match.group(1).strip()
            return self.execute_command(command)

        pattern = r"<~--\s*stdout\[(.*?)\]\s*-->"
        return re.sub(pattern, replace_stdout_marker, markdown)

    def execute_command(self, command: str) -> str:
        env = os.environ.copy()
        env["COLUMNS"] = str(TERM_WIDTH)

        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=False,
            env=env,
            cwd=self.config["root"]
        )
        assert result.returncode == 0

        console = Console(
            file=StringIO(),
            record=True,
            width=TERM_WIDTH,
            force_terminal=True,
        )

        prompt = Text()
        prompt.append("adityasz@github:clap-py$ ", style="bold")
        console.print(prompt, end="")
        console.print(command)
        output_text = Text.from_ansi(result.stdout)
        console.print(output_text, end="")

        html = console.export_html(inline_styles=True)

        # Extract just the content from the <code> tag, without any style sheets
        content_match = re.search(r"<code[^>]*>(.*?)</code>", html, re.DOTALL)
        assert content_match is not None
        code_content = content_match.group(1)

        return f'<div class="stdout"><pre><code>{code_content}</code></pre></div>\n'

"""
This file was written by Claude 4.0 Sonnet in Cursor
(and then cleaned up by hand).

Parts of this file (or the entire script) may be completely incorrect. The only
test for this is to look at the help output at the bottom of the quickstart
guide and see if it makes sense (right now, it does).
"""

import os
import pty
import re
import select
import subprocess
from contextlib import suppress
from io import StringIO
from typing import Optional, override

from mkdocs.config import config_options
from mkdocs.config.base import LegacyConfig  # for some reason, the default is called Legacy
from mkdocs.plugins import BasePlugin
from rich.console import Console
from rich.text import Text

TERM_WIDTH = 100


class InsertCommandOutputPlugin(BasePlugin[LegacyConfig]):
    config_scheme = (("root", config_options.Type(str, default=".")),)

    @override
    def on_page_markdown(self, markdown: str, **_) -> str:
        def replace_output_marker(match):
            command = match.group(1).strip()
            return self.get_output_as_html(command)

        pattern = r"<~--\s*output\[(.*?)\]\s*-->"
        return re.sub(pattern, replace_output_marker, markdown)

    def read_pty_output(self, master_fd: int, process: subprocess.Popen[bytes]) -> bytes:
        process.wait()

        output = b""
        with suppress(OSError):
            while True:
                ready, _, _ = select.select([master_fd], [], [], 0)
                if not ready:
                    break
                chunk = os.read(master_fd, 4096)
                if not chunk:
                    break
                output += chunk

        return output

    def cleanup_fds(self, master_fd: Optional[int] = None, slave_fd: Optional[int] = None) -> None:
        if slave_fd is not None:
            with suppress(OSError):
                os.close(slave_fd)

        if master_fd is not None:
            with suppress(OSError):
                os.close(master_fd)

    def get_output_as_html(self, command: str) -> str:
        env = os.environ.copy()
        env["COLUMNS"] = str(TERM_WIDTH)
        master_fd, slave_fd = pty.openpty()

        try:
            process = subprocess.Popen(
                command.split(),
                stdout=slave_fd,
                stderr=slave_fd,
                stdin=subprocess.DEVNULL,
                env=env,
                cwd=self.config["root"],
            )
            self.cleanup_fds(master_fd=None, slave_fd=slave_fd)
            output = self.read_pty_output(master_fd, process)
            return self.ansi_to_html(command, output.decode("utf-8", errors="replace"))
        finally:
            self.cleanup_fds(master_fd, slave_fd=None)

    def ansi_to_html(self, command: str, output: str) -> str:
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
        console.print(Text.from_ansi(output), end="")

        html = console.export_html(inline_styles=True)
        content_match = re.search(r"<code[^>]*>(.*?)</code>", html, re.DOTALL)
        assert content_match is not None
        code_content = content_match.group(1)

        return f'<div class="command-output"><pre><code>{code_content}</code></pre></div>\n'

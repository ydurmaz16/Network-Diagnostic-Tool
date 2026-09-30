"""Safe subprocess execution.

Commands are always passed as an argument list with shell=False, so user
input can never be interpreted by a shell.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    output: str
    timed_out: bool = False


def _decode(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data


def run_command(args: Sequence[str], timeout: float) -> CommandResult:
    """Run a command without a shell and return its combined output.

    Raises FileNotFoundError if the executable does not exist.
    """
    extra: dict = {}
    if sys.platform == "win32":
        extra["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        proc = subprocess.run(  # noqa: S603 - shell=False, validated args
            list(args),
            capture_output=True,
            timeout=timeout,
            shell=False,
            check=False,
            stdin=subprocess.DEVNULL,
            **extra,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(None, _decode(exc.stdout), timed_out=True)

    return CommandResult(proc.returncode, _decode(proc.stdout) + _decode(proc.stderr))

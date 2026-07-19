"""Ponto de entrada do ambiente de desenvolvimento.

Execute no ambiente virtual do projeto com: ``python dev.py``.
"""

from __future__ import annotations

import traceback

from devtools.events import EVENTS
from devtools.logger import Logger
from devtools.runner import DevelopmentRunner


def main() -> None:
    Logger.setup()
    Logger.banner()
    runner = DevelopmentRunner()
    EVENTS.emit("before_start", runner)
    try:
        runner.start()
    except Exception as error:
        Logger.error(f"Erro não tratado no ambiente: {error}")
        traceback.print_exc()
        EVENTS.emit("error", error)
        runner.shutdown()


if __name__ == "__main__":
    main()

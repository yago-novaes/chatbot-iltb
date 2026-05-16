"""
Workaround para bug asyncio Python 3.14 no Windows.
Força ProactorEventLoop antes de invocar notebooklm.
"""
import asyncio
import sys

# Fix: forçar ProactorEventLoop no Windows (evita AssertionError em _write_send)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Importar e rodar o CLI do notebooklm normalmente
from notebooklm.notebooklm_cli import cli
cli()

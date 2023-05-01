from collections.abc import Callable

from typing_extensions import TypeAlias
from flask import Flask


OnHandler: TypeAlias = Callable[[], None]


class SocketIO():
    
    def __init__(self, app: Flask) -> None:
        ...
    
    def on(self, type: str) -> Callable[[OnHandler], OnHandler]:
        ...
    
    def run(self, app: Flask, host: str, port: int) -> None:
        ...


def emit(type: str, content: str) -> None:
    ...


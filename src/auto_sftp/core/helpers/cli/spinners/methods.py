import typing as t
from contextlib import contextmanager

from rich.console import Console
from rich.spinner import Spinner

from loguru import logger as log


@contextmanager
def get_console() -> t.Generator[Console, t.Any, None]:
    try:
        console: Console = Console()

        yield console
    except Exception as exc:
        msg = Exception(f"Unhandled exception getting rich Console. Details: {exc}")
        log.error(msg)

        raise exc


@contextmanager
def simple_spinner(text: str = "Processing...", animation: str = "dots") -> None:
    if not text:
        text: str = "Processing..."
    assert isinstance(text, str), TypeError(
        f"Expected spinner text to be a string. Got type: ({type(text)})"
    )

    if not animation:
        animation: str = "dots"
    assert isinstance(animation, str), TypeError(
        f"Expected spinner animation to be a string. Got type: ({type(text)})"
    )

    try:
        _spinner = Spinner(animation, text=text)
    except Exception as exc:
        msg = Exception(f"Unhandled exception getting console spinner. Details: {exc}")
        log.error(msg)

        raise exc

    ## Display spinner
    try:
        with get_console() as console:
            with console.status(text, spinner=animation):
                yield console
    except Exception as exc:
        msg = Exception(
            f"Unhandled exception yielding spinner. Continuing without animation. Details: {exc}"
        )
        log.error(msg)

        pass

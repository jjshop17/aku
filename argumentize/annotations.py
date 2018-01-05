import argparse
import pathlib
from typing import Union

__all__ = [
    'boolean', 'Path',
]


def boolean(argument: Union[str, bool]) -> bool:
    if isinstance(argument, bool):
        return argument
    if argument.lower() in ['y', 'yes', 't', 'true', '1']:
        return True
    if argument.lower() in ['n', 'no', 'f', 'false', '0']:
        return False
    raise argparse.ArgumentTypeError(f'{argument} is not boolean type')


def Path(ensure: bool = False, mkdir: bool = False, expanduser: bool = False, absolute: bool = False):
    def generate_path(argument: Union[str, pathlib.Path]) -> pathlib.Path:
        if isinstance(argument, pathlib.Path):
            return argument
        path = pathlib.Path(argument)
        if ensure and not path.exists():
            if mkdir:
                path.mkdir(parents=True, exist_ok=True)
            raise argparse.ArgumentError(argument, 'does not exists')
        if expanduser:
            path = path.expanduser()
        if absolute:
            path = path.absolute()
        return path

    return generate_path
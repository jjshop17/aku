from abc import ABCMeta, abstractmethod
from typing import get_args, get_origin, Any

from aku.parse_fn import get_parse_fn
from argparse import ArgumentParser


class Tp(object, metaclass=ABCMeta):
    def __init__(self, origin, *args: 'Tp') -> None:
        super(Tp, self).__init__()
        self.origin = origin
        self.args = args

    def __class_getitem__(cls, tp):
        args = get_args(tp)
        origin = get_origin(tp)

        if origin is None and args == ():
            return PrimitiveTp(origin, *args)

        raise NotImplementedError(f'unsupported annotation {tp}')

    @property
    @abstractmethod
    def metavar(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_fn(self, option_string: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def add_argument(self, argument_parser: ArgumentParser, name: str, default: Any):
        raise NotImplementedError


class PrimitiveTp(Tp):
    @property
    def metavar(self) -> str:
        return f'{self.origin.__name__.lower()}'

    def parse_fn(self, option_string: str) -> Any:
        fn = get_parse_fn(self.origin)
        return fn(option_string.strip())

    def add_argument(self, argument_parser: ArgumentParser, name: str, default: Any):
        return argument_parser.add_argument(
            f'--{name}', required=True, help=f'{name}',
            type=self.parse_fn, metavar=self.metavar, default=default,
        )

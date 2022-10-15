import functools
import inspect
import sys
from argparse import Namespace, SUPPRESS
from typing import Type, List

from aku.parser import ArgumentParser
from aku.tp import AkuTp
from aku.utils import get_name, AKU_FN, AKU, AKU_DELAY


class Aku(object):
    def __init__(self, always_add_subparsers: bool = False) -> None:
        super(Aku, self).__init__()
        self.argument_parser = ArgumentParser()
        self._registry = []

        self.always_add_subparsers = always_add_subparsers

    def register(self, fn):
        self._registry.append(fn)
        return fn

    def _parse(self, args: List[str] = None, namespace: Namespace = None):
        assert len(self._registry) > 0, f'you are supposed to register at least one callable'

        if args is None:
            args = sys.argv[1:]

        argument_parser = self.argument_parser
        if not self.always_add_subparsers and len(self._registry) == 1:
            fn = self._registry[0]
            AkuTp[Type[fn]].add_argument(
                argument_parser=argument_parser,
                name=AKU, default=SUPPRESS,
                prefix=(), domain=(),
            )
        else:
            subparsers = argument_parser.add_subparsers()
            registry = {}
            for fn in self._registry:
                name = get_name(fn)
                if name not in registry:
                    registry[name] = (fn, subparsers.add_parser(name=name))
                else:
                    raise ValueError(f'{name} was already registered')

            if len(args) > 0 and args[0] in registry:
                arg, *args = args
                fn, argument_parser = registry[arg]
                AkuTp[Type[fn]].add_argument(
                    argument_parser=argument_parser,
                    name=AKU, default=SUPPRESS,
                    prefix=(), domain=(),
                )

        while True:
            namespace, args = argument_parser.parse_known_args(args=args, namespace=namespace)

            if len(argument_parser._registries.get(AKU_DELAY, {})) == 0:
                break
            else:
                names = []
                for name, delay in list(argument_parser._registries[AKU_DELAY].items()):
                    names.append(name)
                    delay()

                for name in names:
                    del argument_parser._registries[AKU_DELAY][name]

        for action in argument_parser._actions:
            if action.required is None:
                action.required = True
        return args, namespace

    def parse_args(self, args: List[str] = None, namespace: Namespace = None):
        args, namespace = self._parse(args=args, namespace=namespace)
        return self.argument_parser.parse_args(args=args, namespace=namespace)

    def parse_known_args(self, args: List[str] = None, namespace: Namespace = None):
        args, namespace = self._parse(args=args, namespace=namespace)
        return self.argument_parser.parse_known_args(args=args, namespace=namespace)

    def run(self, args: List[str] = None, namespace: Namespace = None):
        namespace = self.parse_args(args=args, namespace=namespace)
        if isinstance(namespace, Namespace):
            namespace = namespace.__dict__

        partial, literal = {}, {}
        for key, value in namespace.items():

            partial_co = partial
            literal_co = literal
            *names, key = key.split('.')
            for name in names:
                partial_co = partial_co.setdefault(name, {})
                literal_co = literal_co.setdefault(name, {})
            if key == AKU_FN:
                partial_co[key], literal_co[key] = value
            else:
                partial_co[key] = literal_co[key] = value

        def recur_partial(item):
            if isinstance(item, dict):
                if AKU_FN in item:
                    func = item.pop(AKU_FN)
                    kwargs = {k: recur_partial(v) for k, v in item.items()}
                    return functools.partial(func, **kwargs)
                else:
                    return {k: recur_partial(v) for k, v in item.items()}
            else:
                return item

        def recur_literal(item):
            out, keys, values = {}, [], []

            def recur(prefix, domain, v):
                nonlocal keys, values

                if isinstance(v, dict):
                    for x, y in v.items():
                        if x == AKU_FN:
                            out['-'.join((*prefix[1:], domain.removesuffix('_')))] = y
                        elif domain.endswith('_'):
                            recur(prefix + (domain.removesuffix('_'),), x, y)
                        else:
                            recur(prefix, x, y)
                else:
                    out['-'.join(prefix + (domain,))] = v

            recur((), '', item)
            return out

        partial = recur_partial(partial)

        assert len(partial) == 1, f'{len(partial)} != 1'
        for _, fn in partial.items():
            if inspect.getfullargspec(fn).varkw is None:
                return fn()
            else:
                return fn(**{AKU: recur_literal(literal)})

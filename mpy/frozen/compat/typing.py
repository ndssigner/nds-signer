# NDS-Signer - `typing` stub for MicroPython: annotations are never evaluated
# for behaviour, only imported by name.


class _Any:
    def __getitem__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self


Any = List = Dict = Tuple = Optional = Union = Type = Callable = Iterable = _Any()
Sequence = Set = Mapping = ClassVar = Literal = _Any()
TYPE_CHECKING = False


def cast(typ, value):
    return value

# NDS-Signer - minimal `dataclasses` for MicroPython.
#
# MicroPython discards class annotations, so field names cannot be discovered
# at runtime. tools/upy_transform.py rewrites every @dataclass class at build
# time and records its annotated fields, in order, in `__nds_fields__`; this
# decorator then builds __init__ / __repr__ / __eq__ from them, including the
# fields inherited from dataclass base classes.

MISSING = object()


class Field:
    def __init__(self, default=MISSING, default_factory=MISSING):
        self.default = default
        self.default_factory = default_factory


def field(default=MISSING, default_factory=MISSING, **kwargs):
    return Field(default, default_factory)


def _fields_of(cls):
    names = []
    for klass in reversed(cls.__mro__ if hasattr(cls, "__mro__") else _mro(cls)):
        for name in klass.__dict__.get("__nds_fields__", ()):
            if name not in names:
                names.append(name)
    return names


def _mro(cls):
    out = [cls]
    for base in cls.__bases__:
        for k in _mro(base):
            if k not in out:
                out.append(k)
    return out


def _default_for(cls, name):
    value = getattr(cls, name, MISSING)
    if isinstance(value, Field):
        if value.default_factory is not MISSING:
            return value.default_factory()
        return value.default
    return value


def _process(cls):
    names = _fields_of(cls)

    def __init__(self, *args, **kwargs):
        if len(args) > len(names):
            raise TypeError("too many positional arguments")
        for i, name in enumerate(names):
            if i < len(args):
                value = args[i]
                if name in kwargs:
                    raise TypeError("multiple values for " + name)
            elif name in kwargs:
                value = kwargs.pop(name)
            else:
                value = _default_for(type(self), name)
                if value is MISSING:
                    raise TypeError("missing argument: " + name)
            setattr(self, name, value)
        for name in kwargs:
            if name not in names:
                raise TypeError("unexpected argument: " + name)
        post_init = getattr(self, "__post_init__", None)
        if post_init is not None:
            post_init()

    def __repr__(self):
        return "%s(%s)" % (
            type(self).__name__,
            ", ".join("%s=%r" % (n, getattr(self, n, None)) for n in names),
        )

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return all(getattr(self, n, None) == getattr(other, n, None) for n in names)

    cls.__init__ = __init__
    if "__repr__" not in cls.__dict__:
        cls.__repr__ = __repr__
    if "__eq__" not in cls.__dict__:
        cls.__eq__ = __eq__
    cls.__dataclass_fields__ = names
    return cls


def dataclass(cls=None, **kwargs):
    if cls is None:
        return _process
    return _process(cls)


def fields(obj):
    return [Field() for _ in getattr(obj, "__dataclass_fields__", ())]

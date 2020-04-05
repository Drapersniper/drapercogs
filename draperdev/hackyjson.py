# -*- coding: utf-8 -*-
# Standard Library
import contextlib
import importlib
import json

MODULES = ("orjson", "ujson")

mainjson = None

__all__ = ["dump", "dumps", "load", "loads", "overload_stdlib"]

backup_dumps = None
backup_dump = None
backup_loads = None
backup_load = None


def import_modules():
    for name in MODULES:
        with contextlib.suppress(Exception):
            yield importlib.import_module(name)


MODULES_IMPORTS = list(import_modules())
MODULES_NAME = [module.__name__ for module in MODULES_IMPORTS]

for item in MODULES:
    with contextlib.suppress(ValueError):
        index = MODULES_NAME.index(item)
        mainjson = MODULES_IMPORTS[index]
        if mainjson:
            break
if mainjson is None:
    mainjson = json


def dumps(obj, **kw):
    output = mainjson.dumps(obj)
    with contextlib.suppress(AttributeError):
        output = output.decode("utf-8")
    return output


def loads(obj, **kw):
    return mainjson.loads(obj)


def dump(obj, fp, **kw):
    return fp.write(dumps(obj))


def load(fp, **kw):
    data = fp.read()
    return mainjson.loads(data)


def overload_stdlib():
    global backup_dumps, backup_dump, backup_loads, backup_load
    import json

    if not backup_dumps and json.dumps is not dumps:
        backup_dumps = json.dumps
        backup_dump = json.dump
        backup_loads = json.loads
        backup_load = json.load

    json.loads = loads
    json.load = load
    json.dumps = dumps
    json.dump = dump


def restore_stdlib():
    import json

    if backup_dumps and json.dumps is dumps:
        json.loads = backup_loads
        json.load = backup_load
        json.dumps = backup_dumps
        json.dump = backup_dump

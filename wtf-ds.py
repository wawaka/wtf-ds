#!/usr/bin/env python3

import sys
import collections

import colored

try:
    import ujson as json
except ImportError:
    import json


MAX_STRING_LENGTH = 36
MAX_VALUES_TO_SHOW = 3

KEY_COLOR = "green"
TYPE_COLOR = 129
STRING_COLOR = 88
NUMBER_COLOR = 150
COUNTER_COLOR = 14
BOOLEAN_COLOR = 11


def Ckey(key):
    return colored.stylize(key, colored.fg(KEY_COLOR))

def Ctype(t):
    return colored.stylize(t, colored.fg(TYPE_COLOR))

def Cstr(s):
    if len(s) > MAX_STRING_LENGTH:
        s = json.dumps(s[:MAX_STRING_LENGTH], ensure_ascii=False)
        prefix = colored.stylize(s[:-1], colored.fg(STRING_COLOR))
        suffix = colored.stylize('"', colored.fg(STRING_COLOR))
        return f"{prefix}…{suffix}"
    else:
        s = json.dumps(s, ensure_ascii=False)
        return colored.stylize(s, colored.fg(STRING_COLOR))

def Cnum(v):
    return colored.stylize(repr(v), colored.fg(NUMBER_COLOR))

def Ccnt(v):
    return colored.stylize(str(v), colored.fg(COUNTER_COLOR))

def Cbool(v):
    return colored.stylize("true" if v else "false", colored.fg(BOOLEAN_COLOR))



class BaseAggregator:
    TYPE_NAME = 'not_implemented'

    def add(self, v):
        self.TYPE_NAME = type(v).__name__
        return

    def __str__(self):
        return colored.stylize('NOT_IMPLEMENTED', colored.bg(9))

    def print(self, prefix):
        return


class DictAggregator(BaseAggregator):
    TYPE_NAME = 'map'

    def __init__(self):
        self.keys = collections.defaultdict(ValueAggregator)
        self.min_len = None
        self.max_len = None

    def add(self, obj):
        assert type(obj) is dict
        l = len(obj)
        self.min_len = l if self.min_len is None or l < self.min_len else self.min_len
        self.max_len = l if self.max_len is None or l > self.max_len else self.max_len

        for k, v in obj.items():
            self.keys[k].add(v)

    def __str__(self):
        cnt = f"{Ccnt(self.min_len)}" if self.min_len == self.max_len else f"{Ccnt(self.min_len)}…{Ccnt(self.max_len)}"
        return f"{cnt} keys"

    def print(self, prefix):
        for k, v in sorted(self.keys.items()):
            print(f"{prefix}.{Ckey(k)}: {v}")
            v.print(f"{prefix}.{Ckey(k)}")
            # v.print(f"{prefix}    ")


class ArrayAggregator(BaseAggregator):
    TYPE_NAME = 'array'

    def __init__(self):
        self.items = ValueAggregator()
        self.min_len = None
        self.max_len = None

    def add(self, a):
        assert type(a) is list
        self.min_len = len(a) if self.min_len is None else min(self.min_len, len(a))
        self.max_len = len(a) if self.max_len is None else max(self.max_len, len(a))
        for v in a:
            self.items.add(v)

    def __str__(self):
        cnt = f"{Ccnt(self.min_len)}" if self.min_len == self.max_len else f"{Ccnt(self.min_len)}…{Ccnt(self.max_len)}"
        return f"{cnt} items"

    def print(self, prefix):
        print(f"{prefix}[]: {self.items}")
        self.items.print(f"{prefix}[]")


class StringAggregator(BaseAggregator):
    TYPE_NAME = 'str'

    def __init__(self):
        self.values = []

    def add(self, value):
        assert type(value) is str
        self.values.append(value)

    def __str__(self):
        d = collections.defaultdict(int)
        for v in self.values:
            d[v] += 1

        if len(d) == 1:
            for v, c in d.items():
                return Cstr(v)

        sorted_items = sorted(d.items(), key=lambda x: (-x[1], x[0]))
        text_values = [f"{Ccnt(c)}×{Cstr(v)}" for v, c in sorted_items[:MAX_VALUES_TO_SHOW]]

        other_c = sum(c for v, c in sorted_items[MAX_VALUES_TO_SHOW:])
        if other_c == 0:
            return ", ".join(text_values)

        text_values.append(f"{Ccnt(other_c)}×…")
        return f"{Ccnt(len(d))}←|{Cstr(min(self.values))}…{Cstr(max(self.values))}|: {', '.join(text_values)}"


class NumberAggregator(BaseAggregator):
    TYPE_NAME = 'number'

    def __init__(self):
        self.values = []

    def add(self, value):
        assert type(value) is int or type(value) is float
        self.values.append(value)

    def __str__(self):
        d = collections.defaultdict(int)
        for v in self.values:
            d[v] += 1

        if len(d) == 1:
            for v, c in d.items():
                return Cnum(v)

        sorted_items = sorted(d.items(), key=lambda x: (-x[1], x[0]))
        text_values = [f"{Ccnt(c)}×{Cnum(v)}" for v, c in sorted_items[:MAX_VALUES_TO_SHOW]]

        other_c = sum(c for v, c in sorted_items[MAX_VALUES_TO_SHOW:])
        if other_c == 0:
            return ", ".join(text_values)

        text_values.append(f"{Ccnt(other_c)}×…")
        return f"{Ccnt(len(d))}←|{Cnum(min(self.values))}…{Cnum(max(self.values))}|: {', '.join(text_values)}"


class IntegerAggregator(NumberAggregator):
    TYPE_NAME = 'int'


class FloatAggregator(NumberAggregator):
    TYPE_NAME = 'float'


class BooleanAggregator(BaseAggregator):
    TYPE_NAME = 'bool'

    def __init__(self):
        self.true = 0
        self.false = 0

    def add(self, value):
        assert type(value) is bool
        if value:
            self.true += 1
        else:
            self.false += 1

    def __str__(self):
        if self.false == 0:
            return f"{Cbool(True)}"
        if self.true == 0:
            return f"{Cbool(False)}"
        return f"{Ccnt(self.false)}×{Cbool(False)}, {Ccnt(self.true)}×{Cbool(True)}"


class NullAggregator(BaseAggregator):
    TYPE_NAME = 'null'

    def add(self, value):
        assert value is None

    def __str__(self):
        return "null"


class ValueAggregator(BaseAggregator):
    AGGREGATORS = {
        'dict': DictAggregator,
        'list': ArrayAggregator,
        'int': IntegerAggregator,
        'float': FloatAggregator,
        'str': StringAggregator,
        'bool': BooleanAggregator,
        'NoneType': NullAggregator,
    }

    def __init__(self):
        self.by_type = {}

    def add(self, v):
        tn = type(v).__name__

        try:
            agg = self.by_type[tn]
        except KeyError:
            agg = self.by_type[tn] = self.AGGREGATORS[tn]()
            agg.cnt = 0

        agg.add(v)
        agg.cnt += 1

    def __str__(self):
        return ", ".join(f"{Ccnt(agg.cnt)}×{Ctype(agg.TYPE_NAME)}({agg})" for tn, agg in sorted(self.by_type.items(), key=lambda x: (x[1], x[0])))

    def print(self, prefix=''):
        for t, agg in self.by_type.items():
            agg.print(prefix)


def main():
    res = collections.defaultdict(IntegerAggregator)

    v = ValueAggregator()

    for line in sys.stdin:
        obj = json.loads(line)
        v.add(obj)

    v.print()


if __name__ == "__main__":
    # import cProfile
    # cProfile.run('main()')
    main()


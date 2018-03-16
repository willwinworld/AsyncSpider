from abc import ABCMeta
from collections import Mapping, MutableMapping, KeysView

__all__ = ['DefinedKeysDictMeta', 'DefinedKeysDict', 'FrozenDict']


class DefinedKeysDictMeta(ABCMeta):
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        keys = getattr(cls, '_keys')
        setattr(cls, '_key_num', len(keys))
        setattr(cls, '_key2index', {k: i for i, k in enumerate(keys)})


class DefinedKeysDict(MutableMapping, metaclass=DefinedKeysDictMeta):
    # has defined keys
    # keys and values are ordered

    __slots__ = ('_values',)
    __marker = object()

    _keys = ()  # subclass must define this
    _key_num = 0
    _key2index = {}

    def __init__(self, **kwargs):
        self._values = [self.__marker] * self._key_num
        self.update(**kwargs)

    def __getitem__(self, key):
        if key not in self._keys:
            raise KeyError(key)
        v = self._values[self._key2index[key]]
        if v is self.__marker:
            raise KeyError(key)
        return v

    def __setitem__(self, key, value):
        if key not in self._keys:
            raise KeyError(key)
        self._values[self._key2index[key]] = value

    def __delitem__(self, key):
        if key not in self._keys:
            raise KeyError(key)
        self._values[self._key2index[key]] = self.__marker

    def __iter__(self):
        for i in range(self._key_num):
            if self._values[i] is not self.__marker:
                yield self._keys[i]

    def __len__(self):
        return self._key_num

    def __str__(self):
        return '{' + ', '.join(('{!r}: {!r}'.format(k, v) for k, v in self.items())) + '}'

    def pop(self, key, default=__marker):
        try:
            v = self[key]
        except KeyError:
            if default is self.__marker:
                raise
            return default
        else:
            del self[key]
            return v

    def clear(self):
        for i in range(self._key_num):
            self._values[i] = self.__marker

    def copy(self):
        return self.__class__(**self)

    @classmethod
    def all_keys(cls):
        return KeysView(cls._keys)


class FrozenDict(Mapping):
    # https://stackoverflow.com/questions/2703599/what-would-a-frozen-dict-be
    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # It would have been simpler and maybe more obvious to
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of
        # n we are going to run into, but sometimes it's hard to resist the
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            self._hash = 0
            for pair in self.items():
                self._hash ^= hash(pair)
        return self._hash

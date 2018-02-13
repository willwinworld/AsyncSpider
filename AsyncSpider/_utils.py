from copy import copy


class Storage:
    __slots__ = ()

    def __init__(self):
        for f in self.keys():
            self[f] = None

    def copy(self, **kwargs):
        new_instance = copy(self)
        new_instance.update(**kwargs)
        return new_instance

    def update(self, **kwargs):
        for k, v in kwargs.items():
            self[k] = v

    def __iter__(self):
        return self.values()

    def keys(self):
        return (f for f in self.__slots__)

    def values(self):
        return (self[f] for f in self.keys())

    def items(self):
        return (item for item in zip(self.keys(), self.values()))

    def as_dict(self):
        return dict(self.items())

    def as_list(self):
        return list(self.values())

    def __getitem__(self, field):
        try:
            return getattr(self, field)
        except AttributeError:
            raise KeyError(f'{self} has not field {repr(field)}.')

    def __setitem__(self, field, value):
        try:
            setattr(self, field, value)
        except AttributeError:
            raise KeyError(f'{self} has not field {repr(field)}.')

    def __str__(self):
        # dict view
        return str(self.as_dict())

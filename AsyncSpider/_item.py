from ._utils import Storage

__all__ = ['Field', 'Item']


class Field(dict):
    def __init__(self, default=None, **metadata):
        dict.__init__(self, default=default, **metadata)


class ItemMeta(type):
    def __new__(mcs, name, bases, namespace: dict):
        item_class = type.__new__(mcs, name, bases, namespace)

        fields = getattr(item_class, 'fields')
        for k, v in namespace.items():
            if isinstance(v, Field):
                fields[k] = v
                delattr(item_class, k)

        return item_class


class Item(Storage, metaclass=ItemMeta):
    fields = {}

    def __init__(self, **kwargs):
        super().__init__()
        for k in self.fields.keys():
            self.setdefault(k, self.fields[k].get('default'))
        self.update(**kwargs)

    def __setitem__(self, key, value):
        if key in self.fields.keys():
            super().__setitem__(key, value)
        else:
            raise KeyError('{} is not in fields.'.format(key))

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise KeyError('{} is not in fields.'.format(key))

    def update(self, **kwargs):
        for k, v in kwargs.items():
            self[k] = v

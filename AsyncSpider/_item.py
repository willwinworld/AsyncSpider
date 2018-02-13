from ._utils import Storage


class Field(dict):
    def __init__(self, default=None, **metadata):
        dict.__init__(self, default=default, **metadata)


class ItemMeta(type):
    def __new__(mcs, name, bases, namespace: dict):
        item_class = type.__new__(mcs, name, bases, namespace)

        slots = []
        fields = getattr(item_class, 'fields')
        for k, v in namespace.items():
            if isinstance(v, Field):
                fields[k] = v
                delattr(item_class, k)
                slots.append(k)
        item_class.__slots__ = tuple(slots)
        return item_class


class Item(Storage, metaclass=ItemMeta):
    fields = {}

    def __init__(self, **kwargs):
        super().__init__()
        for k, f in self.fields.items():
            self[k] = f.get('default')
        self.update(**kwargs)

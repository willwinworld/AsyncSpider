from .data import DefinedKeysDictMeta, DefinedKeysDict

__all__ = ['Field', 'ItemMeta', 'Item']


class Field(dict):
    def __init__(self, **metadata):
        dict.__init__(self, **metadata)


class ItemMeta(DefinedKeysDictMeta):
    def __new__(mcs, name, bases, namespace: dict):
        namespace.setdefault('fields', {})
        return super().__new__(mcs, name, bases, namespace)

    def __init__(cls, name, bases, namespace):
        fields = namespace['fields']

        old_fields = getattr(super(cls, cls), 'fields', None)
        if old_fields is not None:
            fields.update(old_fields.items())

        new_fields_items = (i for i in namespace.items() if isinstance(i[1], Field))
        fields.update(new_fields_items)

        setattr(cls, '_keys', tuple(fields.keys()))
        super(ItemMeta, cls).__init__(name, bases, namespace)


class Item(DefinedKeysDict, metaclass=ItemMeta):
    # keys' order is lost due to function in ItemMeta which collects fields by dict
    """ Usage:
    class MyItem(Item):
        name=Field(default='')
        age=Field()
        alive=Field(default=True)

    MyItem.fields[key] -> Field instance which contains metadata
    """

    fields = {}

    def __init__(self, **kwargs):
        for k in self._keys:
            try:
                d = self.fields[k]['default']
            except KeyError:
                pass
            else:
                kwargs.setdefault(k, d)
        super().__init__(**kwargs)

    def __str__(self):
        return ''.join(('<', self.__class__.__name__, ' ', super().__repr__(), '>'))

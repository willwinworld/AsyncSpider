from AsyncSpider import Item, Field


class TestItem(Item):
    title = Field(type=str)
    content = Field(type=str)
    is_valid = Field(type=bool, default=False)
    count = Field(type=int, default=0)


if __name__ == '__main__':
    t = TestItem(count=1)
    print(f't: {t}')
    t['title'] = 'Philosophy'
    t['content'] = ['deep dark fantasy']
    print(f't: {t}')
    t2 = t.copy()
    t2['title'] = 'Van'
    print(t.pop('title'))
    print(f't: {t!r}')
    print(f't2: {t2}')
    print(TestItem.fields)
    print(TestItem.all_keys())
    print(t.title)
    print(t.title is t2.title)

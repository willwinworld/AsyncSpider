import codecs
import json
import aiohttp
import chardet

__all__ = ['Request', 'Response']


class Request(dict):
    # data class for request params
    def __init__(self, method, url, **kwargs):
        dict.__init__(self, method=method, url=url, **kwargs)


class Response:
    # data class for client response

    __slots__ = ('_method', '_url', '_status', '_content', '_encoding', '_headers', '_cookies', '_host', '_history')

    @classmethod
    async def from_client_response(cls, resp: aiohttp.ClientResponse):
        return cls(method=resp.method, url=str(resp.url),
                   status=resp.status, content=await resp.read(),
                   headers=resp.headers, cookies=resp.cookies,
                   host=resp.host, history=resp.history)

    def __init__(self, method, url, status, content, headers, cookies, host, history):
        self._method = method
        self._url = url
        self._status = status
        self._content = content
        self._encoding = None
        self._headers = headers
        self._cookies = cookies
        self._host = host
        self._history = history

    @property
    def method(self):
        return self._method

    @property
    def url(self):
        return self._url

    @property
    def status(self):
        return self._status

    @property
    def content(self):
        return self._content

    @property
    def headers(self):
        return self._headers

    @property
    def cookies(self):
        return self._cookies

    @property
    def host(self):
        return self._host

    @property
    def history(self):
        return self._history

    @property
    def encoding(self) -> str:
        encoding = self._encoding
        if encoding:
            return encoding

        # copied from aiohttp
        ctype = self.headers.get(aiohttp.hdrs.CONTENT_TYPE, '').lower()
        mimetype = aiohttp.helpers.parse_mimetype(ctype)

        encoding = mimetype.parameters.get('charset')
        if encoding:
            try:
                codecs.lookup(encoding)
            except LookupError:
                encoding = None
        if not encoding:
            if mimetype.type == 'application' and mimetype.subtype == 'json':
                # RFC 7159 states that the default encoding is UTF-8.
                encoding = 'utf-8'
            else:
                encoding = chardet.detect(self._content)['encoding']
        if not encoding:
            encoding = 'utf-8'

        self._encoding = encoding
        return encoding

    @encoding.setter
    def encoding(self, value):
        self._encoding = value

    def text(self, encoding=None, errors='strict') -> str:
        if encoding is None:
            encoding = self.encoding
        else:
            self.encoding = encoding
        return self.content.decode(encoding, errors=errors)

    def json(self, **kwargs):
        return json.loads(self.text(), **kwargs)

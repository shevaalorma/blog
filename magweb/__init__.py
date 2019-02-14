from wsgiref.simple_server import make_server
from webob import Request, Response, exc
from webob.dec import wsgify
import re


class Dictobj:
    def __init__(self, d: dict):
        if not isinstance(d, dict):
            self.__dict__['_dict'] = {}
        else:
            self.__dict__['_dict'] = d

    def __setattr__(self, key, value):
        return NotImplementedError

    def __getattr__(self, item):
        try:
            return self.__dict__['_dict']
        except KeyError:
            raise AttributeError('Attribute {} Not Found'.format(item))


class Context(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError('Attribute {} Not Found'.format(item))

    def __setattr__(self, key, value):
        self[key] = value


class NestedContext(Context):
    def __init__(self, globalcontext: Context = None):
        super().__init__()
        self.relate(globalcontext)

    def relate(self, globalcontext: Context = None):
        self.globalcontext = globalcontext

    def __getattr__(self, item):
        if item in self.keys():
            return self[item]
        return self.globalcontext[item]


class _Router:
    TYPEPATTERN = {
        'str': r'[^/]+',
        'word': r'\w+',
        'int': r'[+-]?\d+',
        'float': r'[+-]\d+\.\d',
        'any': r'.+'
    }

    TYPECAST = {
        'str': str,
        'word': str,
        'int': int,
        'float': float,
        'any': str
    }

    KVPATTERN = re.compile(r'/({[^{}:]+:?[^{}:]*})')

    # {name:str} =>'>P<name>nametype'
    def _transfrom(self, kv: str):
        name, _, type = kv.strip('/{}').partition(':')
        return '?P<{}>{}'.format(name, self.TYPEPATTERN.get(type, '\w+')), name, self.TYPECAST.get(type, str)

    def _parse(self, src: str):
        start = 0
        translator = {}
        res = ''
        # 匹配分组下传来的{name:str}
        while True:
            matcher = self.KVPATTERN.search(src, start)
            if matcher:
                res += matcher.string[start:matcher.start()]
                tmp = self._transfrom(matcher.string[matcher.start():matcher.end()])
                res += tmp[0]
                translator[tmp[1]] = tmp[2]
                start = matcher.end()
            else:
                break

        if res:
            return res, translator
        else:
            return src, translator

    def __init__(self, prefix: str = ''):
        self.__prefix = prefix.rstrip('/\\')
        self.__routetables = []

        # 拦截器
        self.pre_interceptor = []
        self.post_interceptor = []

        # 上下文
        self.ctx = NestedContext()  # 未关联全局，注册时使用

    @property
    def prefix(self):
        return self.__prefix

    # 拦截器函数注册
    def register_preinterceptor(self, fn):
        self.pre_interceptor.append(fn)
        return fn

    def register_postinterptor(self, fn):
        self.post_interceptor.append(fn)
        return fn

    def route(self, rule, *method):  # 用户输入规则转换为pattern
        def wrapper(handler):
            pattern, translator = self._parse(rule)
            self.__routetables.append((method, re.compile(pattern), translator, handler))
            return handler

        return wrapper

    def get(cls, pattern):
        return cls.route(pattern, 'GET')

    def post(cls, pattern):
        return cls.route(pattern, 'POST')

    def head(cls, pattern):
        return cls.route(pattern, 'HEAD')

    def match(self, request: Request):
        # 去除请求路径prefix
        if not request.path.startswith(self.__prefix):
            return None

        # 依次执行拦截请求
        for fn in self.pre_interceptor:
            request = fn(self.ctx, request)

        # 遍历routetables
        for methods, pattern, translator, handler in self.__routetables:
            if not methods or request.method.upper() in methods:
                matcher = pattern.match(request.path.replace(self.__prefix, '', 1))
                if matcher:
                    newdict = {}
                    # request.args = matcher.group()
                    # request.kwargs = Dictobj(matcher.groupdict())
                    for k, v in matcher.groupdict().items():
                        newdict[k] = translator[k](v)
                    request.vars = Dictobj(newdict)
                    # return handler(request)
                    response = handler(self.ctx, request)

                    for fn in self.post_interceptor:
                        response = fn(self.ctx, request, response)

                    return response
                # 匹配不上返回None


class MagWeb:
    # 类属性方式把类暴露出去
    Router = _Router
    Request = Request
    Response = Response

    ctx = Context()

    def __init__(self, **kwargs):
        # 创建上下文对象，共享信息
        self.ctx.app = self
        for k, v in kwargs:
            self.ctx[k] = v

    ROUTES = []

    # 拦截器
    PRE_INTERCEPTOR = []
    POST_INTERCEPTOR = []

    # 拦截器注册函数
    @classmethod
    def register_preinterceptor(cls, fn):
        cls.PRE_INTERCEPTOR.append(fn)
        return fn

    @classmethod
    def register_postinterceptor(cls, fn):
        cls.POST_INTERCEPTOR.append(fn)
        return fn

    @classmethod
    def register(cls, router: _Router):
        # 为Router实例注入全局上下文
        router.ctx.relate(cls.ctx)
        router.ctx.router = router
        cls.ROUTES.append(router)

    @wsgify
    def __call__(self, request: Request) -> Response:
        # 全局拦截请求
        for fn in self.PRE_INTERCEPTOR:
            request = fn(self.ctx, request)

        # 遍历ROUTERS，调用Router实例的match方法，看谁匹配
        for route in self.ROUTES:
            response = route.match(request)

            # 全局拦截响应
            for fn in self.POST_INTERCEPTOR:
                response = fn(self.ctx, request, response)

            if response:  # 匹配非None的Router对象
                return response  # 匹配立即返回
        raise exc.HTTPNotFound('<h1>你的页面被狗吃了！</h1>')

        @classmethod
        def extend(cls, name, ext):
            cls.ctx[name] = ext



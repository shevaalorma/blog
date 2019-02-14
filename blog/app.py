from wsgiref.simple_server import make_server
from magweb import MagWeb
from blog import config
from blog.handler.user import user_router

if __name__ == '__main__':

    application = MagWeb()

    # 路由注册到application
    application.register(user_router)

    server = make_server(config.WSIP, config.WSPORT, application)
    print('wait for connection...')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()

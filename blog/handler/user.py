from magweb import MagWeb
from ..model import User, session
from ..util import jsonify
import jwt
from .. import config
from webob import exc
import bcrypt

# 用户路由，要注册
user_router = MagWeb.Router(prefix='/user')

def gen_token(user_id):
    return jwt.encode({'user_id':user_id},config.AUTH_SECRET,algorithm='HS256').decode()

# 注册
@user_router.post('/reg')
def reg(ctx, request: MagWeb.Request):
    payload = request.json
    email = payload['email']
    if session.query(User).filter(User.email==email).first():
        raise exc.HTTPConflict('{} already exists '.format(email))
    user = User()

    try:
        user.name = payload.get('name')
        user.email = payload['email']
        user.password=bcrypt.hashpw(payload['password'].encode(),bcrypt.gensalt())
    except Exception as e:
        print(e)
        exc.HTTPBadRequest

    session.add(user)

    try:
        session.commit()
        print(gen_token(user.id),type(gen_token(user.id)))
        return jsonify(token = gen_token(user.id))
    except:
        session.rollback()
        raise exc.HTTPServerError


# 登陆
@user_router.post('/login')
def login(ctx, reuest: MagWeb.Request):
    print(reuest)

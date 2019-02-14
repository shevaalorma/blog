from magweb import MagWeb
from ..model import User, session
from ..util import jsonify
import jwt
from .. import config
from webob import exc
import bcrypt
import datetime

# 用户路由，要注册
user_router = MagWeb.Router(prefix='/user')

def gen_token(user_id):
    return jwt.encode({
        'user_id':user_id,
        'timestamp':int(datetime.datetime.now().timestamp())
    },config.AUTH_SECRET,algorithm='HS256').decode()

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
    payload = reuest.json
    email = payload['email']
    user = session.query(User).filter(User.email==email).first()
    if user and bcrypt.checkpw(payload.get('password').encode(),user.password.encode()):
        return jsonify(user={
            'id':user.id,
            'name':user.password,
            'email':user.email
        }),gen_token(user.id)
    else:
        exc.HTTPUnauthorized()

def authenticate(fn):
    def warpper(ctx,request:MagWeb.Request):
        try:
            jwtstr = request.headers.get('Jwt')
            print(jwtstr)
            payload = jwt.decode(jwtstr,config.AUTH_SECRET,algorithms=['HS256'])
            if (datetime.datetime.now().timestamp()-payload.get('timestamp',0))>config.AUTH_EXPIRE:
                raise exc.HTTPUnauthorized()
            user = session.query(User).filter(User.id == payload('user_id',-1)).first()
            if (user is None):
                raise exc.HTTPUnauthorized()
            request.user =user
        except Exception as e:
            print(e)
            raise exc.HTTPUnauthorized()
        return fn(ctx,request)
    return warpper


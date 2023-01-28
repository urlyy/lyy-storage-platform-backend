import datetime

import jwt

import time

key = "lyyyyds"

def create_jwt(user_id: int) -> str:
    data = {
        # 公共声明
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),  # 过期时间
        'iat': datetime.datetime.utcnow(),  # 开始时间
        'iss': 'lyy',  # (Issuer) 指明此token的签发者
        # 私有声明
        'data': {
            'user_id': user_id,
            'create_time': time.time()
        }
    }
    token = jwt.encode(data, key, algorithm='HS256')
    return token


def get_id(token: str) -> int|None:
    try:
        claim = jwt.decode(token, key, issuer='lyy', algorithms=['HS256'])
        user_id = int(claim.get("data").get("user_id"))
        return user_id
    except:
        return None
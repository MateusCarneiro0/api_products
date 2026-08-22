from flask import request, jsonify
from functools import wraps
import jwt
import os
from utils.datetime_utils import calculate_now, calculate_date_of_now

algorithm = os.getenv("ALGORITHM", "HS256")
secret_key_jwt = os.getenv("JWT_SECRET_KEY_APP", "COLOQUE UMA CHAVE IMEDIATAMENTE")


class NotFoundTokenError(Exception):
    def __init__(self, message):
        self.message = message


def get_identify_token():
    authorization = request.headers.get("Authorization")
    if authorization is None:
        raise NotFoundTokenError("Not found a token")
    token = authorization.split(" ")[1]
    return token


def create_access_token(identify: str):
    now = calculate_now()

    refresh_token_expire = calculate_date_of_now(days=7)

    acess_token_expire = calculate_date_of_now(hours=8)

    acess_token_payload = {
        "identify": identify,
        "exp": acess_token_expire,
        "iat": now,
        "type": "acess",
    }
    refresh_token_payload = {
        "sub": identify,
        "type": "refresh",
        "exp": refresh_token_expire,
        "iat": now,
    }

    acess_token = jwt.encode(
        key=secret_key_jwt, payload=acess_token_payload, algorithm=algorithm
    )
    
    refresh_token = jwt.encode(
        key=secret_key_jwt, payload=refresh_token_payload, algorithm=algorithm
    )

    return acess_token, refresh_token


def required_authentication(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        try:
            token = get_identify_token()

            data_decoded = jwt.decode(
                jwt=token,  # type:ignore
                key=secret_key_jwt,
                algorithms=[algorithm],
            )
            return func(*args, **kwargs, id=data_decoded["identify"])
        except NotFoundTokenError as err:
            return jsonify({"error": str(err.message), "type": "inexistent"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Expired token", "type_error": "expired"}), 422

        except jwt.DecodeError as err:
            return jsonify(
                {"error": "Invalid Token", "type_error": "invalid", "details": str(err)}
            ), 422

    return wrapper

def refresh_route(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        try:
            refresh_token = None
        except Exception as e:
            pass

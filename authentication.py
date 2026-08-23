from flask import jsonify
from functools import wraps
import jwt
from utils.datetime_utils import calculate_now, calculate_date_of_now
from utils.jwt_utils import (
    get_identify_token,
    decode_jwt,
    NotFoundTokenError,
    secret_key_jwt,
    algorithm,
    InvalidToken,
)
from redis_manager import put_in_redis, exists_in_redis


def create_access_token(identify: str):

    now = calculate_now()

    refresh_token_expire = calculate_date_of_now(days=7)

    acess_token_expire = calculate_date_of_now(hours=1)

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
            if exists_in_redis(token):
                raise InvalidToken("The token is invalid")
            data_decoded = decode_jwt(token=token, key_payload="identify")

            return func(*args, **kwargs, id=data_decoded)

        except NotFoundTokenError as err:
            return jsonify({"error": str(err.message), "type": "inexistent"}), 422

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Expired token", "type_error": "expired"}), 401

        except InvalidToken as err:
            return jsonify(
                {"error": "Invalid Token", "type_error": "invalid", "details": str(err)}
            ), 422

        except jwt.DecodeError as err:
            return jsonify(
                {"error": "Invalid Token", "type_error": "invalid", "details": str(err)}
            ), 422

    return wrapper


def refresh_route(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            refresh_token = get_identify_token()
            if exists_in_redis(refresh_token):
                raise InvalidToken("The token is invalid")
            identify = decode_jwt(token=refresh_token, key_payload="sub")
            if identify:
                put_in_redis(refresh_token, False)
                return func(*args, **kwargs, identify=identify)
            else:
                raise Exception("No identify")
        except NotFoundTokenError as err:
            return jsonify({"error": str(err.message), "type": "inexistent"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Expired token", "type_error": "expired"}), 422
        except InvalidToken as err:
            return jsonify(
                {"error": "Invalid Token", "type_error": "invalid", "details": str(err)}
            ), 422

        except jwt.DecodeError as err:
            return jsonify(
                {"error": "Invalid Token", "type_error": "invalid", "details": str(err)}
            ), 422
        except KeyError as err:
            return jsonify(
                {
                    "error": "Invalid key in payload",
                    "type_error": "key",
                    "details": str(err),
                }
            ), 500
        except Exception as err:
            return jsonify(
                {
                    "error": "None token",
                    "type_error": "none",
                    "details": str(err),
                }
            ), 422

    return wrapper

import jwt
from flask import request
import os
from dotenv import load_dotenv

load_dotenv()

secret_key_jwt = os.getenv("JWT_SECRET_KEY_APP", "COLOQUE UMA CHAVE IMEDIATAMENTE")
algorithm = os.getenv("ALGORITHM", "HS256")


class NotFoundTokenError(Exception):
    def __init__(self, message):
        self.message = message


class InvalidToken(Exception):
    def __init__(self, message):
        self.message = message


def get_identify_token(is_acess_token=True):
    cookies_token = request.cookies.get(
        f"{'acess_token' if is_acess_token else 'refresh_token'}"
    )
    if cookies_token:
        return cookies_token
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise NotFoundTokenError("Not found a token")
    token = authorization.split(" ")[1].strip()
    return token


def decode_jwt(token, key_payload=""):
    payload = jwt.decode(jwt=token, key=secret_key_jwt, algorithms=[algorithm])
    return payload[key_payload] if key_payload else payload

def get_cookies_refresh():
    acess_token_cookie = request.cookies.get("acess_token")
    refresh_token_cookie = request.cookies.get("refresh_token")
    if(acess_token_cookie == None or refresh_token_cookie == None):
        tokens = request.get_json()
        return tokens
    return {"acess_token":acess_token_cookie,"refresh_token":refresh_token_cookie}

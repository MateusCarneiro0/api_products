from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash

import uuid

from ..db.models.User import User
from ..db import db

from ..auth.authentication import create_access_token

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/users")


@auth_bp.route("/createnewuser", methods=["POST"])
def createNewUser():
    dados = request.get_json()
    if not dados or "user" not in dados or "password" not in dados:
        return jsonify({"error": "O valor não preenche todos os dados"}), 401
    if len(dados["user"]) > 100 or len(dados["password"]) > 100:
        return jsonify({"error": "many characters", "manyCharacters": True}), 200

    hasRepeated = User.query.filter(User.user == dados["user"]).first()
    if not hasRepeated is None:
        return jsonify({"error": "repeat usernames", "hasRepeated": True}), 200
    userId = uuid.uuid4().hex
    new_password = generate_password_hash(dados["password"])
    acess_token, refresh_token = create_access_token(identify=userId)
    new_user = User(
        user=dados["user"],  # type:ignore
        password=new_password,  # type:ignore
        id=userId,  # type:ignore
        cart=[],  # type:ignore
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        response = make_response(
            jsonify(
                {
                    "user": dados["user"],
                    "cart": [],
                }
            ),
            201,
        )
        response.set_cookie(
            key="acess_token",
            value=acess_token,
            max_age=3600,
            secure=True,
            httponly=True,
            samesite="None",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=3600 * 24 * 7,
            secure=True,
            httponly=True,
            samesite="None",
        )

        response.set_cookie(
            key="is_logged",
            value="true",
            max_age=3600 * 24 * 7,
            secure=True,
            httponly=False,
            samesite="None",
        )

        return response

    except Exception as e:
        db.session.rollback()

        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def loginUser():
    try:
        username = request.get_json()["username"]
        password = request.get_json()["password"]
        selectedUser = User.query.filter(username == User.user).first()
        if selectedUser is None or not check_password_hash(
            selectedUser.password, password
        ):
            return jsonify({"auth": False, "message": "Usuário não encontrado"}), 200

        acess_token, refresh_token = create_access_token(selectedUser.id)
        response = make_response(
            jsonify(
                {
                    "auth": True,
                    "user": selectedUser.user,
                    "cart": selectedUser.cart,
                }
            ),
            201,
        )
        response.set_cookie(
            key="acess_token",
            value=acess_token,
            max_age=3600,
            secure=True,
            httponly=True,
            samesite="None",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=3600 * 24 * 7,
            secure=True,
            httponly=True,
            samesite="None",
        )
        response.set_cookie(
            key="is_logged",
            value="true",
            max_age=3600 * 24 * 7,
            secure=True,
            httponly=False,
            samesite="None",
        )
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

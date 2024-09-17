# Online Support Ticket Application
# Tushar Supe : 21f1003637
# Vaidehi Agarwal: 21f1003880
# File Info: This file contains Login/Logout/Register API.
# --------------------  Imports for the integration project  -------------------
import requests
api_key = '03c496ad7cec70da001b7385eb3f0b1d178fed0d2c0911965dfc42b29880d28b'
api_username = '21f1006677'
headers = {
    'Api-Key': api_key,
    'Api-Username': api_username,
    'Content-Type': 'application/json',
}

# --------------------  Imports  --------------------

import os
from flask import Blueprint, request
from flask import jsonify
from flask_restful import Api, Resource
from application.logger import logger
from application.responses import *
from application.models import Auth, Ots_discourse_userid_map
from application.globals import TOKEN_VALIDITY, BACKEND_ROOT_PATH
from application.database import db
import time
from application.views.user_utils import UserUtils
from application.common_utils import (
    token_required,
    admin_required,
    convert_img_to_base64,
    is_img_path_valid,
)

# --------------------  Code  --------------------


class AuthUtils(UserUtils):
    def __init__(self, user_id=None):
        self.user_id = user_id

    def update_auth_table(self, details: dict):
        """
        Usage
        -----
        Update auth table while logging in and creating new account

        Parameters
        ----------
        details : dict with user details

        Returns
        -------
        updated user object

        """
        if details["operation"] == "login":
            user = Auth.query.filter_by(email=details["email"]).first()
            user.web_token = details["web_token"]
            user.is_logged = True
            user.token_created_on = int(time.time())
            user.token_expiry_on = details["token_expiry_on"]
            db.session.commit()

        if details["operation"] == "register":
            user = Auth(
                user_id=details["user_id"],
                email=details["email"],
                password=details["password"],
                role=details["role"],
                first_name=details["first_name"],
                last_name=details["last_name"],
            )
            db.session.add(user)
            db.session.commit()

        if details["operation"] == "verify_user":
            user = Auth.query.filter_by(user_id=details["user_id"]).first()
            user.is_verified = True
            db.session.commit()

        if details["operation"] == "delete_user":
            user = Auth.query.filter_by(user_id=details["user_id"]).first()
            db.session.delete(user)
            db.session.commit()

        return user


auth_bp = Blueprint("auth_bp", __name__)
auth_api = Api(auth_bp)
auth_utils = AuthUtils()


class Login(Resource):
    def post(self):
        """
        Usage
        -----
        For the user login page. It checks user data and raise appropriate error
        if required. Else it generates user token and returns it.

        Parameters
        ----------
        form data sent with request
        data format {'email':'', 'password':''}

        Returns
        -------
        User web token

        """
        form = {}

        # get form data
        try:
            form = request.get_json()
            email = form.get("email", "")
            password = form.get("password", "")
        except Exception as e:
            logger.error(f"Login->post : Error occured while getting form data : {e}")
            raise InternalServerError
        else:
            if auth_utils.is_blank(email) or auth_utils.is_blank(password):
                raise BadRequest(status_msg=f"Email or Password is empty")

            details = {"email": email, "password": password, "operation": "login"}

            # verify form data
            if auth_utils.is_email_valid(email) and auth_utils.is_password_valid(
                password
            ):
                # check if user exists

                user = Auth.query.filter_by(email=email).first()
                if user:
                    # user exists
                    user_id = user.user_id

                    if password == user.password:
                        # password is correct so log in user if user is verified
                        if user.is_verified or user.role == "admin":
                            #  generate token
                            token_expiry_on = int(int(time.time()) + TOKEN_VALIDITY)
                            web_token = auth_utils.generate_web_token(
                                email, token_expiry_on
                            )
                            details["web_token"] = web_token
                            details["token_expiry_on"] = token_expiry_on

                            # update auth table
                            user = auth_utils.update_auth_table(details=details)

                            # get profile pic
                            profile_pic = user.profile_photo_loc
                            if profile_pic == "":
                                profile_pic = os.path.join(
                                    BACKEND_ROOT_PATH,
                                    "databases",
                                    "images",
                                    "profile_pics",
                                    "dummy_profile.png",
                                )
                            img_base64 = ""
                            if is_img_path_valid(profile_pic):
                                img_base64 = convert_img_to_base64(profile_pic)

                            logger.info("User logged in.")
                            return success_200_custom(
                                data={
                                    "user_id": user_id,
                                    "web_token": web_token,
                                    "token_expiry_on": token_expiry_on,
                                    "role": user.role,
                                    "first_name": user.first_name,
                                    "last_name": user.last_name,
                                    "email": user.email,
                                    "profile_photo_loc": img_base64,
                                }
                            )
                        else:
                            # user details are correct but user is not verified by admin
                            raise Unauthenticated(
                                status_msg="User is not verified by Admin."
                            )
                    else:
                        # password is wrong
                        raise Unauthenticated(status_msg="Password is incorrect")
                else:
                    # user does not exists
                    raise NotFoundError(status_msg="User does not exists")
            else:
                # email or password are not valid as per specification
                raise BadRequest(
                    status_msg="Email or Password are not valid as per specification"
                )


class Register(Resource):
    def post(self):
        """
        Usage
        -----
        For the user register page. It checks user data and raise appropriate error
        if required. Created user account and it generates user token and returns it.

        Parameters
        ----------
        form data sent with request
        data format {'first_name':'', 'last_name':'', 'email':'',
                    'password':'', 'retype_password':'', 'role':''}
        'last_name' is optional

        Returns
        -------
        User web token

        """

        details = {
            "first_name": "",
            "last_name": "",
            "email": "",
            "password": "",
            "retype_password": "",
            "role": "",
        }

        # get form data
        try:
            form = request.get_json()
        except Exception as e:
            logger.error(
                f"Register->post : Error occured while getting form data : {e}"
            )
            raise InternalServerError
        else:
            for key in details:
                value = form.get(key, "")
                details[key] = value
                if auth_utils.is_blank(value) and key != "last_name":
                    raise BadRequest(status_msg=f"{key} is empty or invalid")
            details["operation"] = "register"

            # verify registration form data
            if auth_utils.verify_register_form(details):
                # check if user exists
                user = Auth.query.filter_by(email=details["email"]).first()
                if user:
                    # user exists means email is already in use
                    raise AlreadyExistError(status_msg="Email is already in use")
                else:
                    # generate unique user_id
                    user_id = auth_utils.generate_user_id(email=details["email"])

                    # create new user in Auth table
                    details["user_id"] = user_id
                    user = auth_utils.update_auth_table(details=details)

                    # Redirect to login page in frontend
                    # No need to create web_token as during login it will
                    # be created

                    logger.info("New account created")
                    raise Success_200(
                        status_msg="Account created successfully. Now please login."
                    )

            else:
                # email or password are not valid as per specification
                raise BadRequest(
                    status_msg="Email or Password are not valid as per specification OR Password did not match."
                )


class NewUsers(Resource):
    # Admin access required
    # get user_id and token from headers
    # verify token and role of the user

    @token_required
    @admin_required
    def get(self):
        """
        Usage
        -----
        Get all new users which are not verified.
        Only admin can access this.

        Parameters
        ----------

        Returns
        -------
        New users dict

        """

        # get new users data from auth table
        try:
            all_users = (
                Auth.query.filter(Auth.role.in_(["student", "support"]))
                .filter_by(is_verified=False)
                .all()
            )
        except Exception as e:
            logger.error(f"NewUsers->get : Error occured while fetching db data : {e}")
            raise InternalServerError
        else:
            # convert to list of dict
            data = []
            for user in all_users:
                _d = {}
                _d["user_id"] = user.user_id
                _d["first_name"] = user.first_name
                _d["last_name"] = user.last_name
                _d["email"] = user.email
                _d["role"] = user.role
                data.append(_d)
            return success_200_custom(data=data)

    @token_required
    @admin_required
    def put(self, user_id):
        print("###################### User getting verified ##############################")
        """
        Usage
        -----
        When admin verifies user, update user.is_verified to True in auth table

        Parameters
        ----------

        Returns
        -------

        """
        # get form data
        try:
            form = request.get_json()
            user_id = form.get("user_id", "")
            print("################ user_id ################# ",user_id)
        except Exception as e:
            logger.error(f"NewUsers->put : Error occured while getting form data : {e}")
            raise InternalServerError
        else:
            if auth_utils.is_blank(user_id):
                raise BadRequest(status_msg=f"User id is empty or invalid")

            details = {"user_id": user_id, "operation": "verify_user"}

            # check if user exists
            user = Auth.query.filter_by(user_id=user_id).first()
            print("################ User data retrieved from the database ################")
            if user:
                # user exists , proceed to update
                user = auth_utils.update_auth_table(details=details)
                print("########### User verified ################")
                user_name=str(user.first_name)+' '+str(user.last_name)
                user_email=user.email
                user_password=user.password
                user_username=user.first_name
                # print(user_email)
                # print(type(user_email))
                # print('email_demo',type('email_demo'))
                # print('-----------------------')
                user_data_for_discourse = {
                    "name": user_name,
                    "email": user_email,
                    "password": 'Siddhesh@211201',
                    "username": user_username,
                    "active": True,
                    "approved": True,
                    "user_fields[1]": True,
                    "external_ids": {}
                }
                print(user_data_for_discourse)

                create_new_user_discourse_post_url = 'http://localhost:3000/users.json'
                # print("######### All ok yet #########")
                try:
                    response = requests.post(create_new_user_discourse_post_url,json=user_data_for_discourse,headers=headers, verify=False)
                    # print("########### post successful on discourse #############")
                    # print(response.json())
                    discourse_id=response.json()['user_id']
                    # print(user_id,discourse_id)
                    new_ots_disocurse_link=Ots_discourse_userid_map(ots_user_id=str(user_id),discourse_user_id=str(discourse_id))
                    try:
                        db.session.add(new_ots_disocurse_link)
                        db.session.commit()
                    except Exception as error:
                        print(error)
                except requests.exceptions.RequestException as e:
                    print(f"Error: {e}")
                # print(response)
                    
                
                raise Success_200(status_msg="User verified and updated in database.")


            else:
                raise NotFoundError(status_msg="User does not exists.")



    @token_required
    @admin_required
    def delete(self, user_id):
        """
        Usage
        -----
        When admin rejects user, update user.is_verified to False in auth table

        Parameters
        ----------

        Returns
        -------

        """
        # get form data
        try:
            form = request.get_json()
            user_id = form.get("user_id", "")
        except Exception as e:
            logger.error(
                f"NewUsers->delete : Error occured while getting form data : {e}"
            )
            raise InternalServerError
        else:
            if auth_utils.is_blank(user_id):
                raise BadRequest(status_msg=f"User id is empty or invalid")
            details = {"user_id": user_id, "operation": "delete_user"}

            # check if user exists
            user = Auth.query.filter_by(user_id=user_id).first()
            if user:
                # user exists , proceed to update
                user = auth_utils.update_auth_table(details=details)
                raise Success_200(
                    status_msg="Verification failed so user deleted in database."
                )
            else:
                raise NotFoundError(status_msg="User does not exists.")


auth_api.add_resource(Login, "/login")  # path is /api/v1/auth
auth_api.add_resource(Register, "/register")
auth_api.add_resource(NewUsers, "/newUsers", "/newUsers/<string:user_id>")

# --------------------  END  --------------------

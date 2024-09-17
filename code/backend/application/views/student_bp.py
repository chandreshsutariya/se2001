# Online Support Ticket Application
# Tushar Supe : 21f1003637
# Vaidehi Agarwal: 21f1003880
# File Info: This is Student Blueprint file which contains
# Student API and related methods.

# --------------------  Imports  --------------------

from flask import Blueprint, request
from flask_restful import Api, Resource
from application.logger import logger
from application.common_utils import (
    token_required,
    users_required,
)
from application.views.user_utils import UserUtils
from application.responses import *
from application.models import Auth, Ticket, TicketVote
from application.globals import *
from application.database import db

# -------------------- Imports for discourse integration project ----------------------
import requests
from application.models import Ots_discourse_userid_map
from application.api_key import headers, headers_user
# --------------------  Code  --------------------


class StudentUtils(UserUtils):
    def __init__(self, user_id=None):
        self.user_id = user_id


student_bp = Blueprint("student_bp", __name__)
student_api = Api(student_bp)
student_util = StudentUtils()


class StudentAPI(Resource):
    @token_required
    @users_required(users=["student"])
    def get(self, user_id):
        """
        Usage
        -----
        Get a details of student from user_id

        Parameters
        ----------
        user id

        Returns
        -------
        details

        """
        if student_util.is_blank(user_id):
            raise BadRequest(status_msg="User id is missing.")

        # check if user exists
        try:
            user = Auth.query.filter_by(user_id=user_id).first()
        except Exception as e:
            logger.error(
                f"StudentAPI->get : Error occured while fetching student data : {e}"
            )
            raise InternalServerError
        else:
            if user:
                if user.role == "student":
                    n_tickets_created = Ticket.query.filter_by(
                        created_by=user_id
                    ).count()
                    n_tickets_resolved = Ticket.query.filter_by(
                        created_by=user_id, status="resolved"
                    ).count()
                    n_tickets_pending = n_tickets_created - n_tickets_resolved
                    n_tickets_upvoted = TicketVote.query.filter_by(
                        user_id=user_id
                    ).count()
                    student_dict = student_util.convert_user_data_to_dict(user)
                    student_dict["n_tickets_created"] = n_tickets_created
                    student_dict["n_tickets_resolved"] = n_tickets_resolved
                    student_dict["n_tickets_pending"] = n_tickets_pending
                    student_dict["n_tickets_upvoted"] = n_tickets_upvoted

                    return success_200_custom(data=student_dict)
                else:
                    raise BadRequest(status_msg="User must be a student.")
            else:
                raise NotFoundError(status_msg="Student user id does not exists")

    @token_required
    @users_required(users=["student"])
    def put(self, user_id):
        """
        Usage
        ------
        Update student profile,
        Student can update first name, last name, email, password, profile picture location
        ------
        Args:
            user_id (integer): id of user
        ------
        Parameters
        ------
        Form data send with request

        Returns
        ------
        """

        try:
            form = request.get_json()
        except Exception as e:
            logger.error(
                f"StudentAPI->put : Error occured while getting form data : {e}"
            )
            raise InternalServerError
        else:
            student_util.update_user_profile_data(user_id, form)

    # ------------------ Start changes for discourse integration --------------------------- #

        
        headers_user = {
            'Api-Key': api_key_all_user,
            'Api-Username': discourse_user_name,
            'Content-Type': 'application/json',
        }

        update_user_data={
            "name" : form['first_name'] + form['last_name'],
            "external_ids":  {},
        }
        update_user_url='http://localhost:3000/u/' + user_id + '.json'
        response=requests.post(update_user_url,json=update_user_data,headers=headers_user,verify=False)
        print('done')
        print(response.json())
        
            
    @token_required
    @users_required(users=["student"])
    def delete(self, user_id):
        " For deleting user on discourse as well as ots"
        user = Auth.query.filter_by(user_id=user_id).first()
        discourse_id=Ots_discourse_userid_map.query.with_entities(Ots_discourse_userid_map.discourse_user_id).filter_by(ots_user_id=user_id).first()[0]
        try:
            all_user_created_tickets=Ticket.query.filter_by(created_by=user_id).all()
            # print(all_user_tickets)
            for i in all_user_created_tickets:
                i.created_by='abf02c0c383be0608d56da56b38b7d36'
                try:
                    db.session.add(i)
                    db.session.commit()
                except Exception as error:
                    print(error)
            
            all_user_resolved_tickets=Ticket.query.filter_by(resolved_by=user_id).all()
            # print(all_user_tickets)
            for i in all_user_resolved_tickets:
                i.resolved_by='abf02c0c383be0608d56da56b38b7d36'
                try:
                    db.session.add(i)
                    db.session.commit()
                except Exception as error:
                    print(error)
            
            try:
                db.session.delete(user)
                db.session.commit()
            except Exception as error:
                print(error) 

            del_user_url=f'http://localhost:3000/admin/users/{int(discourse_id)}.json'
            del_user_data={
                "delete_posts": False,
                "block_email": False,
                "block_urls": False,
                "block_ip": False
            }
            try:
                response = requests.delete(del_user_url,json=del_user_data,headers=headers,verify=False)
                # print(response.json())
            except Exception as error:
                print(error)

            ots_discourse_del=Ots_discourse_userid_map.query.filter_by(discourse_user_id=discourse_id).first()
            try:
                db.session.delete(ots_discourse_del)
                db.session.commit()
                return({'deletion status from all sources': 'True'})
            except Exception as error:
                print(error)
            
        except Exception as error:
            print(error)

    # ------------------ Start changes for discourse integration --------------------------- #
student_api.add_resource(StudentAPI, "/<string:user_id>")  # path is /api/v1/student
# --------------------  END  --------------------

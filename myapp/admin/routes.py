import werkzeug
from flask_restful import reqparse, Resource
from myapp.extension import api
import datetime
import math
from mpesaa import PaymentService
import os
import json

import pymysql
from flask import Blueprint, render_template, make_response, request, jsonify, json, redirect, url_for, session, \
    current_app as app
from werkzeug.utils import secure_filename
from myapp.extension import db


admin = Blueprint('admin', __name__, url_prefix="/", template_folder='templates')
api.init_app(admin)

class Login(Resource):
    def get(self):
        return make_response(render_template("admin/login.html"))

    def post(self):
        post_parser = reqparse.RequestParser()

        post_parser.add_argument('username', type=str, required=True, help='The username required', )
        post_parser.add_argument('password', type=str, required=True, help='The password required', )
        args = post_parser.parse_args()
        name = args['username']
        password = args['password']

        if (name and password):
            cur = db.connection.cursor(pymysql.cursors.DictCursor)
            sql = "SELECT * FROM users WHERE username = %s AND password = %s "
            val = (name, password)
            results = cur.execute(sql, val)
            if results > 0:
                data = cur.fetchall()
                session['sessionusername'] = data[0]['id']
                session.permanent = True
                cur.close()
                return redirect('/home')


            else:
                cur.close()
                error = 'username and password could not match'
                return make_response(render_template('admin/login.html', error=error))

        else:
            error = 'Enter the required field'
            return make_response(render_template('admin/login.html', error=error))

class Indexa(Resource):
    def get(self):
        return make_response(render_template("admin/index.html"))

    def post(self):
        if not session.get('sessionusername'):
            error = 'please login to continue'
            return make_response(render_template('admin/login.html', error=error))
        else:
            post_parser = reqparse.RequestParser()
            post_parser.add_argument('pg', type=str)
            post_parser.add_argument('srch', type=str)
            args = post_parser.parse_args()
            statuss="0"

            # Setting page, limit and offset variables
            per_page = 10
            if args['pg'] == "":
                page = 1
            else:
                page = int(args['pg'])

            search = args['srch']
            offset = (page - 1) * per_page

            cur = db.connection.cursor(pymysql.cursors.DictCursor)

            # Executing a query to get the total number of products
            if search == "":
                val=(statuss)
                sqlt = "SELECT COUNT(*) FROM transactions  WHERE status=%s"
                total = cur.execute(sqlt,val)

                sql = "SELECT * FROM transactions WHERE status=%s LIMIT %s,%s"
                val = (statuss,offset,per_page)
                results = cur.execute(sql, val)

            else:
                sqlt = "SELECT * FROM transactions WHERE  (name LIKE %s OR phone LIKE %s  OR transid LIKE %s)  AND status=%s"
                sval = (('%' + search + '%'),('%' + search + '%'),('%' + search + '%'),statuss)
                total = cur.execute(sqlt, sval)

                sql = "SELECT * FROM transactions  WHERE (name LIKE %s OR phone LIKE %s  OR transid LIKE %s)  AND status=%s LIMIT %s,%s"
                val = (('%' + search + '%'),('%' + search + '%'),('%' + search + '%'), statuss,offset, per_page)
                results = cur.execute(sql, val)



            if results > 0:
                data = cur.fetchall()

                sqlbalance = "SELECT balance FROM transactions WHERE id=(SELECT MAX(id) FROM transactions);"
                cur.execute(sqlbalance)
                dataa = cur.fetchall()
                paybillbalance = dataa[0]['balance']
                cur.close()

                return jsonify({
                    'totalrecords': total,
                    'totalpages': math.ceil(total / per_page),
                    'currentpage': page,
                    'data': data,
                    'paybillbalance':paybillbalance
                })
            else:
                sqlbalance = "SELECT balance FROM transactions WHERE id=(SELECT MAX(id) FROM transactions);"
                cur.execute(sqlbalance)
                dataa = cur.fetchall()
                paybillbalance = dataa[0]['balance']
                cur.close()
                return jsonify({
                    'totalrecords': 0,
                    'totalpages': 'null',
                    'currentpage': 0,
                    'data': 0,
                    'paybillbalance':paybillbalance
                })


class Comfirm(Resource):

    def post(self):
        json_data = request.get_json(force=True)

        shortcode = json_data['BusinessShortCode']
        Transids= json_data['TransID']
        amountsent = json_data['TransAmount']
        accbalance = json_data['OrgAccountBalance']
        phoneno = json_data['MSISDN']
        firstname = json_data['FirstName']
        middlename = json_data['MiddleName']
        lastname = json_data['LastName']
        Allname =str(firstname+" "+middlename+" "+lastname)
        accountref=json_data['BillRefNumber']
        statuses=0
        timestamp = int(datetime.datetime.now().timestamp())

        cur = db.connection.cursor()
        val = (Transids, accbalance, Allname, phoneno, amountsent,accountref, statuses, timestamp)
        sql = "INSERT IGNORE  INTO transactions (transid,balance,name,phone,payment,account,status,time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(sql,val)
        db.connection.commit()
        cur.close()

        return '{"ResultCode":0,"ResultDesc":"Confirmation received successfully"}'

class Valida(Resource):
    def post(self):
        return '{"ResultCode":0, "ResultDesc":"Success", "ThirdPartyTransID": 0}'

class Comfirmpayment(Resource):
    def post(self):
        if not session.get('sessionusername'):
            error = 'please login to continue'
            return make_response(render_template('admin/login.html', error=error))
        else:
            post_parser = reqparse.RequestParser()

            post_parser.add_argument('pid', type=str)
            args = post_parser.parse_args()

            cur = db.connection.cursor()

            pid = args['pid']
            statuses="1"

            sqlec = "UPDATE transactions SET status=%s WHERE id = %s"
            val = (statuses,pid)
            cur.execute(sqlec, val)
            db.connection.commit()
            results = cur.rowcount
            if results > 0:
                cur.close()
                msg = '{ "suc":"payment comfirmed"}'
                msghtml = json.loads(msg)
                return msghtml
            else:
                cur.close()
                msg = '{ "err":"no changes"}'
                msghtml = json.loads(msg)
                return msghtml

class Push(Resource):
    def get(self):
        return make_response(render_template("admin/stkpush.html"))

    def post(self):
        if not session.get('sessionusername'):
            error = 'please login to continue'
            return make_response(render_template('admin/login.html', error=error))
        else:
            post_parser = reqparse.RequestParser()
            post_parser.add_argument('phone', type=str)
            post_parser.add_argument('amount', type=str)
            args = post_parser.parse_args()

            amount= args['amount']
            phone= args['phone']

            mpesa = PaymentService(consumer_key="4Og7Ziq9wuwzvL85zVo3fnGQAgNJrz4Z",
                                   consumer_password="Q8y2DZtaGy6N8Xdl",
                                   passphrase="976a240803d7d1110a1872333770510399125b0c2031814d53a63c484d15f27f",
                                   shortcode="918885", live=True, debug=True)
            # accesstoken=mpesa.get_access_token()
            timestamp = (
                str(datetime.datetime.now())
                    .split(".")[0]
                    .replace("-", "")
                    .replace(" ", "")
                    .replace(":", "")
            )
            passsword = mpesa._generate_password(timestamp=timestamp)
            results = mpesa.process_request(phone_number=phone, amount=amount,
                                            callback_url="https://mpesa.mabnets.com/kfpcreceive.php?QR19",
                                            reference="testpay",
                                            description="testpay")
            print (results)

            msg = '{ "suc":"push was sent"}'
            msghtml = json.loads(msg)
            return msghtml


api.add_resource(Login, '/')
api.add_resource(Indexa, '/home')
api.add_resource(Comfirm, '/comfirmation')
api.add_resource(Valida, '/validation')
api.add_resource(Comfirmpayment, '/comfirm')
api.add_resource(Push, '/push')


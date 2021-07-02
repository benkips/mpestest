from os.path import dirname, join, realpath

from flask import Flask
from .extension import api
from .admin.routes import admin
from .extension import db
import datetime


app = Flask(__name__)

pymysql_connect_kwargs = {'user': 'root',
                              'password': '',
                              'host': '127.0.0.1',
                              'database':'sammympesa'}



app.config['pymysql_kwargs'] = pymysql_connect_kwargs
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/uploads/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


app.config['PERMANENT_SESSION_LIFETIME'] =  datetime.timedelta(days=1)
app.config['SESSION_REFRESH_EACH_REQUEST']  = True





db.init_app(app)
secret = "ts-c5nmxNzyu7xfdq-GmQxBYb_muHe4p3G1w26UxtHM"
app.secret_key=secret









app.register_blueprint(admin)


if __name__ == '__main__':
    app.run()
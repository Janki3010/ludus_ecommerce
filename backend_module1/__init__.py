from flask import Flask
from flask_restful import Api
from flask_mysqldb import MySQL
from flask_redis import FlaskRedis
import importlib

app = Flask(__name__)
api = Api(app)

app.config['REDIS_URL'] = "redis://localhost:6379/0"
redis_client = FlaskRedis(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'ludus_ecommerce'

mysql = MySQL(app)
app.secret_key = 'your_secret_key'

importlib.import_module('backend_module1.pack1')
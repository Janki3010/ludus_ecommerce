from flask import Flask
from flask_restful import Api
from flask_mail import Mail, Message
from flask_redis import FlaskRedis
import importlib

app = Flask(__name__)
api = Api(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your SMTP server
app.config['MAIL_PORT'] = 587  # Common port for TLS
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'turabit.qa@gmail.com'
app.config['MAIL_PASSWORD'] = 'aamazjpktbrwwenp'
app.config['MAIL_DEFAULT_SENDER'] = 'dapij33397@sgatra.com'
mail = Mail(app)

app.config['REDIS_URL'] = "redis://localhost:6379/0"
redis_client = FlaskRedis(app)
#
app.config['SECRET_KEY'] = '12452367368'

RECAPTCHA_SECRET_KEY = '6LeWilQqAAAAAPFWJZjjmoO3ZP0xWNeDWSqGKkD6'
RECAPTCHA_SITE_KEY = '6LeWilQqAAAAAIKiOBUhYgsXSI_k5w4InofQLw6K'


importlib.import_module('frontend_module1.pack1')
from backend_module1 import api
from backend_module1.pack1.resources import *

api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(ForgotPassword, '/forgotPassword')
api.add_resource(ResetPassword, '/reset_password')
api.add_resource(AddAddress, '/add_address')
api.add_resource(AllAddress, '/all_address')
api.add_resource(EditAddress, '/edit_address')
api.add_resource(Products, '/products')
api.add_resource(Product_detail, '/product_details')

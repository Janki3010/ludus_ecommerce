from frontend_module1 import api
from frontend_module1.pack1.resources import *

api.add_resource(Dashboard, '/')
api.add_resource(SignUp, '/Signup')
api.add_resource(SignIn, '/Signin')
api.add_resource(ForgotPassword, '/ForgotPassword')
api.add_resource(ValidateOTP, '/validate_otp')
api.add_resource(ResetPassword, '/reset_password')
api.add_resource(Home, '/home')
api.add_resource(Address, '/address')
api.add_resource(AllAddress, '/all_address')
api.add_resource(AddNewAddress, '/add_address')
api.add_resource(EditAddress, '/edit_address')
api.add_resource(ProductDetails, '/product_detail')
# api.add_resource(HomeProducts, '/HomeProducts')
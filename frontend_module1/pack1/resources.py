import random
import requests
from flask_mail import Message
from flask import make_response, render_template, request, redirect, flash, session
from flask_restful import Resource

from frontend_module1 import RECAPTCHA_SECRET_KEY, mail, app, redis_client


class Dashboard(Resource):
    def get(self):
        return make_response(render_template('dashboard.html'))


class SignUp(Resource):
    def get(self):
        return make_response(render_template('signup.html'))

    def post(self):
        data = {
            "fname": request.form['fname'],
            "lname": request.form['lname'],
            "month": request.form['month'],
            "day": request.form['day'],
            "year": request.form['year'],
            "gender": request.form['gender'],
            "email": request.form['email'],
            "password": request.form['password'],

        }
        response = requests.post('http://127.0.0.1:7100/register', json=data)

        if response.status_code == 200:
            return redirect('http://127.0.0.1:6070/Signin')
        else:
            return make_response({"error": "Failed to insert data into the database"}, 500)


class SignIn(Resource):
    def get(self):
        return make_response(render_template('signin.html'))

    def post(self):
        recaptcha_response = request.form.get('g-recaptcha-response')
        payload = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = response.json()

        if not result.get('success'):
            flash('reCAPTCHA verification failed. Please try again.')
            return redirect('http://127.0.0.1:6070/Signin')  # Redirect to the login page
        data = {
            "email": request.form['email'],
            "password": request.form['password']
        }

        # if request.form['email'] == 'admin@gmail.com':
        #     return redirect('http://127.0.0.1:6001/admin')
        # else:
        response = requests.post('http://127.0.0.1:7100/login', json=data)

        if response.status_code == 200:
            return redirect('http://127.0.0.1:6070/')
        else:
            return 'Error'


class ForgotPassword(Resource):
    def get(self):
        return make_response(render_template('lost-password.html'))

    def post(self):
        email = request.form['email']
        data = {'email': email}
        response = requests.post('http://127.0.0.1:7100/forgotPassword', json=data)

        if response.status_code != 200:
            flash('Email does not exist.', 'danger')
            return redirect('http://127.0.0.1:6070/ForgotPassword')

        otp = random.randint(100000, 999999)  # Generate a 6-digit OTP

        msg = Message('Your OTP for Password Reset', recipients=[email])
        msg.body = f'Your OTP is {otp}. Please use it to reset your password.'

        try:
            mail.send(msg)
            flash('Check your email for the OTP!', 'info')
        except Exception as e:
            flash('Failed to send email. Please try again later.', 'danger')
            app.logger.error(f'Error sending email: {str(e)}')

        session['otp'] = otp
        return redirect('http://127.0.0.1:6070/validate_otp')


class ValidateOTP(Resource):
    def get(self):
        return make_response(render_template('validate_otp.html'))

    def post(self):
        entered_otp = request.form['otp']

        if 'otp' in session and session['otp'] == int(entered_otp):
            return redirect('http://127.0.0.1:6070/reset_password')
        else:
            flash('Invalid or expired OTP.', 'danger')
            return redirect('http://127.0.0.1:6070/forgot_password')


class ResetPassword(Resource):
    def get(self):
        return make_response(render_template('reset_password.html'))

    def post(self):
        new_password = request.form['password']

        data = {'new_password': new_password}
        response = requests.post('http://127.0.0.1:7100/reset_password', json=data)

        if response.status_code == 200:
            flash('Your password has been updated!', 'success')
            return redirect(f'http://127.0.0.1:6070/Signin')
        else:
            flash('Failed to update password.', 'danger')
            return redirect('http://127.0.0.1:6070/reset_password')


class Address(Resource):
    def get(self):
        return make_response(render_template('dash-address-book.html'))


class AddNewAddress(Resource):
    def get(self):
        return make_response(render_template('dash-address-add.html'))

    def post(self):
        data = {
            "name": request.form['name'],
            "phone": request.form['phone'],
            "street-address": request.form['address-street'],
            "postal-code": request.form['postal-code'],
            "city": request.form['city'],
            "state": request.form['state'],
            "country": request.form['country']
        }

        response = requests.post('http://127.0.0.1:7100/add_address', json=data)

        if response.status_code == 200:
            return redirect('http://127.0.0.1:6070/all_address')
        else:
            return make_response({"error": "Failed to insert data into the database"}, 500)


class AllAddress(Resource):
    def get(self):
        if request.method == 'GET':
            response = requests.get('http://127.0.0.1:7100/all_address')

            if response.status_code == 200:
                address = response.json()['user_address']
                return make_response(render_template('dash-address-make-default.html', all_address=address))
            else:
                return make_response('Error at time to fetch all the addresses', response.status_code)

    def post(self):
        data = {
            'address_id': request.form['address_id']
        }
        response = requests.post('http://127.0.0.1:7100/all_address', json=data)
        if response.status_code == 200:
            return make_response(render_template('checkout.html'))
        else:
            return make_response({"error": "Failed to insert data into the database"}, 500)


class EditAddress(Resource):
    def get(self):
        try:
            response = requests.get('http://127.0.0.1:7100/edit_address')
            response.raise_for_status()
            if response.status_code == 200:
                address = response.json()['user_address'][0]
                return make_response(render_template('dash-address-edit.html', address=address))
        except requests.exceptions.RequestException as e:
            print(f"Error fetching address: {e}")
            return make_response('Error at time to fetch all the addresses', 500)

    def post(self):
        data = {
            'address_id': session.get('address_id'),
            'name': request.form['name'],
            'address': request.form['address'],
            'phone': request.form['phone']
        }
        response = requests.post('http://127.0.0.1:7100/edit_address', json=data)
        if response.status_code == 200:
            return redirect('http://127.0.0.1:6070/all_address')
        else:
            return make_response({"error": "Failed to insert data into the database"}, 500)


class Home(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/products')
        if response.status_code == 200:
            data = response.json()['products']
            return make_response(render_template('index.html', products=data))
        else:
            return make_response('Error fetching product details', response.status_code)
        # return make_response(render_template('index.html'))


class ProductDetails(Resource):
    def get(self):
        product_id = request.args.get('product_id')
        session['product_id'] = product_id
        return make_response(render_template('product-detail.html'))

    def post(self):
        product_id = session.get('product_id')
        data = {
            'product_id': product_id
        }
        

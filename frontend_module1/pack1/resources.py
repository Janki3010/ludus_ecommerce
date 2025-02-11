import random
import requests
from flask_mail import Message
from flask import make_response, render_template, request, redirect, flash, session
from flask_restful import Resource

from frontend_module1 import RECAPTCHA_SECRET_KEY, mail, app, redis_client


class Dashboard(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/dashboard')
        if len(response.json()['user_address']) >= 1:
            user_address = response.json()['user_address'][0]
        else:
            user_address = response.json()['user_address']
        user_profile = response.json()['user_profile']
        products = response.json()['products']
        return make_response(
            render_template('dashboard.html', address=user_address, profile=user_profile, products=products))


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
            return redirect('http://127.0.0.1:6070/dashboard')
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


class MyProfile(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/edit_profile')
        user_data = response.json()['user_data']
        return make_response(render_template('dash-my-profile.html', data=user_data))


class EditProfile(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/edit_profile')
        user_data = response.json()['user_data']
        return make_response(render_template('dash-edit-profile.html', data=user_data))

    def post(self):
        data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'birthday': request.form.get('birthday'),
            'gender': request.form.get('gender'),
            'email': request.form.get('email')
        }
        response = requests.post('http://127.0.0.1:7100/edit_address', json=data)
        if response.status_code == 200:
            return redirect('/edit_profile')


class Address(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/all_address')

        if response.status_code == 200:
            all_address = response.json()['user_address']
            return make_response(render_template('dash-address-book.html', all_address=all_address))


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
            return redirect('/home')
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

        data = {
            'product_id': product_id
        }
        try:
            response = requests.post('http://127.0.0.1:7100/product_details', json=data)
            response.raise_for_status()

            product_details = response.json()['product_details']
            user_id = response.json()['user_id']
            all_reviews = response.json()['reviews']
            return make_response(
                render_template('product-detail.html', product=product_details, product_id=product_id, user_id=user_id,
                                all_reviews=all_reviews))
        except requests.exceptions.HTTPError as http_err:
            return f'HTTP error occurred: {http_err}', 500
        except requests.exceptions.ConnectionError as conn_err:
            return f'Connection error occurred: {conn_err}', 500
        except Exception as err:
            return f'An error occurred: {err}', 500


class AddToCart(Resource):
    def post(self):
        data = {
            'product_id': request.form['product_id'],
            'product_name': request.form['product_name'],
            'product_price': request.form['product_price'],
            'product_image': request.form['product_image'],
            'qty': request.form['quantity']
        }
        response = requests.post('http://127.0.0.1:7100/add_to_cart', json=data)
        if response.status_code == 200:
            return redirect('/cart_products')
        else:
            return 'Error at time of add to cart'


class ManageCart(Resource):
    def post(self):
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        action = request.form['action']

        data = {
            'product_id': product_id,
            'qty': quantity,
            'action': action
        }

        response = requests.post('http://127.0.0.1:7100/manage_product', json=data)

        if response.status_code == 200:
            return redirect('/cart_products')
        else:
            return 'Error processing your request', 500


class RemoveFromCart(Resource):
    def get(self):
        product_id = request.args.get('product_id')
        data = {'product_id': product_id}
        response = requests.get('http://127.0.0.1:7100/remove_from_cart', json=data)
        if response.status_code == 200:
            return redirect('/cart_products')


class CartProducts(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/fetch_cart_products')
        cart_products = response.json()['cart_products']
        total_price = response.json()['total_price']
        return make_response(render_template('cart.html', cart_products=cart_products, total_price=total_price))


class ClearCart(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/clear_cart')
        if response.status_code == 200:
            return redirect('/cart_products')


class ProceedToCheckout(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/checkout')
        if response.status_code == 200 and response.json()['message'] == 'success':
            products = response.json()['checkout_products']
            total_price = response.json()['total_price']
            default_address = response.json()['default_address']
            address_parts = default_address[2].split(',')

            address_dict = {
                'street_address': address_parts[0],
                'ZIP': address_parts[1],
                'City': address_parts[2],
                'state': address_parts[3],
                'country': address_parts[4]
            }

            return make_response(render_template('checkout.html', products=products, total_price=total_price,
                                                 default_address=default_address, address_dict=address_dict))
        elif response.json()['message'] == 'Address Not Found':
            flash('Please provide address for deliver the product on the location', 'error')
            return make_response(render_template('cart.html'))
            # return {"meassage": 'Please provide address for deliver the product on the location'}


class PlaceOrder(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/place_order')
        if response.status_code == 200:
            return redirect('/order_products')


class OrderProducts(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/order_products')
        if response.status_code == 200:
            products = response.json()['products']
            return make_response(render_template('dash-my-order.html', order_products=products))

class PaymentOption(Resource):
    def get(self):
        return make_response(render_template('dash-payment-option.html'))

class Cancellation(Resource):
    def get(self):
        return make_response(render_template('dash-cancellation.html'))


class Add_To_WishList(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/add_to_wishlist')
        if response.status_code == 200:
            return redirect('/show_wishlist')


class ShowWishlist(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/show_wishlist')
        wishlist_products = response.json()['wishlist_products']

        if response.status_code == 200:
            return make_response(render_template('wishlist.html', wishlist_products=wishlist_products))


class RemoveWishlistProduct(Resource):
    def get(self):
        product_id = request.args.get('product_id')
        data = {'product_id': product_id}
        response = requests.get('http://127.0.0.1:7100/remove_wishlist', json=data)
        if response.status_code == 200:
            return redirect('/show_wishlist')


class ContactUsInfo(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/contact_us_info')
        contact_us_info = response.json()['contact_us_info'][0]
        return make_response(render_template('contact.html', info=contact_us_info))


class AboutUs(Resource):
    def get(self):
        return make_response(render_template('about.html'))


class Error(Resource):
    def get(self):
        return make_response(render_template('404.html'))


class Reviews(Resource):
    def post(self):
        product_id = request.args.get('product_id')
        data = {
            'product_id': product_id,
            'rating': request.form.get('rating'),
            'review': request.form.get('review'),
            'name': request.form.get('name')
        }

        response = requests.post('http://127.0.0.1:7100/add_review', json=data)

        if response.status_code == 200:

            return redirect(f'/product_detail?product_id={product_id}')
        else:
            return 'Error processing your request', 500


class AllProducts(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/products')
        if response.status_code == 200:
            data = response.json()['products']
            return make_response(render_template('shop-side-version-2.html', products=data))
        else:
            return make_response('Error fetching product details', response.status_code)


class FAQ(Resource):
    def get(self):
        return make_response(render_template('faq.html'))


class OneTimeAddress(Resource):
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
            return redirect('/proceed_checkout')
        else:
            return make_response({"error": "Failed to insert data into the database"}, 500)


class BlogDetails(Resource):
    def get(self):
        return make_response(render_template('blog-detail.html'))


class BlogLeft(Resource):
    def get(self):
        return make_response(render_template('blog-left-sidebar.html'))


class BlogRight(Resource):
    def get(self):
        return make_response(render_template('blog-right-sidebar.html'))


class BlogMasonry(Resource):
    def get(self):
        return make_response(render_template('blog-masonry.html'))


class BlogSidebar(Resource):
    def get(self):
        return make_response(render_template('blog-sidebar-none.html'))


class SignOut(Resource):
    def get(self):
        response = requests.get('http://127.0.0.1:7100/Signout')
        if response.status_code == 200:
            return redirect('/Signup')

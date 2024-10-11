from flask import request
from flask_restful import Resource

from backend_module1 import mysql, redis_client


class Register(Resource):
    def post(self):
        data = request.json
        fname = data.get('fname')
        lname = data.get('lname')
        month = data.get('month')
        day = data.get('day')
        year = data.get('year')
        birthday = f'{year}-{month}-{day}'
        gender = data.get('gender')
        email = data.get('email')
        password = data.get('password')

        cur = mysql.connection.cursor()
        cur.callproc('add_users', (fname, lname, birthday, gender, email, password))

        mysql.connection.commit()
        cur.close()

        return {"message": "Data inserted successfully"}, 200


class Login(Resource):
    def post(self):
        data = request.json
        email = data.get('email')
        password = data.get('password')

        cur = mysql.connection.cursor()
        cur.execute('select * from users where email = %s and password = %s', (email, password))
        account = cur.fetchone()
        cur.close()
        if account:
            # # global access_token
            user_id = account[0]
            # # access_token = create_access_token(identity=user_id)
            # session['loggedin'] = True
            # session['id'] = account[0]
            redis_client.set('user_id', user_id)
            # # session['email'] = account[2]
            # # session['username'] = account[1]
            return {'message': 'success'}, 200
            # return {'message': 'success', 'access_token': access_token, 'user_id': user_id}, 200
        else:
            return {'message': 'user not found'}, 404


class ForgotPassword(Resource):
    def post(self):
        data = request.json
        email = data.get('email')
        cur = mysql.connection.cursor()
        cur.execute('SELECT email from users where email=%s', (email,))
        email = cur.fetchone()

        redis_client.set('email', str(email))
        if email:
            return {'message': 'email exists'}, 200


class ResetPassword(Resource):
    def post(self):
        email = redis_client.get('email')
        decoded_string = email.decode('utf-8')
        email = decoded_string.strip("()' ,")
        data = request.json
        new_password = data.get('new_password')
        cur = mysql.connection.cursor()
        cur.callproc('newPassword', (new_password, str(email)))
        mysql.connection.commit()
        cur.close()


class AddAddress(Resource):
    def post(self):
        user_id = redis_client.get('user_id')
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        street_address = data.get('street-address')
        postal_code = data.get('postal-code')
        city = data.get('city')
        state = data.get('state')
        country = data.get('country')
        adress = f'{street_address},{postal_code},{city},{state},{country}'
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO address(uid,user_address,name,phone) values(%s,%s,%s,%s)",
                    (user_id, adress, name, phone))
        mysql.connection.commit()
        cur.close()
        return {"message": "Data inserted successfully"}, 200


class AllAddress(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        cur = mysql.connection.cursor()
        cur.execute(
            "select user_address,name,phone,default_shipping,default_billing,address_id from address where uid=%s",
            (user_id,))
        all_address = cur.fetchall()
        if not all_address:
            return {'message': 'No address found'}, 404
        return {'message': 'success', 'user_address': list(all_address)}, 200

    def post(self):
        user_id = redis_client.get('user_id')
        data = request.json
        address_id = data.get('address_id')
        redis_client.set('address_id', address_id)
        # default_address = data.get('default_address')
        cur = mysql.connection.cursor()
        # cur.execute('update ludus_ecommerce.address set ludus_ecommerce.address.default_shipping = 1 , ludus_ecommerce.address.default_billing = 1 where uid=%s and user_address=%s',(user_id,address))
        cur.callproc('default_shipping', (address_id, user_id))
        mysql.connection.commit()
        cur.close()
        return {"message": "Data inserted successfully"}, 200


class EditAddress(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        address_id = redis_client.get('address_id')
        cur = mysql.connection.cursor()

        cur.execute("SELECT user_address, name, phone FROM address WHERE address_id = %s AND uid = %s",
                    (address_id, user_id))
        all_address = cur.fetchall()
        mysql.connection.commit()
        cur.close()

        if not all_address:
            return {'message': 'No address found'}, 404

        # Decode bytes to string if needed
        decoded_addresses = []
        for address in all_address:
            decoded_address = {
                'user_address': address[0].decode('utf-8') if isinstance(address[0], bytes) else address[0],
                'name': address[1],
                'phone': address[2]
            }
            decoded_addresses.append(decoded_address)

        return {'message': 'success', 'user_address': decoded_addresses,
                'address_id': address_id.decode('utf-8')}, 200

    def post(self):
        user_id = redis_client.get('user_id')
        data = request.json
        address_id = data.get('address_id')
        name = data.get('name')
        address = data.get('address')
        phone = data.get('phone')
        cur = mysql.connection.cursor()
        cur.callproc('edit_address', (address, name, phone, user_id, address_id))
        mysql.connection.commit()
        cur.close()
        return 'User address updated successfully'


class Products(Resource):
    def get(self):
        cur = mysql.connection.cursor()
        # cur.callproc('fetchProduct')
        cur.execute('select product_name, description, price, image, qty, category.name, product_id from ludus_ecommerce.products, ludus_ecommerce.category where products.category_Id = category.category_id')
        products = cur.fetchall()

        product_list = []
        for product in products:
            product_list.append({
                'name': product[0],
                'description': product[1],
                'price': product[2],
                'image_path': product[3],
                'qty': product[4],
                'category': product[5],
                'product_id': product[6]
            })

        return {'message': 'success', 'products': product_list}, 200

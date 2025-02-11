from datetime import datetime, date

import MySQLdb
from flask import request, session
from flask_restful import Resource
# from pip._internal.network import session

from backend_module1 import mysql, redis_client


class AddressService:
    @staticmethod
    def get_default_address(user_id):
        cur = mysql.connection.cursor()

        cur.execute('SELECT address_id FROM address WHERE uid = %s AND default_shipping = 1', (int(user_id),))
        address_id_row = cur.fetchone()

        if address_id_row is None:
            return None, {'message': 'No default shipping address found'}, 404

        address_id = address_id_row[0]

        cur.execute("SELECT user_address, name, phone FROM address WHERE address_id = %s AND uid = %s",
                    (address_id, int(user_id)))
        all_address = cur.fetchall()

        if not all_address:
            return None, {'message': 'No address found'}, 404

        decoded_addresses = []
        for address in all_address:
            decoded_address = {
                'user_address': address[0].decode('utf-8') if isinstance(address[0], bytes) else address[0],
                'name': address[1],
                'phone': address[2]
            }
            decoded_addresses.append(decoded_address)

        return decoded_addresses, {'message': 'success', 'address_id': address_id}, 200


class OrderService:
    @staticmethod
    def get_order_products(user_id):
        cur = mysql.connection.cursor()
        """ CREATE DEFINER=`root`@`localhost` PROCEDURE `order_products`(IN uid int)
            BEGIN
            SELECT DISTINCT 
                p.product_name, 
                p.image, 
                oi.qty, 
                oi.price, 
                o.Status,
            	o.OrderID,
                o.OrderDate
                
            FROM 
                ludus_ecommerce.products p
            JOIN 
                ludus_ecommerce.order_items oi ON p.product_id = oi.p_id
            JOIN 
                ludus_ecommerce.orders o ON o.OrderID = oi.order_id
            WHERE 
                o.UserID = uid
            ORDER BY 
                    o.OrderDate DESC;
            END"""
        cur.callproc('order_products', (int(user_id),))
        order_products = cur.fetchall()

        products = []
        for product in order_products:
            product_dict = {
                'product_name': product[0],
                'image': product[1],
                'qty': product[2],
                'price': product[3],
                'status': product[4],
                'order_id': product[5],
                'order_date': product[6].strftime('%Y-%m-%d %H:%M:%S') if product[6] else None
            }
            products.append(product_dict)

        return products


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
        """CREATE DEFINER=`root`@`localhost` PROCEDURE `add_users`(IN fname varchar(20),
           IN lname varchar(20),
           IN birthday date,
           IN gender varchar(10),
           IN email varchar(30),
           IN password varchar(30)
                       )
            BEGIN
              insert into ludus_ecommerce.users (fname,lname,birthday,gender,email,password) values(fname,lname,birthday,gender,email,password);
            END """
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
        """ CREATE DEFINER=`root`@`localhost` PROCEDURE `newPassword`(IN new_password varchar(20), IN email varchar(45))
            BEGIN
              update ludus_ecommerce.users set password=new_password where ludus_ecommerce.users.email=email; 
            END"""
        cur.callproc('newPassword', (new_password, str(email)))
        mysql.connection.commit()
        cur.close()


class EditProfile(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE id=%s', (int(user_id),))
        user_data = cur.fetchone()

        if user_data is None:
            return {'message': 'User not found'}, 404

        userData = {
            'user_id': user_data[0],
            'first_name': user_data[1],
            'last_name': user_data[2],
            'birthday': user_data[3].isoformat() if isinstance(user_data[3], date) else user_data[3],
            'gender': user_data[4],
            'email': user_data[5],
        }

        return {'message': 'success', 'user_data': userData}, 200

    def post(self):
        data = request.json
        user_id = redis_client.get('user_id')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        birthday = data.get('birthday')
        gender = data.get('gender')
        email = data.get('email')
        cur = mysql.connection.cursor()
        """CREATE DEFINER=`root`@`localhost` PROCEDURE `edit_profile`(IN uid int,
          IN first_name varchar(20),
          IN last_name varchar(20),
          IN birthday date,
          IN gender varchar(10),
          IN email varchar(45)
        )
        BEGIN
          UPDATE ludus_ecommerce.users SET fname=first_name,lname=last_name,birthday=birthday,gender=gender,email=email where id=uid;
        END """
        cur.callproc('edit_profile', (user_id, first_name, last_name, birthday, gender, email))
        mysql.connection.commit()
        cur.close()
        return {'message': 'Updated successfully'}, 200


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

        # cur.execute('select address_id from address where uid = %s and default_shipping = 1', (int(user_id),))
        # address_id = cur.fetchone()
        # redis_client.set('address_id', bytes(address_id))
        # default_address = data.get('default_address')

        # cur.execute('update ludus_ecommerce.address set ludus_ecommerce.address.default_shipping = 1 , ludus_ecommerce.address.default_billing = 1 where uid=%s and user_address=%s',(user_id,address))
        cur = mysql.connection.cursor()
        """CREATE DEFINER=`root`@`localhost` PROCEDURE `default_shipping`(
            IN p_address_id INT,
            IN p_uid INT
        )
        BEGIN
            UPDATE ludus_ecommerce.address 
            SET 
                default_shipping = 1, 
                default_billing = 1 
            WHERE 
                uid = p_uid AND address_id = p_address_id;
        
            UPDATE ludus_ecommerce.address 
            SET 
                default_shipping = 0, 
                default_billing = 0 
            WHERE 
                uid = p_uid AND address_id != p_address_id;
        END """
        cur.callproc('default_shipping', (address_id, user_id))
        mysql.connection.commit()
        cur.close()
        return {"message": "Data inserted successfully"}, 200


class EditAddress(Resource):
    def get(self):
        user_id = redis_client.get('user_id')

        addresses, message, status_code = AddressService.get_default_address(user_id)

        if addresses is None:
            return message, status_code

        return {'message': 'success', 'user_address': addresses,
                'address_id': message['address_id']}, 200

    def post(self):
        user_id = redis_client.get('user_id')
        data = request.json
        address_id = data.get('address_id')
        name = data.get('name')
        address = data.get('address')
        phone = data.get('phone')
        cur = mysql.connection.cursor()
        """CREATE DEFINER=`root`@`localhost` PROCEDURE `edit_address`(
            IN p_address VARCHAR(100),
            IN p_name VARCHAR(15),
            IN p_phone VARCHAR(12),
            IN p_uid INT,
            IN p_address_id INT
        )
        BEGIN
            UPDATE ludus_ecommerce.address 
            SET user_address = p_address, 
                name = p_name, 
                phone = p_phone 
            WHERE uid = p_uid 
              AND address_id = p_address_id;
        END """
        cur.callproc('edit_address', (address, name, phone, user_id, address_id))
        mysql.connection.commit()
        cur.close()
        return 'User address updated successfully'


class Products(Resource):
    def get(self):
        cur = mysql.connection.cursor()
        # cur.callproc('fetchProduct')
        cur.execute(
            'select product_name, description, price, image, qty, category.name, product_id from ludus_ecommerce.products, ludus_ecommerce.category where products.category_Id = category.category_id')
        products = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        product_list = []
        for product in products:
            product_list.append({
                'name': product[0],
                'description': product[1],
                'price': product[2],
                'image_path': product[3],
                'qty': product[4],
                'category': product[5],
                'product_id': product[6],
            })

        return {'message': 'success', 'products': product_list}, 200


class Product_detail(Resource):
    def post(self):
        user_id = redis_client.get('user_id')
        data = request.json
        product_id = data.get('product_id')
        redis_client.set('product_id', product_id)

        cur = mysql.connection.cursor()
        cur.execute(
            'SELECT product_name, description, price, image, qty, product_id FROM products WHERE product_id = %s',
            (product_id,))
        product_detail = cur.fetchone()

        cur.execute('SELECT * FROM reviews WHERE pro_id=%s', (product_id,))
        all_reviews = cur.fetchall()

        reviews_list = []
        for review in all_reviews:
            review_dict = {
                'id': review[0],
                'pro_id': review[1],
                'user_id': review[2],
                'rating': review[3],
                'comment': review[4],
                'created_at': review[5].strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
                'username': review[6]
            }
            reviews_list.append(review_dict)

        if product_detail is None:
            return {'message': 'Product not found'}, 404

        product_details = list(product_detail)

        # Decode image if it's in bytes
        if isinstance(product_details[3], bytes):
            product_details[3] = product_details[3].decode('utf-8')

        mysql.connection.commit()
        cur.close()

        return {'message': 'success', 'product_details': product_details, 'user_id': user_id.decode('utf-8'), 'reviews':reviews_list}, 200


class AddToWishList(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        product_id = redis_client.get('product_id')
        cur = mysql.connection.cursor()
        """CREATE DEFINER=`root`@`localhost` PROCEDURE `AddToWishlist`(
            IN userId INT,
            IN productId INT
        )
        BEGIN
            DECLARE productExists INT;
        
            SELECT COUNT(*) INTO productExists
            FROM wishlist
            WHERE Uid = userId AND Pid = productId;
        
            IF productExists = 0 THEN
                INSERT INTO wishlist (Uid, Pid, created_at, updated_at)
                VALUES (userId, productId, NOW(), NOW());
            END IF;

END """
        cur.callproc('AddToWishlist', (user_id, product_id))
        # cur.execute(
        #     'INSERT INTO wishlist (Uid, Pid, created_at, updated_at) VALUES (%s, %s, %s, %s)',
        #     (int(user_id), int(product_id), datetime.today(), datetime.today())
        # )
        mysql.connection.commit()
        cur.close()

        return {'message': 'success'}


class ShowWishList(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        cur = mysql.connection.cursor()
        cur.execute(
            'select product_name, price, image, product_id from products,wishlist where products.product_id = '
            'wishlist.Pid and '
            'Uid = %s',
            (int(user_id),))
        wishlist_products = cur.fetchall()
        products = list(wishlist_products)
        return {'message': 'success', 'wishlist_products': products}


class RemoveWishlistPro(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        data = request.json
        product_id = data.get('product_id')
        cur = mysql.connection.cursor()
        cur.execute('delete from ludus_ecommerce.wishlist where Pid = %s and Uid = %s', (product_id, user_id))
        mysql.connection.commit()
        cur.close()

        return {'message': 'success'}


class AddToCart(Resource):
    def post(self):
        user_id = redis_client.get('user_id')
        data = request.json
        product_id = data.get('product_id')
        # user_id = data.get('user_id')
        product_name = data.get('product_name')
        product_price = data.get('product_price')
        product_image = data.get('product_image')
        quantity = data.get('qty')
        if not user_id or not product_id or not quantity:
            return {"message": "Missing required fields"}, 400

        cur = mysql.connection.cursor()
        """ CREATE DEFINER=`root`@`localhost` PROCEDURE `addToCart`(IN userId INT, IN productId INT, IN qty1 INT, IN price INT)
            BEGIN
                DECLARE existing_qty INT;
                
                -- Check if the item is already in the cart and its status
                SELECT quantity INTO existing_qty
                FROM ludus_ecommerce.cart
                WHERE user_id = userId AND product_id = productId AND status = 'InCart';
                
                IF existing_qty IS NOT NULL THEN
                    -- Update the quantity if the item is already in the cart
                    UPDATE ludus_ecommerce.cart
                    SET quantity = quantity + qty1
                    WHERE user_id = userId AND product_id = productId AND status = 'InCart';
                ELSE
                    -- Check if the item was previously ordered
                    SELECT COUNT(*) INTO @orderedCount
                    FROM ludus_ecommerce.cart
                    WHERE user_id = userId AND product_id = productId AND status = 'Ordered';
            
                    IF @orderedCount > 0 THEN
                        -- If the item was previously ordered, insert it back into the cart
                        INSERT INTO ludus_ecommerce.cart (user_id, product_id, quantity, price, status)
                        VALUES (userId, productId, qty1, price, 'InCart');
                    ELSE
                        -- Insert a new record if the item is not in the cart
                        INSERT INTO ludus_ecommerce.cart (user_id, product_id, quantity, price, status)
                        VALUES (userId, productId, qty1, price, 'InCart');
                    END IF;
                END IF;
                
                -- Update product quantity in inventory
                UPDATE ludus_ecommerce.products 
                SET qty = qty - qty1 
                WHERE product_id = productId;
            END """
        cur.callproc('addToCart', (user_id, product_id, quantity, product_price))
        mysql.connection.commit()
        cur.close()

        return {"message": "Product added to cart successfully"}, 200


class ManageProduct(Resource):
    def post(self):
        user_id = redis_client.get('user_id')
        data = request.json
        product_id = data.get('product_id')
        quantity = data.get('qty')
        action = data.get('action')
        cur = mysql.connection.cursor()
        """CREATE DEFINER=`root`@`localhost` PROCEDURE `manage_cart`(IN pid INT, IN q INT, IN uid INT, IN action VARCHAR(10))
            BEGIN
               DECLARE cid INT;
               DECLARE current_qty INT;
            
                SELECT cart_id, quantity INTO cid, current_qty 
            	FROM cart 
            	WHERE user_id = uid AND product_id = pid
            	LIMIT 1;  -- Ensure only one row is returned
            
            
               IF action = 'remove' THEN
                  -- Check if current quantity is less than the quantity to remove
                  IF current_qty < q THEN
                     SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quantity in cart cannot be less than zero';
                  END IF;
            
                  UPDATE cart SET quantity = quantity - q WHERE cart_id = cid;
                  UPDATE products SET qty = qty + q WHERE product_id = pid;
            
               ELSEIF action = 'update' THEN
                  IF cid IS NULL THEN
                     INSERT INTO cart (user_id, product_id, quantity) VALUES (user_id, pid, q);
                  ELSE
                     UPDATE cart SET quantity = quantity + q WHERE cart_id = cid;
                  END IF;
            
                  UPDATE products SET qty = qty - q WHERE product_id = pid;
            
               ELSE
                  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid action';
               END IF;
            END """
        cur.callproc('manage_cart', (int(product_id), int(quantity), int(user_id), action))

        message = f"Product {action}d successfully"

        mysql.connection.commit()
        cur.close()

        return {"message": message}, 200


class RemoveFromCart(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        data = request.json
        product_id = data.get('product_id')
        cur = mysql.connection.cursor()
        cur.execute('delete from cart where product_id = %s and user_id = %s', (product_id, user_id))
        mysql.connection.commit()
        cur.close()

        return {'message': 'success'}


class FetchCartProducts(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        cur = mysql.connection.cursor()
        """CREATE DEFINER=`root`@`localhost` PROCEDURE `fetch_cart_products`(IN user_id int)
            BEGIN
              select products.product_name, products.image, products.price*cart.quantity as TotalPrice, products.product_id, cart_id, cart.quantity, products.price from ludus_ecommerce.products JOIN ludus_ecommerce.cart on ludus_ecommerce.products.product_id = ludus_ecommerce.cart.product_id where ludus_ecommerce.cart.user_id = user_id and status='InCart';
            END """
        cur.callproc('fetch_cart_products', (int(user_id),))
        products = cur.fetchall()
        product_list = []
        for product in products:
            product_list.append({
                'name': product[0],
                'image_path': product[1],
                'totalPrice': product[2],
                'product_id': product[3],
                'cart_id': product[4],
                'qty': product[5],
                'price': product[6]
            })
        total = 0
        for price in products:
            total += price[2]

        return {'message': 'success', 'cart_products': product_list, 'total_price': total}, 200


class ClearCart(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        cur = mysql.connection.cursor()
        cur.execute('delete from cart where user_id = %s', (user_id,))
        mysql.connection.commit()
        cur.close()

        return {'message': 'success'}


class CheckOut(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        cur = mysql.connection.cursor()
        """ CREATE DEFINER=`root`@`localhost` PROCEDURE `buyProducts`(IN uid int)
                BEGIN
                 SELECT product_name,quantity,(cart.quantity*cart.price) as Total_Price, image,cart.product_id from ludus_ecommerce.cart JOIN ludus_ecommerce.products where cart.product_id=products.product_id and user_id=uid;
                END """
        cur.callproc('buyProducts', (user_id,))
        checkout_products = cur.fetchall()
        products = list(checkout_products)
        total = 0
        for price in products:
            total += price[2]

        cur.execute('select name,phone,user_address from address where uid=%s and default_shipping=1', (user_id,))
        default_address = cur.fetchone()
        if default_address:
            default_address = list(default_address)
            return {'message': 'success', 'checkout_products': products, 'total_price': total,
                    'default_address': default_address}, 200
        else:
            return {'message': 'Address Not Found'}


class PlaceOrder(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        cur = mysql.connection.cursor()
        """ CREATE DEFINER=`root`@`localhost` PROCEDURE `PlaceOrder`(IN uid INT)
        BEGIN
            DECLARE newOrderId INT;
        
            -- Insert a new order into the orders table
            INSERT INTO ludus_ecommerce.orders(UserID, OrderDate, Status)
            VALUES(uid, NOW(), 'Processing');
        
            -- Get the last inserted order ID
            SET newOrderId = LAST_INSERT_ID();
        
            -- Insert items from the cart into the order_items table
            INSERT INTO ludus_ecommerce.order_items(order_id, p_id, qty, price)
            SELECT newOrderId, product_id, quantity, price
            FROM ludus_ecommerce.cart
            WHERE user_id = uid AND status = 'InCart';
        
            -- Update the cart items' status to 'Ordered' or remove them
            UPDATE ludus_ecommerce.cart
            SET status = 'Ordered'
            WHERE user_id = uid AND status = 'InCart';
        END"""
        cur.callproc('PlaceOrder', (int(user_id),))
        mysql.connection.commit()
        # cur.callproc('order_products', (int(user_id),))
        # order_products = cur.fetchall()
        # products = list(order_products)

        cur.close()
        return {"message": "Place ordered successfully"}, 200
        # return {"message": "Place ordered successfully", 'products': products}, 200


class OrderProducts(Resource):
    def get(self):
        user_id = redis_client.get('user_id')
        products = OrderService.get_order_products(user_id)

        return {"message": "Fetched ordered products successfully", 'products': products}, 200


class Dashboard(Resource):
    def get(self):
        user_id = redis_client.get('user_id')

        cur = mysql.connection.cursor()
        cur.execute('SELECT fname, email from users where id=%s', (int(user_id),))
        user_profile = cur.fetchone()
        user_profile = list(user_profile)

        products = OrderService.get_order_products(user_id)

        addresses, message, status_code = AddressService.get_default_address(user_id)

        if addresses is None:
            return {'message': 'success', 'user_address': [], 'user_profile': user_profile, 'products': products}, 200

        return {'message': 'success', 'user_address': addresses,
                'user_profile': user_profile, 'products': products}, 200


class ContactUsInfo(Resource):
    def get(self):
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM contact_us')
        contact_us_info = cur.fetchall()
        contact_us_info = list(contact_us_info)
        return {'message': 'Success', 'contact_us_info': contact_us_info}, 200


class AddReview(Resource):
    def post(self):
        user_id = redis_client.get('user_id')
        data = request.json
        product_id = data.get('product_id')
        review = data.get('review')
        rating = data.get('rating')
        name = data.get('name')
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO reviews(pro_id,u_id,rating,comment,date,name) VALUES(%s,%s,%s,%s,%s,%s)',
                    (product_id, user_id, rating, review, datetime.today(), name))
        mysql.connection.commit()
        cur.close()
        return {'message': 'Success'}


class SignOut(Resource):
    def get(self):
        redis_client.delete('user_id')

        return {"message": "Logged out successfully"}, 200

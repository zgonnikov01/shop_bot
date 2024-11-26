import datetime

from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session, selectinload

from config import load_config
from db.models import Base, User, Product, Order, OrderItem, Cart, CartItem, Notification
import sheets
import sheets.orders
import sheets.products
import sheets.users

config = load_config()
db_url = config.db.url

engine = create_engine(db_url, echo=False)

def create_db_and_tables():
    Base.metadata.create_all(engine)


def get_product(product_id=None, product_name=None) -> Product | None:
    with Session(engine) as session:
        if product_name:
            return session.query(Product).filter_by(name=product_name).first()
        return session.query(Product).filter_by(id=product_id).first()


def get_products(include_hidden=False):
    with Session(engine) as session:
        if include_hidden:
            return session.query(Product).order_by(Product.id).all()
        return session.query(Product).filter_by(is_hidden=False).order_by(Product.id).all()


def get_products_fancy(include_hidden=False):
    with Session(engine) as session:
        if include_hidden:
            return session.query(Product).order_by(Product.id).all()
        else:
            products = session.query(Product).filter_by(is_hidden=False).order_by(Product.id).all()
        products_pretty = []
        for product in products:
            products_pretty.append(f'{product.name}: {product.price}р.')
        return '\n'.join(products_pretty)


def create_product(name, description, categories, stock, picture, price, variant, is_hidden=False) -> Product:
    with Session(engine) as session:  
        new_product = Product(
            name=name,
            description=description,
            categories=categories,
            stock=stock,
            picture=picture,
            price=price,
            variant=variant,
            discount=0,
            is_hidden=is_hidden
        )
        session.add(new_product)
        session.commit()
        session.refresh(new_product)
        return new_product


def update_product(product_id=None, product_name=None, **kwargs) -> Product:
    with Session(engine) as session:
        if product_name:
            product = session.query(Product).filter_by(name=product_name).first()
        else:
            product = session.query(Product).filter_by(id=product_id).first()

        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        session.commit()
        session.refresh(product)
        return product


def get_order(order_id):
    with Session(engine) as session:
        return session.query(Order).filter_by(id=order_id).first()


def get_orders():
    with Session(engine) as session:
        return session.query(Order).all()
    

def check_and_fix_cart_stock(telegram_id) -> str | None:
    user = get_user_by_telegram_id(telegram_id=telegram_id)
    cart_items = get_cart_items_by_telegram_id(telegram_id=telegram_id)
    deleted={}
    for cart_item in cart_items:
        product = get_product(product_id=cart_item.product_id)
        if product.is_hidden:
            deleted[product.name] = cart_item.quantity
            remove_item_from_cart(cart_id=user.cart.id, product_id=product.id, quantity=cart_item.quantity)
        elif cart_item.quantity > product.stock:
            deleted[product.name] = cart_item.quantity - product.stock
            remove_item_from_cart(cart_id=user.cart.id, product_id=product.id, quantity=(cart_item.quantity - product.stock))
    if deleted:
        return '\n'.join([f'{item}: {value}' for item, value in deleted.items()])


#def check_and_fix_cart_stock(telegram_id) -> str | None:
#    with Session(engine) as session:
#        user = get_user_by_telegram_id(telegram_id=telegram_id)
#        cart_items = sorted(get_cart_items_by_telegram_id(telegram_id=telegram_id), key=lambda item: item.id)
#        products = sorted(sheets.products.get_products(), key=lambda item: item['id'])
#        
#        deleted = {}
#        for index, cart_item in enumerate(cart_items):
#            product = products[index]
#            while cart_item and cart_item.quantity > int(product['stock']):
#                if product['name'] not in deleted:
#                    deleted[product['name']] = 0
#                deleted[product['name']] += 1
#                cart_item = remove_item_from_cart(cart_id=user.cart.id, product_id=int(product['id']))
#        
#        if deleted:
#            return '\n'.join([f'{item}: {value}' for item, value in deleted.items()])


def create_order(telegram_id, delivery_cost):
    with Session(engine) as session:
        user = get_user_by_telegram_id(telegram_id)
        cart = get_cart(user.id)
        cart_items = get_cart_items_by_telegram_id(telegram_id)

        new_order = Order(
            customer_id=user.id,
            status='created',
            products_cost=cart.total,
            delivery_cost=delivery_cost,
            total=cart.total + delivery_cost,
            tracking_number=''
        )
        
        session.add(new_order)
        session.commit()

        for item in cart_items:
            order_item = OrderItem(
                product_id=item.product_id,
                quantity=item.quantity,
                order_id=new_order.id
            )
            session.add(order_item)
        session.commit()

        update_order(
            customer_id=user.id,
            order_id=new_order.id,
            customer_telegram_handle=user.telegram_handle,
            # items=session.query(OrderItem).filter_by(order_id=new_order.id).all(),
            status='Создан',
            products_cost=cart.total,
            delivery_cost=delivery_cost,
            total=cart.total + delivery_cost
        )
        
        # customer_id=mapped_column(ForeignKey('users.id')
        # customer_telegram_handle = mapped_column(ForeignKey('telegram_handle'))
        # items: Mapped[list['OrderItem']] = relationship()
        # status: Mapped[str]¡¡
        # products_cost: Mapped[int]
        # delivery_cost: Mapped[int]
        # total: Mapped[int]
        # tracking_number: Mapped[str]
        session.add(new_order)
        session.commit()
        session.refresh(new_order)

        sheets.orders.create(new_order, get_order_items_names(order_id=new_order.id))

        # clear_cart(cart_id=cart.id)
        
        return new_order


def update_order(order_id, **kwargs):
    with Session(engine) as session:
        order = session.query(Order).filter_by(id=order_id).first()
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        session.commit()
        return order


def delete_order(order_id):
    with Session(engine) as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if order:
            session.delete(order)
            session.commit()
        return order


def get_user(user_id: int) -> User:
    with Session(engine) as session:
        user = session.query(User).filter_by(id=user_id).options(selectinload(User.cart)).first()
        return user
    
def get_user_data_by_tg_id_fancy(user_tg_id, minimize=False):
    user = get_user_by_telegram_id(user_tg_id)
    data = [
        f'ID: <a href="tg://user?id={user_tg_id}">{user_tg_id}</a>',
        f'Ник в телеграм: {"@" + user.telegram_handle if user.telegram_handle else "-"}'
    ] if not minimize else []
    data += [
        f'Телефон: {user.phone_number}',
        f'Адрес: {user.address}',
        f'Почтовый индекс: {user.postal_code}'
    ]
    return '\n'.join(data)


def get_user_by_telegram_id(telegram_id):
    with Session(engine) as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).options(selectinload(User.cart)).first()
        return user
    

def get_cart_by_telegram_id(telegram_id):
    with Session(engine) as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).options(selectinload(User.cart)).first()
        cart = session.query(Cart).filter_by(owner_id=user.id).first()
        return cart

def get_cart_items_by_telegram_id(telegram_id) -> list[CartItem]:
    with Session(engine) as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        cart = session.query(Cart).filter_by(owner_id=user.id).first()
        cart_items = session.query(CartItem).filter_by(cart_id=cart.id).all()
        return cart_items
    

def get_cart_items_by_telegram_id_fancy(telegram_id) -> str:
    with Session(engine) as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        cart = session.query(Cart).filter_by(owner_id=user.id).first()
        cart_items = session.query(CartItem).filter_by(cart_id=cart.id).all()
        result = []
        current_total = 0
        for cart_item in cart_items:
            product = get_product(cart_item.product_id)
            price = product.price
            quantity = cart_item.quantity
            discount = product.discount
            if discount > 0:
                #result.append(f'<s>{product.name}: {str(quantity)} * {str(price)}р. = {str(quantity * price)}р.</s>')
                discount_price = price - discount
                result.append(f'{product.name}: {str(quantity)} * {str(discount_price)}р. = {str(quantity * discount_price)}р.')
                current_total += quantity * discount_price
            else:
                result.append(f'{product.name}: {str(quantity)} * {str(price)}р. = {str(quantity * price)}р.')
                current_total += quantity * price
        update_cart(cart_id=cart.id, total=current_total)

        delivery_cost = get_delivery_cost(cart_id=cart.id)

        result.append(f'Стоимость доставки по РФ: {delivery_cost}р.')
        result.append(f'\nОбщая сумма: {cart.total + delivery_cost}р.')
        result = '\n'.join(result)
        return result
    

def get_order_items_fancy(order_id) -> str:
    with Session(engine) as session:
        order_items = session.query(OrderItem).filter_by(order_id=order_id).all()
        result = []
        total = 0
        for order_item in order_items:
            product = get_product(order_item.product_id)
            price = product.price
            quantity = order_item.quantity
            discount = product.discount
            if discount > 0:
                #result.append(f'<s>{product.name}: {str(quantity)} * {str(price)}р. = {str(quantity * price)}р.</s>')
                discount_price = price - discount
                result.append(f'{product.name}: {str(quantity)} * {str(discount_price)}р. = {str(quantity * discount_price)}р.')
                total += quantity * discount_price
            else:
                result.append(f'{product.name}: {str(quantity)} * {str(price)}р. = {str(quantity * price)}р.')
                total += quantity * price

        delivery_cost = get_delivery_cost(order_id=order_id)

        result.append(f'Стоимость доставки по РФ: {delivery_cost}р.')
        result.append(f'\nОбщая сумма: {total + delivery_cost}р.')
        result = '\n'.join(result)
        return result


def decrease_stock(order_id):
    with Session(engine) as session:
        order_items = session.query(OrderItem).filter_by(order_id=order_id).all()
        for order_item in order_items:
            product = get_product(order_item.product_id)
            update_product(
                product_id=order_item.product_id,
                stock=product.stock - order_item.quantity
            )
        session.commit()


def get_delivery_cost(order_id=None, cart_id=None):
    with Session(engine) as session:
        if order_id:
            total = session.query(Order).filter_by(id=order_id).first().products_cost
        else:
            total = session.query(Cart).filter_by(id=cart_id).first().total

    if total < 5000:
        return 350
    return 0


def get_order_items_for_lifepay(order_id) -> str:
    with Session(engine) as session:
        order_items = session.query(OrderItem).filter_by(order_id=order_id).all()
        result = []
        for order_item in order_items:
            product = get_product(order_item.product_id)
            quantity = order_item.quantity
            result.append(f'{product.name} x {quantity}.0 = {product.price * quantity}.00')
        order = session.query(Order).filter_by(id=order_id).first()
        if order.delivery_cost > 0:
            result.append(f'Услуги сервиса доставки x {1}.0 = {order.delivery_cost}.00')
        return ', '.join(result)
    

def get_cart_item_by_telegram_id(telegram_id, product_id):
    with Session(engine) as session:
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            cart = user.cart
            cart_item = session.query(CartItem).filter_by(cart_id=cart.id, product_id=product_id).first()
            return cart_item
        except Exception as e:
            return None


def get_users():
    with Session(engine) as session:
        return session.query(User).all()


def create_user(telegram_id, telegram_handle, name, phone_number, address, postal_code):
    with Session(engine) as session:
        new_user = User(
            telegram_id=telegram_id,
            telegram_handle=telegram_handle,
            name=name,
            phone_number=phone_number,
            address=address,
            postal_code=postal_code,
            cart_msg_id='',
            catalog_msg_id='',
            order_msg_id=''
        )
        session.add(new_user)
        session.commit()
        new_user.cart = create_cart(owner_id=new_user.id)
        session.commit()    
        session.refresh(new_user)

        sheets.users.create(new_user)

        return new_user


def update_user(user_id, **kwargs):
    with Session(engine) as session:
        user = session.query(User).filter_by(id=user_id).first()
        #if 'cart' not in dir(user):
        if user.cart == None:
            user.cart = create_cart(owner_id=user.id)
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        session.commit()
        session.refresh(user)

        sheets.users.update(user)

        return user


def delete_user(user_id):
    with Session(engine) as session:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            session.delete(user)
            session.commit()
        return user
        

def get_cart(owner_id=None) -> Cart:
    with Session(engine) as session:
        cart = session.query(Cart).filter_by(owner_id=owner_id).first()
        return cart

def create_cart(owner_id) -> Cart:
    with Session(engine) as session:
        user = session.query(User).filter_by(id=owner_id).first()
        if user.cart != None:
            return user.cart
        new_cart = Cart(owner_id=owner_id, total=0)
        session.add(new_cart)
        session.commit()
        session.refresh(new_cart)
        return new_cart


def clear_cart(cart_id):
    with Session(engine) as session:
        session.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
        session.commit()
        cart = session.query(Cart).filter_by(id=cart_id).first()
        cart.total = 0
        session.commit()


def update_cart(cart_id, **kwargs):
    with Session(engine) as session:
        cart = session.query(Cart).filter_by(id=cart_id).first()
        for key, value in kwargs.items():
            if hasattr(cart, key):
                setattr(cart, key, value)
        session.commit()
        return cart


def add_item_to_cart(cart_id, product_id) -> CartItem | str:
    with Session(engine) as session:
        product = session.query(Product).filter_by(id=product_id).first()

        old_item = session.query(CartItem).filter_by(
            cart_id=cart_id,
            product_id=product_id
        ).first()
        
        # sheet_product = sheets.products.get_product(product_id)

        if old_item:
            if product.stock < old_item.quantity + 1:
                return None

            old_item.quantity = old_item.quantity + 1
            session.commit()
            session.refresh(old_item)
            cart_item = old_item
        else:
            if product.stock == 0:
                return None
            cart_item = CartItem(
                cart_id=cart_id,
                product_id=product_id, 
                quantity=1
            )
        
        cart = session.query(Cart).filter_by(id=cart_id).first()
        cart.total = cart.total + product.price - product.discount
        #session.commit()
        #session.refresh(cart)
        session.add(cart_item)
        session.commit()
        session.refresh(cart_item)
        return cart_item
    
    
def remove_item_from_cart(cart_id, product_id, quantity=1):
    with Session(engine) as session:
        cart = session.query(Cart).filter_by(id=cart_id).first()
        product = session.query(Product).filter_by(id=product_id).first()
        cart.total = max(0, cart.total - (product.price - product.discount) * quantity)
        #session.commit()
        #session.refresh(cart)

        cart_item = session.query(CartItem).filter_by(
            cart_id=cart_id,
            product_id=product_id
        ).first()
        
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity = max(0, cart_item.quantity - quantity)
                session.commit()
                session.refresh(cart_item)
            else:
                session.delete(cart_item)
        
        session.commit()


def get_cart_items(cart_id, owner_id=None):
    with Session(engine) as session:
        if owner_id:
            return session.query(CartItem).filter_by(
                owner_id=owner_id
            ).all()
        return session.query(CartItem).filter_by(
            cart_id=cart_id).all()


def get_order_items_names(order_id, customer_id=None):
    with Session(engine) as session:
        if customer_id:
            return [
                session.query(Product).filter_by(id=order_item.product_id).first().name + ': ' + \
                str(order_item.quantity) \
                for order_item in \
                session.query(OrderItem).filter_by(customer_id=customer_id).all()
            ]
        return [
                session.query(Product).filter_by(id=order_item.product_id).first().name + ': ' + \
                str(order_item.quantity) \
                for order_item in \
                session.query(OrderItem).filter_by(order_id=order_id).all()
            ]


def get_cart_item(cart_id, product_id):
    with Session(engine) as session:
        return session.query(CartItem).filter_by(
            cart_id=cart_id,
            product_id=product_id
        ).first()
    

def create_notification(text, media, expire_datetime):
    with Session(engine) as session:
        notification = Notification(
            text=text,
            media=media,
            expire_datetime=expire_datetime
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification


def get_notifications(include_expired=False):
    with Session(engine) as session:
        if include_expired:
            return session.query(Notification).all()
        return session.query(Notification).filter(Notification.expire_datetime > datetime.datetime.now()).all()


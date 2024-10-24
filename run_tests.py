from db.methods import create_order, get_user, get_products, create_db_and_tables, create_user, add_item_to_cart, remove_item_from_cart, get_cart_items
from db.models import Order, Product, OrderItem


create_db_and_tables()

user = get_user(create_user(123, '@maks', 'maks', 'admin', '23412345234').id)
print(user.cart)
add_item_to_cart(user.cart.id, get_products()[0].id)
print(get_cart_items(user.cart.id))
remove_item_from_cart(user.cart.id, get_products()[0].id)
print(get_cart_items(user.cart.id))


# products = get_products()
# print(products)
# create_order(
#     items=[OrderItem(quantity=1, product_id=product.id) for product in products],
#     status='',
#     products_cost=123,
#     delivery_cost=234,
#     total=123+234,
#     tracking_number='12345678'
# )


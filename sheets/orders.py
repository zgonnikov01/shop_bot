import gspread

from db.models import Order, OrderItem
from config import load_config

config = load_config()

gc = gspread.service_account(filename="token.json")
sh = gc.open_by_key(config.sheet_key)
wsh = sh.worksheet("Заказы")

def get_orders() -> list[dict]:
    data = wsh.get_all_values()
    
    
    fields = data[0]
    field_map = {field: index for index, field in enumerate(fields)}

    order_dicts = []
    for row in data[1:]:
        order_dicts.append({field: row[field_map[field]] for field in fields})
    
    orders = []

    for order_dict in order_dicts:
        orders.append(
            {
                'id': order_dict['ID заказа'],
                'customer_id': order_dict['ID клиента'],
                'items': order_dict['Товары'],
                'status': order_dict['Статус'],
                'products_cost': order_dict['Стоимость товаров'],
                'delivery_cost': order_dict['Стоимость доставки'],
                'total': order_dict['Итого'],
                'tracking_number': order_dict['Номер отслеживания'],
                'created_at': order_dict['Дата создания']
            }
        )
        
    return orders


def get_order(order_id) -> dict | None:
    orders = get_orders()
    for order in orders:
        if int(order['id']) == order_id:
            return order



def create(order: Order, order_items_names: list):
    formatted_items = ", ".join(order_items_names) if isinstance(order_items_names, list) else str(order_items_names)
    
    row = [
        order.id,                 # ID заказа
        order.customer_id,        # ID клиента
        formatted_items,          # Товары (you may need to format this appropriately)
        order.status,             # Статус
        order.products_cost,      # Стоимость продуктов
        order.delivery_cost,      # Стоимость доставки
        order.total,              # Итого
        order.tracking_number,    # Номер отслеживания
        order.created_at.strftime("%Y-%m-%d %H:%M:%S")  # Formatting datetime
    ]
    
    wsh.append_row(row)
    

def update_order_in_sheet(order: Order, order_items_names: list):
    # Search for the order by order.id in the spreadsheet
    cell = wsh.find(str(order.id))  # Find the cell with the order ID
    
    if cell:
        # If the order exists, we can update the corresponding row
        row_number = cell.row  # Get the row number where the order ID is found
        
        # Format the items appropriately
        formatted_items = ", ".join(order_items_names) if isinstance(order_items_names, list) else str(order_items_names)
        
        # Prepare the updated row values
        updated_row = [
            order.id,                             # ID заказа
            order.customer_id,                    # ID клиента
            formatted_items,                      # Товары
            order.status,                         # Статус
            order.products_cost,                  # Стоимость продуктов
            order.delivery_cost,                  # Стоимость доставки
            order.total,                          # Итого
            order.tracking_number,                # Номер отслеживания
            order.created_at.strftime("%Y-%m-%d %H:%M:%S")  # Formatting datetime
        ]
        
        # Update the row in the spreadsheet based on the found row number
        try:
            wsh.update(f'A{row_number}:I{row_number}', [updated_row])
            print(f"Order updated successfully.")
        except Exception as e:
            print(f"Failed to update order {order.id}: {e}")
    else:
        print(f"Order not found in the spreadsheet.")
        
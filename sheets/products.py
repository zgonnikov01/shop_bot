import gspread

from db.models import Product
from config import load_config

config = load_config()

gc = gspread.service_account(filename="token.json")
sh = gc.open_by_key(config.sheet_key)
wsh = sh.worksheet("Товары")

def get_products() -> list[dict]:
    data = wsh.get_all_values()
    
    
    fields = data[0]
    field_map = {field: index for index, field in enumerate(fields)}

    product_dicts = []
    for row in data[1:]:
        product_dicts.append({field: row[field_map[field]] for field in fields})
    
    products = []

    for product_dict in product_dicts:
        products.append(
            {
                'name': product_dict['Наименование'],
                'description': product_dict['Описание'],
                'categories': product_dict['Разделы'],
                'variant': product_dict['Фасовка'],
                'stock': product_dict['Остаток'],
                'price': product_dict['Цена'],
                'id': product_dict['ID'],
                'picture': ''
            }
        )
        
    return products


def get_product(product_id) -> dict | None:
    products = get_products()
    for product in products:
        if int(product['id']) == product_id:
            return product



def set_id(name: str, id: int) -> None:
    data = wsh.get_all_values()

    fields = data[0]
    field_map = {field: index for index, field in enumerate(fields)}

    print('trying to update...')
    for index, row in enumerate(data[1:]):
        if row[field_map['Наименование']] == name:
            wsh.update_cell(index + 2, field_map['ID'] + 1, id)
    print('updated')
    

def update(products: list[Product]):
    for product in products:
        cell = wsh.find(str(product.id))
        if cell:
            try:
                wsh.update_cell(cell.row, cell.col + 5, product.stock)
                print(f'Product "{product.name}" stock updated successfully.')
            except Exception as e:
                print(f'Failed to update product "{product.name}": {e}')
        else:
            print(f'Product not found in the spreadsheet.')
     

def decrease_stock(decrease_data):
    for dd in decrease_data:
        product_id, product_stock = dd
        cell = wsh.find(str(product_id))
        if cell:
            try:
                wsh.update_cell(cell.row, cell.col + 5, product_stock)
            except Exception as e:
                print(f'Failed to update product "{product_id}": {e}')
        else:
            print(f'Product not found in the spreadsheet.')


import gspread

from db.models import User
from config import load_config

config = load_config()

gc = gspread.service_account(filename="token.json")
sh = gc.open_by_key(config.sheet_key)
wsh = sh.worksheet("Клиенты")

def create(user: User):
    
    row = [
        user.id,                                        # ID пользователя
        user.telegram_id,                               # ID Телеграм
        user.telegram_handle,                           # Телеграм Handle
        user.name,                                      # Имя пользователя
        user.phone_number,                              # Номер телефона
        user.address,                                   # Адрес
        user.postal_code,                               # Почтовый индекс
        user.created_at.strftime("%Y-%m-%d %H:%M:%S"),  # Дата создания (formatted as YYYY-MM-DD HH:MM:SS)
    ]
    
    wsh.append_row(row)
    

def update(user: User):
    cell = wsh.find(str(user.id))  # Find the cell with the user ID
    
    if cell:
        row_number = cell.row
        
        # Prepare the updated row values
        updated_row = [
            user.id,                                        # ID пользователя
            user.telegram_id,                               # ID Телеграм
            user.telegram_handle,                           # Телеграм Handle
            user.name,                                      # Имя пользователя
            user.phone_number,                              # Номер телефона
            user.address,                                   # Адрес
            user.postal_code,                               # Почтовый индекс
            user.created_at.strftime("%Y-%m-%d %H:%M:%S"),  # Дата создания (formatted as YYYY-MM-DD HH:MM:SS)
        ]
        
        # Update the row in the spreadsheet based on the found row number
        try:
            wsh.update(f'A{row_number}:I{row_number}', [updated_row])
            print(f"User updated successfully.")
        except Exception as e:
            print(f"Failed to update user {user.id}: {e}")
    else:
        print(f"User not found in the spreadsheet.")
        
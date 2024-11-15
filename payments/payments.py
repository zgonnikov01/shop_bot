import requests
import json


from config import load_config


config = load_config()


def create_bill(
        amount: str,
        description: str,
        customer_phone: str
):
    r = requests.post(
        'https://api.life-pay.ru/v1/bill',
        json={
            'apikey': config.lifepay.apikey,
            'login': config.lifepay.login,
            'amount': amount,
            'description': description,
            'customer_phone': customer_phone,
            'method': 'sbp',
        }
    )
    return json.loads(r.text)


def get_bill_status(number):
    r = requests.get(
        'https://api.life-pay.ru/v1/bill/status',
        params={
            'apikey': config.lifepay.apikey,
            'login': config.lifepay.login,
            'number': str(number)
        }
    )
    return json.loads(r.text)
    

def cancel_bill(number):
    r = requests.get(
        'https://api.life-pay.ru/v1/bill/cancellation',
        params={
            'apikey': config.lifepay.apikey,
            'login': config.lifepay.login,
            'number': str(number)
        }
    )
    return json.loads(r.text)


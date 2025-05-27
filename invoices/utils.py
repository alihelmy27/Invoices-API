import requests
from rest_framework import status
from rest_framework.response import Response

from invoices_api import settings

api_key = settings.EXCHANGE_API_KEY
base_url = settings.EXCHANGE_API_URL

def get_supported_currencies():
    url = f"{base_url}/{api_key}/codes"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    # data['supported_codes'] is a list like [['USD', 'United States Dollar'], ...]
    return [code[0] for code in data["supported_codes"]]


def get_exchange_rate(from_currency, to_currency="USD"):
    url = f"{base_url}/{api_key}/latest/{from_currency}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    rates = data["conversion_rates"]
    return rates.get(to_currency)
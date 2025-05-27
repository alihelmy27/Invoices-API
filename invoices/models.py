# invoices/models.py

import mongoengine as me
import requests
from invoices_api import settings
from datetime import datetime


class Invoice(me.Document):
    amount = me.FloatField(required=True)
    currency = me.StringField(max_length=10, required=True)
    converted_amount = me.FloatField(default=0)
    exchange_rate = me.FloatField(default=1.0)
    created_at = me.DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        if not self.converted_amount or not self.exchange_rate:
            self.converted_amount, self.exchange_rate = self.convert_to_usd()
        if not self.created_at:
            self.created_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def convert_to_usd(self):
        base_url = settings.EXCHANGE_API_URL
        api_key = settings.EXCHANGE_API_KEY
        url = f"{base_url}/{api_key}/pair/{self.currency}/USD/{self.amount}"

        try:
            response = requests.get(url)
            data = response.json()
            if data.get("result") == "success":
                return data.get("conversion_result", self.amount), data.get(
                    "conversion_rate", 1.0
                )
        except Exception as e:
            print("Currency API error:", e)
        return self.amount, 1.0

# invoices/serializers.py

from rest_framework import serializers


class InvoiceSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    amount = serializers.FloatField()
    currency = serializers.CharField(max_length=10)
    converted_amount = serializers.FloatField(read_only=True)
    exchange_rate = serializers.FloatField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

# invoices/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import requests
from invoices_api import settings
from .models import Invoice
from .serializers import InvoiceSerializer
from mongoengine.errors import DoesNotExist
from .utils import get_exchange_rate,get_supported_currencies

api_key = settings.EXCHANGE_API_KEY
base_url = settings.EXCHANGE_API_URL

def get_object(pk):
    return Invoice.objects.get(id=pk)

class InvoiceListCreateAPIView(APIView):
    def get(self, request):
        invoices = Invoice.objects()
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InvoiceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data.get("amount")
        currency = serializer.validated_data.get("currency")
        try:
            supported_currencies = get_supported_currencies()
        except Exception as e:
            return Response(
                {
                    "detail": f"Unable to retrieve supported currencies at this time.Due To: {str(e)}"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if currency not in supported_currencies:
            return Response(
                {
                    "currency": f"Unsupported currency '{currency}'. Supported currencies: {supported_currencies}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Get exchange rate to USD
        try:
            exchange_rate = get_exchange_rate(currency, "USD")
        except Exception as e:
            return Response(
                {
                    "detail": f"Exchange rate for currency '{currency}' is not available."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        converted_amount = amount * exchange_rate
        invoice = Invoice(
            amount=amount,
            currency=currency,
            converted_amount=converted_amount,
            exchange_rate=exchange_rate,
        )
        invoice.save()
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

class InvoiceDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            invoice = get_object(pk)
        except DoesNotExist as e:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        json_data = InvoiceSerializer(invoice)
        return Response(json_data.data,status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            invoice = get_object(pk)
        except DoesNotExist as e:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        json_data = InvoiceSerializer(data=request.data)
        if json_data.is_valid():
            invoice.amount = json_data.validated_data["amount"]
            invoice.currency = json_data.validated_data["currency"]
            try:
                supported_currencies = get_supported_currencies()
            except Exception as e:
                return Response(
                    {
                        "detail": f"Unable to retrieve supported currencies at this time.Due To: {str(e)}"
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            if invoice.currency not in supported_currencies:
                return Response(
                    {
                        "currency": f"Unsupported currency '{invoice.currency}'. Supported currencies: {supported_currencies}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            invoice.converted_amount = 0  # reset to force recalculation
            invoice.save()
            return Response(InvoiceSerializer(invoice).data,status=status.HTTP_204_NO_CONTENT)
        return Response(json_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            invoice = get_object(pk)
        except DoesNotExist as e:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        invoice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class InvoiceExchangeRateAPIView(APIView):
    def get(self, request, pk):
        try:
            invoice = get_object(pk)
        except DoesNotExist as e :
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "currency": invoice.currency,
                "exchange_rate": invoice.exchange_rate
            }
        )


class TotalRevenueAPIView(APIView):
    def get(self, request):
        target_currency = request.query_params.get("currency", "USD").upper()
        try:
            supported_currencies = get_supported_currencies()
        except Exception as e:
            return Response(
                {
                    "detail": f"Unable to retrieve supported currencies at this time.Due To: {str(e)}"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if target_currency not in supported_currencies:
            return Response(
                {
                    "currency": f"Unsupported currency '{target_currency}'. Supported currencies: {supported_currencies}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        invoices = Invoice.objects()
        if not invoices:
            return Response(
                {"currency": target_currency, "total_revenue": 0.0}
            )
        # Sum of all converted_amounts (they're in USD)
        total_usd = sum(invoice.converted_amount for invoice in Invoice.objects)

        # No need to convert
        if target_currency == "USD":
            return Response({"currency": "USD", "total_revenue": round(total_usd, 2)})

        # Convert total USD revenue to requested currency
        try:
            url = f"{base_url}/{api_key}/pair/USD/{target_currency}/{total_usd}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            converted_total = data["conversion_result"]
            return Response(
                {
                    "currency": target_currency,
                    "total_revenue": round(converted_total, 2),
                }
            )
        except Exception as e:
            return Response(
                {"detail": f"Failed to convert USD to {target_currency}: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AverageInvoiceAPIView(APIView):
    def get(self, request):
        target_currency = request.query_params.get("currency", "USD").upper()
        try:
            supported_currencies = get_supported_currencies()
        except Exception as e:
            return Response(
                {
                    "detail": f"Unable to retrieve supported currencies at this time.Due To: {str(e)}"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if target_currency not in supported_currencies:
            return Response(
                {
                    "currency": f"Unsupported currency '{target_currency}'. Supported currencies: {supported_currencies}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        invoices = Invoice.objects()

        if not invoices:
            return Response(
                {"currency": target_currency, "average_invoice": 0.0, "count": 0}
            )

        total_usd = sum(inv.converted_amount for inv in invoices)
        count = invoices.count()
        avg_usd = total_usd / count

        # No conversion needed
        if target_currency == "USD":
            return Response(
                {
                    "currency": "USD",
                    "average_invoice": round(avg_usd, 2)
                }
            )

        # Convert average to requested currency
        try:
            url = f"{base_url}/{api_key}/pair/USD/{target_currency}/{avg_usd}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            converted_avg = data["conversion_result"]
            return Response(
                {
                    "currency": target_currency,
                    "average_invoice": round(converted_avg, 2),
                }
            )
        except Exception as e:
            return Response(
                {"detail": f"Failed to convert USD to {target_currency}: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

import json
from mongoengine import get_db
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from invoices.models import Invoice
from django.urls import reverse

class InvoiceListCreateAPIViewTests(APITestCase):

    @patch("invoices.views.get_supported_currencies")
    @patch("invoices.views.get_exchange_rate")
    def test_create_invoice_success(self, mock_get_exchange_rate, mock_get_supported_currencies):
        mock_get_supported_currencies.return_value = ['USD', 'EUR', 'EGP']
        mock_get_exchange_rate.return_value = 30.0  # 1 EGP = 30 USD

        data = {
            "amount": 100,
            "currency": "EGP"
        }
        self.url = reverse("invoice-list-create")
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['currency'], 'EGP')
        self.assertEqual(response.data['converted_amount'], 3000.0)
        self.assertTrue(Invoice.objects(currency="EGP"))

    @patch("invoices.views.get_supported_currencies")
    def test_create_invoice_invalid_currency(self, mock_get_supported_currencies):
        mock_get_supported_currencies.return_value = ['USD', 'EUR']

        data = {
            "amount": 50,
            "currency": "XYZ"
        }
        self.url = reverse("invoice-list-create")
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("currency", response.data)

    def test_create_invoice_missing_fields(self):
        self.url = reverse("invoice-list-create")
        response = self.client.post(self.url, {"amount": 100}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("invoices.views.get_supported_currencies")
    def test_supported_currency_api_failure(self, mock_get_supported_currencies):
        mock_get_supported_currencies.side_effect = Exception("API Error")
        data = {"amount": 100, "currency": "USD"}
        self.url = reverse("invoice-list-create")
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("invoices.views.get_supported_currencies")
    @patch("invoices.views.get_exchange_rate")
    def test_exchange_rate_failure(self, mock_get_exchange_rate, mock_get_supported_currencies):
        mock_get_supported_currencies.return_value = ['USD', 'EGP']
        mock_get_exchange_rate.side_effect = Exception("API Down")

        data = {"amount": 100, "currency": "EGP"}
        self.url = reverse("invoice-list-create")
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("detail", response.data)

    def test_list_invoices_empty(self):
        self.url = reverse("invoice-list-create")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @patch("invoices.views.get_supported_currencies")
    @patch("invoices.views.get_exchange_rate")
    def test_list_invoices_with_data(self, mock_get_exchange_rate, mock_get_supported_currencies):
        # Create one invoice
        mock_get_supported_currencies.return_value = ['USD', 'EGP']
        mock_get_exchange_rate.return_value = 30.0
        self.url = reverse("invoice-list-create")
        self.client.post(self.url, {"amount": 100, "currency": "EGP"}, format='json')

        # Now fetch them
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def tearDown(self):
        db = get_db()
        for collection_name in db.list_collection_names():
            db.drop_collection(collection_name)


class InvoiceDetailAPIViewTests(APITestCase):
    def setUp(self):
        self.invoice = Invoice(amount=100, currency="EUR", exchange_rate=1.1, converted_amount=110)
        self.invoice.save()
        self.detail_url = reverse("invoice-detail", kwargs={"pk": str(self.invoice.id)})

    def tearDown(self):
        Invoice.objects.delete()

    def test_get_invoice_success(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["amount"], 100)
        self.assertEqual(response.data["currency"], "EUR")

    def test_get_invoice_not_found(self):
        fake_id = "666f6f6f6f6f6f6f6f6f6f6f"
        url = reverse("invoice-detail", kwargs={"pk": fake_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Not found")

    @patch("invoices.utils.get_exchange_rate", return_value=1.2)
    @patch("invoices.utils.get_supported_currencies", return_value=["USD", "EUR"])
    def test_put_invoice_success(self, mock_currencies, mock_rate):
        data = {"amount": 250, "currency": "USD"}
        response = self.client.put(self.detail_url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        updated = Invoice.objects.get(id=self.invoice.id)
        self.assertEqual(updated.amount, 250)
        self.assertEqual(updated.currency, "USD")

    def test_put_invoice_invalid_data(self):
        data = {"amount": "", "currency": ""}
        response = self.client.put(self.detail_url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_invoice_not_found(self):
        fake_id = "666f6f6f6f6f6f6f6f6f6f6f"
        url = reverse("invoice-detail", kwargs={"pk": fake_id})
        data = {"amount": 300, "currency": "USD"}
        response = self.client.put(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_invoice_success(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_delete_invoice_not_found(self):
        fake_id = "666f6f6f6f6f6f6f6f6f6f6f"
        url = reverse("invoice-detail", kwargs={"pk": fake_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Not found")


class InvoiceExchangeRateAPIViewTests(APITestCase):
    def setUp(self):
        self.invoice = Invoice(
            amount=100,
            currency="EUR",
            exchange_rate=1.1,
            converted_amount=110
        )
        self.invoice.save()
        self.url = reverse("invoice-exchange-rate", kwargs={"pk": str(self.invoice.id)})

    def tearDown(self):
        Invoice.objects.delete()

    def test_get_exchange_rate_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["exchange_rate"], 1.1)

    def test_get_exchange_rate_not_found(self):
        fake_id = "666f6f6f6f6f6f6f6f6f6f6f"  # Non-existent ObjectId
        url = reverse("invoice-exchange-rate", kwargs={"pk": fake_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Not found")


class TotalRevenueAPIViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("total-revenue")
        self.invoice1 = Invoice.objects.create(
            amount=100,
            currency="EUR",
            exchange_rate=1.1,
            converted_amount=110,
        )
        self.invoice2 = Invoice.objects.create(
            amount=200,
            currency="GBP",
            exchange_rate=1.25,
            converted_amount=250,
        )

    def tearDown(self):
        Invoice.objects.delete()

    @patch("invoices.views.get_supported_currencies")
    def test_total_revenue_usd_success(self, mock_supported):
        mock_supported.return_value = ["USD", "EUR", "GBP"]
        response = self.client.get(self.url + "?currency=USD")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currency"], "USD")
        self.assertEqual(response.data["total_revenue"], round(110 + 250, 2))

    @patch("invoices.views.get_supported_currencies")
    @patch("invoices.views.requests.get")
    def test_total_revenue_foreign_currency_success(
        self, mock_requests_get, mock_supported
    ):
        mock_supported.return_value = ["USD", "EUR", "GBP"]
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "conversion_result": 500.00
        }

        response = self.client.get(self.url + "?currency=EUR")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["total_revenue"], 500.00)

    @patch("invoices.views.get_supported_currencies")
    def test_total_revenue_invalid_currency(self, mock_supported):
        mock_supported.return_value = ["USD", "EUR", "GBP"]
        response = self.client.get(self.url + "?currency=XYZ")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unsupported currency", response.data["currency"])

    @patch("invoices.views.get_supported_currencies")
    @patch("invoices.views.requests.get")
    def test_total_revenue_exchange_api_failure(
        self, mock_requests_get, mock_supported
    ):
        mock_supported.return_value = ["USD", "EUR"]
        mock_requests_get.side_effect = Exception("Conversion API failed")

        response = self.client.get(self.url + "?currency=EUR")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Failed to convert USD to EUR", response.data["detail"])


class AverageInvoiceAPIViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("average-invoice")
        # Add some test invoices
        self.invoice1 = Invoice.objects.create(
            amount=100,
            currency="EUR",
            exchange_rate=1.1,
            converted_amount=110,
        )
        self.invoice2 = Invoice.objects.create(
            amount=200,
            currency="GBP",
            exchange_rate=1.25,
            converted_amount=250,
        )

    def tearDown(self):
        Invoice.objects.delete()

    @patch("invoices.views.get_supported_currencies")
    def test_average_invoice_usd_success(self, mock_supported):
        mock_supported.return_value = ["USD", "EUR", "GBP"]
        response = self.client.get(self.url + "?currency=USD")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currency"], "USD")
        expected_avg = round((110 + 250) / 2, 2)
        self.assertEqual(response.data["average_invoice"], expected_avg)

    @patch("invoices.views.get_supported_currencies")
    @patch("invoices.views.requests.get")
    def test_average_invoice_foreign_currency_success(
        self, mock_requests_get, mock_supported
    ):
        mock_supported.return_value = ["USD", "EUR", "GBP"]
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "conversion_result": 180.00
        }

        response = self.client.get(self.url + "?currency=EUR")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["average_invoice"], 180.00)

    @patch("invoices.views.get_supported_currencies")
    def test_average_invoice_unsupported_currency(self, mock_supported):
        mock_supported.return_value = ["USD", "EUR", "GBP"]
        response = self.client.get(self.url + "?currency=ABC")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unsupported currency", response.data["currency"])

    @patch("invoices.views.get_supported_currencies")
    @patch("invoices.views.requests.get")
    def test_average_invoice_conversion_api_failure(
        self, mock_requests_get, mock_supported
    ):
        mock_supported.return_value = ["USD", "EUR"]
        mock_requests_get.side_effect = Exception("Conversion failed")

        response = self.client.get(self.url + "?currency=EUR")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Failed to convert USD to EUR", response.data["detail"])

    @patch("invoices.views.get_supported_currencies")
    def test_average_invoice_no_data(self, mock_supported):
        # Clean invoices and try again
        Invoice.objects.delete()
        mock_supported.return_value = ["USD", "EUR", "GBP"]

        response = self.client.get(self.url + "?currency=USD")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currency"], "USD")
        self.assertEqual(response.data["average_invoice"], 0.0)
        self.assertEqual(response.data["count"], 0)
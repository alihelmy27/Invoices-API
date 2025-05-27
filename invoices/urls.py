# invoices/urls.py

from django.urls import path
from .views import (
    InvoiceListCreateAPIView,
    InvoiceDetailAPIView,
    InvoiceExchangeRateAPIView,
    TotalRevenueAPIView,
    AverageInvoiceAPIView,
)

urlpatterns = [
    path("invoices/", InvoiceListCreateAPIView.as_view(), name="invoice-list-create"),
    path("invoices/<str:pk>", InvoiceDetailAPIView.as_view(), name="invoice-detail"),
    path(
        "invoices/<str:pk>/exchange-rate",
        InvoiceExchangeRateAPIView.as_view(),
        name="invoice-exchange-rate",
    ),
    path(
        "analytics/total-revenue/", TotalRevenueAPIView.as_view(), name="total-revenue"
    ),
    path(
        "analytics/average-invoice/",
        AverageInvoiceAPIView.as_view(),
        name="average-invoice",
    ),
]

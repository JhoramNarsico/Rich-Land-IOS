"""
Module for handling all inventory-related URL routing.

This file centralizes the URL configurations for various inventory features,
including product management, sales, procurement, and reporting, to enhance
readability and maintainability.
"""

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'inventory'

urlpatterns = [
    # --- INVENTORY CORE ---
    # Main product views and actions
    path('', views.ProductListView.as_view(), name='product_list'),
    path('product/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/<slug:slug>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('product/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Custom Product Actions
    path('product/<slug:slug>/toggle_status/', views.product_toggle_status, name='product_toggle_status'),
    path('product/<slug:slug>/refund/', views.product_refund, name='product_refund'),
    path('products/import/', views.import_products, name='product_import'),
    
    # AJAX Endpoints
    path('ajax/category/add/', views.add_category_ajax, name='add_category_ajax'),
    path('ajax/expense-category/add/', views.add_expense_category_ajax, name='add_expense_category_ajax'),
    path('products/search/', views.search_products, name='product_search'),
    path('api/sales-chart-data/', views.sales_chart_data, name='sales_chart_data'),

    # --- ANALYTICS AND REPORTING ---
    path('history/', views.ProductHistoryListView.as_view(), name='product_history_list'),
    path('product/<slug:slug>/history/', views.ProductHistoryDetailView.as_view(), name='product_history_detail'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('reports/', views.ReportingView.as_view(), name='reporting'),
    path('analytics/', views.analytics_dashboard, name='analytics'),

    # --- SUPPLIERS AND PURCHASE ORDERS ---
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='purchaseorder_list'),
    path('purchase-orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchaseorder_detail'),
    path('purchase-orders/<int:pk>/receive/', views.receive_purchase_order, name='purchaseorder_receive'),
    
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/import/', views.import_supplier_deliveries, name='supplier_deliveries_import'),

    # --- POINT OF SALE (POS) TRANSACTIONS ---
    path('pos/', views.pos_dashboard, name='pos_dashboard'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),
    path('pos/sow/new/', views.pos_sow_create, name='pos_sow_create'),
    path('pos/history/', views.POSHistoryListView.as_view(), name='pos_history'),
    path('pos/receipt/<str:receipt_id>/', views.POSReceiptDetailView.as_view(), name='pos_receipt_detail'),

    # --- CUSTOMER RELATIONSHIP MANAGEMENT (CRM) ---
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/import-ledger/', views.import_ledger_entries, name='customer_ledger_import'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/update/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/payment/', views.customer_payment, name='customer_payment'),
    path('customers/<int:pk>/export/', views.export_statement, name='customer_statement_export'),
    path('customers/<int:pk>/sow/new/', views.hydraulic_sow_create, name='hydraulic_sow_create'),
    path('customers/templates/ledger/', views.download_ledger_template, name='download_ledger_template'),
    path('customers/<int:pk>/sow/<int:sow_pk>/update/', views.hydraulic_sow_update, name='hydraulic_sow_update'),
    path('sow/import/', views.hydraulic_sow_import, name='hydraulic_sow_import'),
    path('customers/<int:pk>/sow/export/', views.export_sow_history, name='customer_sow_export'),
    path('customers/<int:pk>/sow/import/', views.import_sow_history, name='customer_sow_import'),
    path('customers/templates/sow/', views.download_sow_template, name='download_sow_template'),

    # --- FINANCIALS AND EXPENSES ---
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/import/', views.import_expenses, name='expense_import'),
    path('expenses/templates/download/', views.download_expense_template, name='download_expense_template'),
    path('expenses/<int:pk>/update/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
]

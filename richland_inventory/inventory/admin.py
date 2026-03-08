from django.contrib import admin
from django.utils import timezone
from django.db import transaction, models
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Product, Category, StockTransaction, Supplier, PurchaseOrder, PurchaseOrderItem,
    Customer, CustomerPayment, HydraulicSow, POSSale, Expense, ExpenseCategory,
    PriceOverrideLog
)
from django.utils.html import format_html
from django.urls import reverse
from django.db.models.functions import Coalesce
from decimal import Decimal
from core.cache_utils import clear_dashboard_cache

admin.site.site_header = "Rich Land Admin"
admin.site.site_title = "Rich Land Admin Portal"
admin.site.index_title = "Welcome to the Rich Land Inventory Portal"

# --- Core Inventory ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

class StockTransactionInline(admin.TabularInline):
    model = StockTransaction
    extra = 0
    fields = ('product', 'quantity', 'selling_price', 'transaction_type', 'transaction_reason')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'quantity', 'status', 'last_edited_on')
    list_filter = ('status', 'category', 'date_updated')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('status',)
    history_list_display = ["status", "quantity", "price"]
    autocomplete_fields = ('category',)

    def get_readonly_fields(self, request, obj=None):
        if obj: # On the change form, make quantity readonly
            return ('quantity',)
        return () # On the add form, it's not readonly (but will be excluded)

    def get_exclude(self, request, obj=None):
        if obj is None: # On the add form, exclude quantity
            return ('quantity',)
        return () # On the change form, do not exclude it

    @admin.display(description='Last Edited On')
    def last_edited_on(self, obj):
        last_record = obj.history.first()
        if last_record:
            return last_record.history_date.strftime('%Y-%m-%d %H:%M')
        return "N/A"

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'product', 'transaction_type', 'transaction_reason', 'quantity', 'user', 'pos_sale')
    list_filter = ('timestamp', 'transaction_type', 'transaction_reason', 'user')
    search_fields = ('product__name', 'pos_sale__receipt_id', 'notes')
    autocomplete_fields = ('product', 'user', 'pos_sale')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

# --- Customer Relationship Management ---

class CustomerPaymentInline(admin.TabularInline):
    model = CustomerPayment
    extra = 0
    fields = ('payment_date', 'amount', 'reference_number', 'notes')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

class HydraulicSowInline(admin.TabularInline):
    model = HydraulicSow
    extra = 0
    fields = ('date_created', 'application', 'hose_type', 'length')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_id', 'email', 'phone', 'credit_limit', 'balance')
    search_fields = ('name', 'customer_id', 'email', 'phone')
    inlines = [CustomerPaymentInline, HydraulicSowInline]
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        credit_sales = models.Sum('purchases__total_amount', filter=models.Q(purchases__payment_method='CREDIT'))
        total_payments = models.Sum('payments__amount')
        
        qs = qs.annotate(
            calculated_balance=models.ExpressionWrapper(
                Coalesce(credit_sales, Decimal('0.00')) - Coalesce(total_payments, Decimal('0.00')),
                output_field=models.DecimalField()
            )
        )
        return qs

    @admin.display(description='Current Balance', ordering='calculated_balance')
    def balance(self, obj):
        try:
            # Ensure balance is a Decimal. Handle SafeString or None.
            val = obj.calculated_balance
            if val is None:
                balance = Decimal('0.00')
            else:
                balance = Decimal(str(val))
        except (ValueError, TypeError, Exception):
            balance = Decimal('0.00')

        color = "green" if balance <= 0 else "red"
        return format_html('<span style="color: {}; font-weight: bold;">₱{}</span>', color, f"{balance:,.2f}")

@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'payment_date', 'reference_number', 'linked_sale', 'recorded_by')
    list_filter = ('payment_date',)
    search_fields = ('customer__name', 'reference_number', 'sale_paid__receipt_id')
    autocomplete_fields = ('customer', 'sale_paid', 'recorded_by')
    
    @admin.display(description='Applied to Invoice', ordering='sale_paid')
    def linked_sale(self, obj):
        if obj.sale_paid:
            link = reverse("admin:inventory_possale_change", args=[obj.sale_paid.id])
            return format_html('<a href="{}">{}</a>', link, obj.sale_paid.receipt_id)
        return "-"

@admin.register(HydraulicSow)
class HydraulicSowAdmin(admin.ModelAdmin):
    list_display = ('sow_id', 'customer', 'date_created', 'application', 'hose_type', 'cost')
    list_filter = ('date_created',)
    search_fields = ('customer__name', 'application', 'notes', 'sow_id')
    autocomplete_fields = ('customer',)

# --- Point of Sale ---

@admin.register(POSSale)
class POSSaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_id', 'timestamp', 'customer', 'total_amount', 'payment_method', 'cashier', 'override_flag')
    list_filter = ('timestamp', 'payment_method', 'cashier', 'has_price_override')
    search_fields = ('receipt_id', 'customer__name')
    inlines = [StockTransactionInline]
    autocomplete_fields = ('customer', 'cashier')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False
    
    @admin.display(description='Override?', boolean=True)
    def override_flag(self, obj):
        return obj.has_price_override
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(PriceOverrideLog)
class PriceOverrideLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'pos_sale', 'product', 'salesman', 'original_price', 'override_price', 'price_difference')
    list_filter = ('timestamp', 'salesman', 'product')
    search_fields = ('pos_sale__receipt_id', 'product__name', 'salesman__username')
    date_hierarchy = 'timestamp'
    readonly_fields = ('pos_sale', 'product', 'salesman', 'original_price', 'override_price', 'reason', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# --- Suppliers & Purchasing ---

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    autocomplete_fields = ['product']
    readonly_fields = ('price', 'line_total_display')
    fields = ('product', 'quantity', 'price', 'line_total_display')

    def line_total_display(self, instance):
        if instance.pk:
            return f"{instance.line_total:,.2f}"
        return "-"
    line_total_display.short_description = "Total Amount"

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier_id', 'contact_person', 'email', 'phone')
    search_fields = ('name', 'supplier_id', 'contact_person', 'email')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'supplier', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('order_id', 'supplier__name')
    inlines = [PurchaseOrderItemInline]
    date_hierarchy = 'order_date'
    autocomplete_fields = ('supplier',)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, PurchaseOrderItem):
                if instance.price is None and instance.product:
                    instance.price = instance.product.price
            instance.save()
        formset.save_m2m()

# --- Expenses ---

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_date', 'description', 'category', 'amount', 'recorded_by')
    list_filter = ('expense_date', 'category')
    search_fields = ('description', 'category__name')
    autocomplete_fields = ('category', 'recorded_by')
    date_hierarchy = 'expense_date'
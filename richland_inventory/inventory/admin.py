"""
Django admin configuration for the inventory application.
Registers models and customizes the admin interface for easy management.
"""

from django.contrib import admin
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Q, DecimalField, OuterRef, Subquery, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from simple_history.admin import SimpleHistoryAdmin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin

from .models import (
    Product, Category, StockTransaction, Supplier, PurchaseOrder, PurchaseOrderItem,
    Customer, CustomerPayment, HydraulicSow, POSSale, Expense, ExpenseCategory,
    PriceOverrideLog
)
from core.cache_utils import clear_dashboard_cache

admin.site.site_header = "Rich Land Admin"
admin.site.site_title = "Rich Land Admin Portal"
admin.site.index_title = "Welcome to the Rich Land Inventory Portal"


# --- Core Inventory ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for product Categories."""
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class StockTransactionInline(admin.TabularInline):
    """Inline view for viewing Stock Transactions within related models."""
    model = StockTransaction
    extra = 0
    fields = ('product', 'quantity', 'selling_price', 'transaction_type', 'transaction_reason')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    """Admin configuration for Product models, tracking history and caching."""
    list_display = ('name', 'sku', 'category', 'price', 'quantity', 'status', 'last_edited_on')
    list_filter = ('status', 'category', 'date_updated')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('status',)
    history_list_display = ["status", "quantity", "price"]
    autocomplete_fields = ('category',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        clear_dashboard_cache()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        clear_dashboard_cache()

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
    """Admin configuration for direct viewing of Stock Transactions."""
    list_display = ('timestamp', 'product', 'transaction_type', 'transaction_reason', 'quantity', 'user', 'pos_sale')
    list_filter = ('timestamp', 'transaction_type', 'transaction_reason', 'user')
    search_fields = ('product__name', 'pos_sale__receipt_id', 'notes')
    autocomplete_fields = ('product', 'user', 'pos_sale')
    date_hierarchy = 'timestamp'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        clear_dashboard_cache()

    def delete_model(self, request, obj):
        # Restore stock if a transaction is manually deleted (e.g. error correction)
        with transaction.atomic():
            product = obj.product
            if obj.transaction_type == 'IN':
                product.quantity -= obj.quantity
            else:
                product.quantity += obj.quantity
            product.save()
            super().delete_model(request, obj)
            clear_dashboard_cache()

    def has_add_permission(self, request):
        return False


# --- Customer Relationship Management ---

class CustomerPaymentInline(admin.TabularInline):
    """Inline view for viewing Customer Payments."""
    model = CustomerPayment
    extra = 0
    fields = ('payment_date', 'amount', 'reference_number', 'notes')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class HydraulicSowInline(admin.TabularInline):
    """Inline view for viewing scopes of work tied to a customer."""
    model = HydraulicSow
    extra = 0
    fields = ('date_created', 'application', 'hose_type', 'length')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin configuration for Customer profiles and financial balances."""
    list_display = ('name', 'customer_id', 'email', 'phone', 'current_balance_display')
    search_fields = ('name', 'customer_id', 'email', 'phone')
    inlines = [CustomerPaymentInline, HydraulicSowInline]
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        # Optimized to avoid Cartesian product issues when summing multiple relations
        qs = super().get_queryset(request)
        
        credit_sales_subquery = POSSale.objects.filter(
            customer=OuterRef('pk'),
            payment_method='CREDIT'
        ).values('customer').annotate(
            total=Sum('total_amount')
        ).values('total')

        payments_subquery = CustomerPayment.objects.filter(
            customer=OuterRef('pk')
        ).values('customer').annotate(
            total=Sum('amount')
        ).values('total')

        return qs.annotate(
            _total_credit_sales=Coalesce(Subquery(credit_sales_subquery), Decimal('0.00'), output_field=DecimalField()),
            _total_payments_made=Coalesce(Subquery(payments_subquery), Decimal('0.00'), output_field=DecimalField())
        ).annotate(
            _balance=F('_total_credit_sales') - F('_total_payments_made')
        )

    @admin.display(description='Current Balance', ordering='_balance')
    def current_balance_display(self, obj):
        return f"{obj._balance:,.2f}"


@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    """Admin configuration for handling individual customer payments."""
    list_display = ('customer', 'amount', 'payment_date', 'reference_number', 'sale_paid', 'recorded_by')
    list_filter = ('payment_date',)
    search_fields = ('customer__name', 'reference_number', 'sale_paid__receipt_id')
    autocomplete_fields = ('customer', 'sale_paid', 'recorded_by')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        clear_dashboard_cache()


@admin.register(HydraulicSow)
class HydraulicSowAdmin(admin.ModelAdmin):
    """Admin configuration for customized scope of work requests."""
    list_display = ('customer', 'date_created', 'application', 'hose_type')
    list_filter = ('date_created',)
    search_fields = ('customer__name', 'application', 'notes')
    autocomplete_fields = ('customer',)


# --- Point of Sale ---

@admin.register(POSSale)
class POSSaleAdmin(admin.ModelAdmin):
    """Admin configuration for managing point of sale receipts."""
    list_display = ('receipt_id', 'timestamp', 'customer', 'total_amount', 'payment_method', 'cashier', 'has_price_override')
    list_filter = ('timestamp', 'payment_method', 'cashier', 'has_price_override')
    search_fields = ('receipt_id', 'customer__name')
    inlines = [StockTransactionInline]
    autocomplete_fields = ('customer', 'cashier')
    date_hierarchy = 'timestamp'

    def delete_model(self, request, obj):
        # Crucial: Restore stock when a sale is deleted from the admin
        with transaction.atomic():
            for item in obj.items.all():
                product = item.product
                product.quantity += item.quantity
                product.save()
            super().delete_model(request, obj)
            clear_dashboard_cache()

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PriceOverrideLog)
class PriceOverrideLogAdmin(admin.ModelAdmin):
    """Admin configuration for tracking sales price overrides."""
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
    """Inline view for adding items directly to a Purchase Order."""
    model = PurchaseOrderItem
    extra = 1
    autocomplete_fields = ['product']
    readonly_fields = ('line_total_display',) # price is NOT readonly so it can be edited/set
    fields = ('product', 'quantity', 'price', 'line_total_display')

    def line_total_display(self, instance):
        if instance.pk:
            return f"{instance.line_total:,.2f}"
        return "-"
    line_total_display.short_description = "Total Amount"


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin configuration for managing product vendors."""
    list_display = ('name', 'supplier_id', 'contact_person', 'email', 'phone')
    search_fields = ('name', 'supplier_id', 'contact_person', 'email')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin configuration for viewing and completing Purchase Orders."""
    list_display = ('order_id', 'supplier', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('order_id', 'supplier__name')
    inlines = [PurchaseOrderItemInline]
    date_hierarchy = 'order_date'
    autocomplete_fields = ('supplier',)

    def save_model(self, request, obj, form, change):
        if change:
            # Detect if status was changed to RECEIVED in the admin
            original = PurchaseOrder.objects.get(pk=obj.pk)
            if original.status != 'RECEIVED' and obj.status == 'RECEIVED':
                # Trigger the stock-in logic
                obj.status = original.status # Temporarily revert to trigger correctly
                obj.complete_order(request.user)
                clear_dashboard_cache()
                return # complete_order handles the save
        
        super().save_model(request, obj, form, change)
        clear_dashboard_cache()


# --- Expenses ---

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for organizing types of expenses."""
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Admin configuration for tracking business expenditures."""
    list_display = ('expense_date', 'description', 'category', 'amount', 'recorded_by')
    list_filter = ('expense_date', 'category')
    search_fields = ('description', 'category__name')
    autocomplete_fields = ('category', 'recorded_by')
    date_hierarchy = 'expense_date'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        clear_dashboard_cache()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        clear_dashboard_cache()


# --- User & Group Management (Simplified for Owner) ---

# Robustly unregister default models
if admin.site.is_registered(User):
    admin.site.unregister(User)
if admin.site.is_registered(Group):
    admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom UserAdmin that makes role (Group) assignment easier.
    Permissions are moved to a collapsed section.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_groups')
    filter_horizontal = ('groups', 'user_permissions')
    
    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Roles (Groups)'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Roles & Access', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
            'description': 'Assign user to a Group (e.g., Manager, Salesman) to grant permissions automatically.'
        }),
        ('Advanced Permissions', {
            'classes': ('collapse',),
            'fields': ('user_permissions',),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    """
    Custom GroupAdmin with filter_horizontal for permissions.
    """
    filter_horizontal = ('permissions',)
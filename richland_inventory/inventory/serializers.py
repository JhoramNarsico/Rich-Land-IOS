# inventory/serializers.py

from rest_framework import serializers
from .models import (
    Product, Category, Customer, CustomerPayment, HydraulicSow, 
    POSSale, StockTransaction, Expense, ExpenseCategory
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ProductSerializer(serializers.ModelSerializer):
    # Show the category name (Read Only) for better API readability
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 
            'name', 
            'sku', 
            'image',
            'category',       # The ID (for writing/updating)
            'category_name',  # The Name (for reading/displaying)
            'price', 
            'quantity', 
            'reorder_level',
            'status',
            'last_purchase_date',
            'date_created', 
            'date_updated'
        ]

# --- NEW SERIALIZERS ---

class CustomerSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, source='get_balance')

    class Meta:
        model = Customer
        fields = [
            'id', 'customer_id', 'name', 'email', 'phone', 'address', 
            'tax_id', 'credit_limit', 'balance', 'created_at', 'updated_at'
        ]

class CustomerPaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    recorded_by_username = serializers.CharField(source='recorded_by.username', read_only=True)
    sale_paid_receipt_id = serializers.CharField(source='sale_paid.receipt_id', read_only=True, allow_null=True)

    class Meta:
        model = CustomerPayment
        fields = [
            'id', 'customer', 'customer_name', 'sale_paid', 'sale_paid_receipt_id', 
            'amount', 'payment_date', 'reference_number', 'notes', 
            'recorded_by', 'recorded_by_username'
        ]
        read_only_fields = ['recorded_by'] # Set by the system

class HydraulicSowSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta:
        model = HydraulicSow
        fields = '__all__'
        read_only_fields = ['created_by'] # Set by the system

class StockTransactionSerializer(serializers.ModelSerializer):
    """Serializer for items within a POSSale."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = StockTransaction
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity', 'selling_price'
        ]

class POSSaleSerializer(serializers.ModelSerializer):
    cashier_username = serializers.CharField(source='cashier.username', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    items = StockTransactionSerializer(many=True, read_only=True)
    sow_details = serializers.SerializerMethodField()

    class Meta:
        model = POSSale
        fields = [
            'id', 'receipt_id', 'timestamp', 'cashier', 'cashier_username', 
            'customer', 'customer_name', 'payment_method', 'total_amount', 
            'amount_paid', 'change_given', 'has_price_override', 'notes', 'items',
            'sow_details'
        ]

    def get_sow_details(self, obj):
        """If this is a job receipt, fetch the associated Hydraulic SOW data."""
        if obj.receipt_id.startswith(('JOB-', 'SOW-')):
            sow = HydraulicSow.objects.filter(sow_id=obj.receipt_id).select_related('customer', 'created_by').first()
            if sow:
                return HydraulicSowSerializer(sow).data
        return None

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name']

class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', required=False, allow_blank=True, allow_null=True)
    recorded_by_username = serializers.CharField(source='recorded_by.username', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'category', 'category_name', 'description', 'amount', 
            'expense_date', 'receipt', 'recorded_by', 'recorded_by_username', 'date_created'
        ]
        read_only_fields = ['recorded_by', 'category']

    def _get_category(self, category_name):
        if category_name:
            category, _ = ExpenseCategory.objects.get_or_create(name=category_name.strip())
            return category
        return None

    def create(self, validated_data):
        category_name = validated_data.pop('category', {}).get('name')
        validated_data['category'] = self._get_category(category_name)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        category_name = validated_data.pop('category', {}).get('name')
        instance.category = self._get_category(category_name)
        return super().update(instance, validated_data)
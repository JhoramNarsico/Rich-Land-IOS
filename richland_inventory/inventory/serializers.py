"""
Data serializers for the inventory API.
Converts complex Django database models into native Python datatypes 
that can be easily rendered into JSON for the frontend POS and external clients.
"""

from rest_framework import serializers

from .models import (
    Product, Category, Customer, CustomerPayment, 
    HydraulicSow, POSSale, Expense, ExpenseCategory
)


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model.
    Exposes core product details for the POS interface and inventory APIs.
    """
    class Meta:
        model = Product
        fields =['id', 'name', 'sku', 'price', 'quantity', 'date_created', 'date_updated']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the product Category model."""
    class Meta:
        model = Category
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for the Customer billing profile model."""
    class Meta:
        model = Customer
        fields = '__all__'


class CustomerPaymentSerializer(serializers.ModelSerializer):
    """Serializer for tracking Customer Payments."""
    class Meta:
        model = CustomerPayment
        fields = '__all__'


class HydraulicSowSerializer(serializers.ModelSerializer):
    """Serializer for Hydraulic Scope of Work (SOW) custom jobs."""
    class Meta:
        model = HydraulicSow
        fields = '__all__'


class POSSaleSerializer(serializers.ModelSerializer):
    """Serializer for Point of Sale transactions and receipts."""
    class Meta:
        model = POSSale
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for company Expense records."""
    class Meta:
        model = Expense
        fields = '__all__'


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for Expense Categories."""
    class Meta:
        model = ExpenseCategory
        fields = '__all__'
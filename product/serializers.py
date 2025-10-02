from rest_framework import serializers
from decimal import Decimal
from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para Category"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'products_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_products_count(self, obj):
        """Retorna o número de produtos na categoria"""
        return obj.products.count()
    
    def validate_name(self, value):
        """Valida o nome da categoria"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("O nome da categoria deve ter pelo menos 2 caracteres.")
        return value.strip().title()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer para Product"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'author', 'isbn', 'description', 'price', 
            'stock_quantity', 'category', 'category_name', 'publication_date', 
            'is_active', 'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_isbn(self, value):
        """Valida o formato do ISBN"""
        # Remove espaços e hífens
        isbn_clean = value.replace('-', '').replace(' ', '')
        
        # Verifica se tem 13 dígitos
        if len(isbn_clean) != 13:
            raise serializers.ValidationError("ISBN deve ter 13 dígitos.")
        
        # Verifica se todos são dígitos
        if not isbn_clean.isdigit():
            raise serializers.ValidationError("ISBN deve conter apenas números.")
        
        return isbn_clean
    
    def validate_price(self, value):
        """Valida o preço do produto"""
        if value <= Decimal('0'):
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        
        if value > Decimal('9999.99'):
            raise serializers.ValidationError("O preço não pode exceder R$ 9.999,99.")
        
        return value
    
    def validate_stock_quantity(self, value):
        """Valida a quantidade em estoque"""
        if value < 0:
            raise serializers.ValidationError("A quantidade em estoque não pode ser negativa.")
        
        return value
    
    def validate_title(self, value):
        """Valida o título do produto"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("O título deve ter pelo menos 3 caracteres.")
        
        return value.strip()
    
    def validate_author(self, value):
        """Valida o nome do autor"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("O nome do autor deve ter pelo menos 2 caracteres.")
        
        return value.strip()


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de produtos"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'author', 'isbn', 'price', 
            'stock_quantity', 'category_name', 'is_available'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para visualização de produto individual"""
    category = CategorySerializer(read_only=True)
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'author', 'isbn', 'description', 'price', 
            'stock_quantity', 'category', 'publication_date', 
            'is_active', 'is_available', 'created_at', 'updated_at'
        ]
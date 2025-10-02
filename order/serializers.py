from rest_framework import serializers
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Order, OrderItem
from product.models import Product
from product.serializers import ProductListSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializer básico para User"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer para OrderItem"""
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_author = serializers.CharField(source='product.author', read_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_title', 'product_author', 
            'quantity', 'unit_price', 'subtotal', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate_quantity(self, value):
        """Valida a quantidade do item"""
        if value <= 0:
            raise serializers.ValidationError("A quantidade deve ser maior que zero.")
        
        if value > 100:
            raise serializers.ValidationError("Quantidade máxima é 100 unidades por item.")
        
        return value
    
    def validate_unit_price(self, value):
        """Valida o preço unitário"""
        if value <= Decimal('0'):
            raise serializers.ValidationError("O preço unitário deve ser maior que zero.")
        
        return value
    
    def validate(self, data):
        """Validação do item como um todo"""
        product = data.get('product')
        quantity = data.get('quantity')
        
        if product and quantity:
            # Verifica se o produto está ativo
            if not product.is_active:
                raise serializers.ValidationError("Produto não está disponível.")
            
            # Verifica se há estoque suficiente
            if product.stock_quantity < quantity:
                raise serializers.ValidationError(
                    f"Estoque insuficiente. Disponível: {product.stock_quantity}"
                )
        
        return data


class OrderItemDetailSerializer(OrderItemSerializer):
    """Serializer detalhado para OrderItem com informações do produto"""
    product = ProductListSerializer(read_only=True)
    
    class Meta(OrderItemSerializer.Meta):
        fields = [
            'id', 'product', 'quantity', 'unit_price', 
            'subtotal', 'created_at'
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer para Order"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_name', 'status', 'total_amount', 
            'shipping_address', 'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_amount']
    
    def get_items_count(self, obj):
        """Retorna o número de itens no pedido"""
        return obj.items.count()
    
    def validate_shipping_address(self, value):
        """Valida o endereço de entrega"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "O endereço de entrega deve ter pelo menos 10 caracteres."
            )
        
        return value.strip()
    
    def validate_status(self, value):
        """Valida mudanças de status"""
        if self.instance:
            current_status = self.instance.status
            
            # Regras de transição de status
            valid_transitions = {
                'pending': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['delivered'],
                'delivered': [],
                'cancelled': []
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Não é possível alterar status de '{current_status}' para '{value}'"
                )
        
        return value


class OrderDetailSerializer(OrderSerializer):
    """Serializer detalhado para Order com itens"""
    items = OrderItemDetailSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta(OrderSerializer.Meta):
        fields = [
            'id', 'user', 'status', 'total_amount', 'shipping_address',
            'items', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de pedidos"""
    items = OrderItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'items']
    
    def validate_items(self, value):
        """Valida os itens do pedido"""
        if not value:
            raise serializers.ValidationError("O pedido deve ter pelo menos um item.")
        
        if len(value) > 50:
            raise serializers.ValidationError("Máximo de 50 itens por pedido.")
        
        # Verifica produtos duplicados
        product_ids = [item['product'].id for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Produtos duplicados no pedido.")
        
        return value
    
    def create(self, validated_data):
        """Cria o pedido com seus itens"""
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        # Cria o pedido
        order = Order.objects.create(
            user=user,
            shipping_address=validated_data['shipping_address'],
            total_amount=Decimal('0.00')
        )
        
        # Cria os itens e calcula o total
        total = Decimal('0.00')
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            # Usa o preço atual do produto
            unit_price = product.price
            
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=unit_price
            )
            
            total += order_item.subtotal
            
            # Reduz o estoque
            product.stock_quantity -= quantity
            product.save()
        
        # Atualiza o total do pedido
        order.total_amount = total
        order.save()
        
        return order
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date
from unittest.mock import Mock
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer, OrderDetailSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderItemDetailSerializer, UserSerializer
)
from product.models import Category, Product


class OrderModelTest(TestCase):
    """Testes para o modelo Order"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.order_data = {
            'user': self.user,
            'status': 'pending',
            'total_amount': Decimal('99.99'),
            'shipping_address': '123 Main St, City, State 12345'
        }
    
    def test_create_order(self):
        """Teste de criação de pedido"""
        order = Order.objects.create(**self.order_data)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_amount, Decimal('99.99'))
        self.assertIsNotNone(order.created_at)
    
    def test_order_str_method(self):
        """Teste do método __str__ do pedido"""
        order = Order.objects.create(**self.order_data)
        expected_str = f"Order #{order.id} - {self.user.username}"
        self.assertEqual(str(order), expected_str)


class OrderItemModelTest(TestCase):
    """Testes para o modelo OrderItem"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.product = Product.objects.create(
            title='Clean Code',
            author='Robert C. Martin',
            isbn='9780132350884',
            description='Test description',
            price=Decimal('45.99'),
            stock_quantity=10,
            category=self.category,
            publication_date=date.today()
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('91.98'),
            shipping_address='123 Main St'
        )
    
    def test_create_order_item(self):
        """Teste de criação de item do pedido"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('45.99')
        )
        self.assertEqual(item.order, self.order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal('45.99'))
    
    def test_subtotal_property(self):
        """Teste da propriedade subtotal"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('45.99')
        )
        expected_subtotal = Decimal('91.98')
        self.assertEqual(item.subtotal, expected_subtotal)
    
    def test_order_item_str_method(self):
        """Teste do método __str__ do item do pedido"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('45.99')
        )
        expected_str = f"{self.product.title} x 2"
        self.assertEqual(str(item), expected_str)


class UserSerializerTest(TestCase):
    """Testes para UserSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_user_serializer_fields(self):
        """Teste dos campos do UserSerializer"""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        expected_fields = ['id', 'username', 'email', 'first_name', 'last_name']
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')


class OrderItemSerializerTest(TestCase):
    """Testes para OrderItemSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.product = Product.objects.create(
            title='Clean Code',
            author='Robert C. Martin',
            isbn='9780132350884',
            description='Test description',
            price=Decimal('45.99'),
            stock_quantity=10,
            category=self.category,
            publication_date=date.today(),
            is_active=True
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('91.98'),
            shipping_address='123 Main St'
        )
        self.valid_data = {
            'product': self.product.id,
            'quantity': 2,
            'unit_price': '45.99'
        }
    
    def test_valid_serializer(self):
        """Teste de serializer válido"""
        serializer = OrderItemSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_quantity_validation(self):
        """Teste de validação da quantidade"""
        # Quantidade zero
        invalid_data = self.valid_data.copy()
        invalid_data['quantity'] = 0
        serializer = OrderItemSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)
        
        # Quantidade muito alta
        invalid_data['quantity'] = 101
        serializer = OrderItemSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)
    
    def test_unit_price_validation(self):
        """Teste de validação do preço unitário"""
        # Preço negativo
        invalid_data = self.valid_data.copy()
        invalid_data['unit_price'] = '-10.00'
        serializer = OrderItemSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('unit_price', serializer.errors)
    
    def test_product_stock_validation(self):
        """Teste de validação do estoque do produto"""
        # Produto sem estoque suficiente
        self.product.stock_quantity = 1
        self.product.save()
        
        invalid_data = self.valid_data.copy()
        invalid_data['quantity'] = 5
        serializer = OrderItemSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_inactive_product_validation(self):
        """Teste de validação de produto inativo"""
        self.product.is_active = False
        self.product.save()
        
        serializer = OrderItemSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class OrderSerializerTest(TestCase):
    """Testes para OrderSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('99.99'),
            shipping_address='123 Main St, City, State 12345',
            status='pending'
        )
        self.valid_data = {
            'user': self.user.id,
            'shipping_address': '456 Oak Ave, Town, State 67890',
            'status': 'pending'
        }
    
    def test_valid_serializer(self):
        """Teste de serializer válido"""
        serializer = OrderSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_shipping_address_validation(self):
        """Teste de validação do endereço de entrega"""
        # Endereço muito curto
        invalid_data = self.valid_data.copy()
        invalid_data['shipping_address'] = 'Short'
        serializer = OrderSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('shipping_address', serializer.errors)
    
    def test_status_transition_validation(self):
        """Teste de validação de transição de status"""
        # Transição válida: pending -> processing
        self.order.status = 'pending'
        self.order.save()
        
        valid_data = {'status': 'processing'}
        serializer = OrderSerializer(self.order, data=valid_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        # Transição inválida: delivered -> pending
        self.order.status = 'delivered'
        self.order.save()
        
        invalid_data = {'status': 'pending'}
        serializer = OrderSerializer(self.order, data=invalid_data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
    
    def test_items_count_field(self):
        """Teste do campo items_count"""
        # Cria alguns itens para o pedido
        category = Category.objects.create(name='Test', description='Test')
        product = Product.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            description='Test',
            price=Decimal('10.00'),
            stock_quantity=10,
            category=category,
            publication_date=date.today()
        )
        
        OrderItem.objects.create(
            order=self.order,
            product=product,
            quantity=2,
            unit_price=Decimal('10.00')
        )
        
        serializer = OrderSerializer(self.order)
        self.assertEqual(serializer.data['items_count'], 1)


class OrderCreateSerializerTest(TestCase):
    """Testes para OrderCreateSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.product1 = Product.objects.create(
            title='Clean Code',
            author='Robert C. Martin',
            isbn='9780132350884',
            description='Test description',
            price=Decimal('45.99'),
            stock_quantity=10,
            category=self.category,
            publication_date=date.today(),
            is_active=True
        )
        self.product2 = Product.objects.create(
            title='The Pragmatic Programmer',
            author='Andrew Hunt',
            isbn='9780201616224',
            description='Test description',
            price=Decimal('39.99'),
            stock_quantity=5,
            category=self.category,
            publication_date=date.today(),
            is_active=True
        )
        
        # Mock request object
        self.mock_request = Mock()
        self.mock_request.user = self.user
        
        self.valid_data = {
            'shipping_address': '123 Main St, City, State 12345',
            'items': [
                {
                    'product': self.product1.id,
                    'quantity': 2,
                    'unit_price': '45.99'
                },
                {
                    'product': self.product2.id,
                    'quantity': 1,
                    'unit_price': '39.99'
                }
            ]
        }
    
    def test_valid_order_creation(self):
        """Teste de criação válida de pedido"""
        serializer = OrderCreateSerializer(
            data=self.valid_data,
            context={'request': self.mock_request}
        )
        self.assertTrue(serializer.is_valid())
        
        order = serializer.save()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 2)
        expected_total = Decimal('131.97')  # (45.99 * 2) + (39.99 * 1)
        self.assertEqual(order.total_amount, expected_total)
    
    def test_empty_items_validation(self):
        """Teste de validação para itens vazios"""
        invalid_data = self.valid_data.copy()
        invalid_data['items'] = []
        
        serializer = OrderCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)
    
    def test_too_many_items_validation(self):
        """Teste de validação para muitos itens"""
        invalid_data = self.valid_data.copy()
        invalid_data['items'] = [
            {
                'product': self.product1.id,
                'quantity': 1,
                'unit_price': '10.00'
            }
        ] * 51  # Mais de 50 itens
        
        serializer = OrderCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)
    
    def test_duplicate_products_validation(self):
        """Teste de validação para produtos duplicados"""
        invalid_data = self.valid_data.copy()
        invalid_data['items'] = [
            {
                'product': self.product1.id,
                'quantity': 1,
                'unit_price': '45.99'
            },
            {
                'product': self.product1.id,  # Produto duplicado
                'quantity': 2,
                'unit_price': '45.99'
            }
        ]
        
        serializer = OrderCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)
    
    def test_stock_reduction_on_order_creation(self):
        """Teste de redução de estoque na criação do pedido"""
        initial_stock1 = self.product1.stock_quantity
        initial_stock2 = self.product2.stock_quantity
        
        serializer = OrderCreateSerializer(
            data=self.valid_data,
            context={'request': self.mock_request}
        )
        self.assertTrue(serializer.is_valid())
        order = serializer.save()
        
        # Recarrega os produtos do banco
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        
        # Verifica se o estoque foi reduzido corretamente
        self.assertEqual(self.product1.stock_quantity, initial_stock1 - 2)
        self.assertEqual(self.product2.stock_quantity, initial_stock2 - 1)

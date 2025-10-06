from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date
from order.models import Order, OrderItem
from order.serializers import OrderSerializer, OrderDetailSerializer, OrderCreateSerializer
from product.models import Category, Product


class OrderViewSetTest(APITestCase):
    """Testes para OrderViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        
        # Criar categoria e produto para os testes
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
        
        # Criar um pedido existente
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('45.99'),
            shipping_address='123 Main St, City, State 12345'
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=1,
            unit_price=Decimal('45.99')
        )
    
    def test_list_orders_authenticated(self):
        """Teste de listagem de pedidos com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = '/api/orders/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_orders_unauthenticated(self):
        """Teste de listagem de pedidos sem autenticação (deve falhar)"""
        url = '/api/orders/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_list_orders_filters_by_user(self):
        """Teste se listagem filtra apenas pedidos do usuário autenticado"""
        # Criar pedido para outro usuário
        Order.objects.create(
            user=self.other_user,
            total_amount=Decimal('25.99'),
            shipping_address='456 Oak Ave'
        )
        
        self.client.force_authenticate(user=self.user)
        url = '/api/orders/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Apenas pedido do usuário autenticado
    
    def test_create_order_authenticated(self):
        """Teste de criação de pedido com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = '/api/orders/'
        order_data = {
            'shipping_address': '789 Pine St, Town, State 67890',
            'items': [
                {
                    'product': self.product1.id,
                    'quantity': 2,
                    'unit_price': str(self.product1.price)
                },
                {
                    'product': self.product2.id,
                    'quantity': 1,
                    'unit_price': str(self.product2.price)
                }
            ]
        }
        response = self.client.post(url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        
        # Verificar se o total foi calculado corretamente
        new_order = Order.objects.latest('created_at')
        expected_total = (self.product1.price * 2) + (self.product2.price * 1)
        self.assertEqual(new_order.total_amount, expected_total)
    
    def test_create_order_unauthenticated(self):
        """Teste de criação de pedido sem autenticação (deve falhar)"""
        url = '/api/orders/'
        order_data = {
            'shipping_address': '789 Pine St, Town, State 67890',
            'items': []
        }
        response = self.client.post(url, order_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_retrieve_order_authenticated(self):
        """Teste de recuperação de pedido específico"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/orders/{self.order.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order.id)
        self.assertIn('items', response.data)  # OrderDetailSerializer
    
    def test_retrieve_other_user_order_denied(self):
        """Teste de recuperação de pedido de outro usuário (deve falhar)"""
        self.client.force_authenticate(user=self.other_user)
        url = f'/api/orders/{self.order.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_order_status(self):
        """Teste de atualização de status do pedido"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/orders/{self.order.id}/'
        update_data = {'status': 'processing'}
        response = self.client.patch(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')
    
    def test_delete_order_pending_status(self):
        """Teste de cancelamento de pedido com status pending"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/orders/{self.order.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
    
    def test_delete_order_non_pending_status(self):
        """Teste de cancelamento de pedido com status não pending (deve falhar)"""
        self.order.status = 'delivered'
        self.order.save()
        
        self.client.force_authenticate(user=self.user)
        url = f'/api/orders/{self.order.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_status_action(self):
        """Teste do endpoint update_status"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/orders/{self.order.id}/update_status/'
        data = {'status': 'processing'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')
    
    def test_update_status_invalid_transition(self):
        """Teste de transição de status inválida"""
        self.order.status = 'delivered'
        self.order.save()
        
        self.client.force_authenticate(user=self.user)
        url = f'/api/orders/{self.order.id}/update_status/'
        data = {'status': 'pending'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_my_orders_action(self):
        """Teste do endpoint my_orders"""
        self.client.force_authenticate(user=self.user)
        url = '/api/orders/my_orders/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_statistics_action(self):
        """Teste do endpoint statistics"""
        self.client.force_authenticate(user=self.user)
        url = '/api/orders/statistics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_fields = ['total_orders', 'total_spent', 'orders_by_status', 'average_order_value']
        for field in expected_fields:
            self.assertIn(field, response.data)
    
    def test_items_action(self):
        """Teste do endpoint items"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/orders/{self.order.id}/items/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_search_orders(self):
        """Teste de busca por pedidos"""
        self.client.force_authenticate(user=self.user)
        url = '/api/orders/?search=Main'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_orders_by_status(self):
        """Teste de filtro por status"""
        self.client.force_authenticate(user=self.user)
        url = '/api/orders/?status=pending'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class OrderItemViewSetTest(APITestCase):
    """Testes para OrderItemViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.product = Product.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            description='Test description',
            price=Decimal('25.99'),
            stock_quantity=10,
            category=self.category,
            publication_date=date.today()
        )
        
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('25.99'),
            shipping_address='123 Main St'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('25.99')
        )
    
    def test_list_order_items_authenticated(self):
        """Teste de listagem de itens com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = '/api/order-items/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_order_items_unauthenticated(self):
        """Teste de listagem de itens sem autenticação (deve falhar)"""
        url = '/api/order-items/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_list_order_items_filters_by_user(self):
        """Teste se listagem filtra apenas itens de pedidos do usuário"""
        # Criar pedido e item para outro usuário
        other_order = Order.objects.create(
            user=self.other_user,
            total_amount=Decimal('15.99'),
            shipping_address='456 Oak Ave'
        )
        OrderItem.objects.create(
            order=other_order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('15.99')
        )
        
        self.client.force_authenticate(user=self.user)
        url = '/api/order-items/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Apenas item do usuário autenticado
    
    def test_retrieve_order_item(self):
        """Teste de recuperação de item específico"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/order-items/{self.order_item.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order_item.id)
    
    def test_filter_order_items_by_order(self):
        """Teste de filtro por pedido"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/order-items/?order={self.order.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_order_items_by_product(self):
        """Teste de filtro por produto"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/order-items/?product={self.product.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
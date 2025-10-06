"""
Testes para a funcionalidade de paginação nos pedidos (orders)
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from order.models import Order, OrderItem
from product.models import Category, Product


class OrderPaginationTestCase(TestCase):
    """Casos de teste específicos para paginação de pedidos"""
    
    def setUp(self):
        """Configurar dados de teste para pedidos"""
        self.client = APIClient()
        
        # Criar usuários de teste
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass123',
            email='test1@example.com'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            email='test2@example.com'
        )
        
        # Criar categoria e produto para os pedidos
        self.category = Category.objects.create(
            name='Test Category',
            description='Categoria de teste'
        )
        
        self.product = Product.objects.create(
            title='Test Product',
            author='Test Author',
            isbn='9780123456789',
            description='Produto de teste',
            price=Decimal('39.99'),
            stock_quantity=100,
            category=self.category,
            publication_date=date.today(),
            is_active=True
        )
        
        # Criar pedidos para user1 (para testar que só vê seus próprios pedidos)
        self.orders_user1 = []
        for i in range(12):
            order = Order.objects.create(
                user=self.user1,
                shipping_address=f'Endereço User1 {i+1}',
                status='pending',
                total_amount=Decimal(f'{100.00 + i*10}')
            )
            
            OrderItem.objects.create(
                order=order,
                product=self.product,
                quantity=i+1,
                unit_price=self.product.price
            )
            
            self.orders_user1.append(order)
        
        # Criar pedidos para user2
        self.orders_user2 = []
        for i in range(8):
            order = Order.objects.create(
                user=self.user2,
                shipping_address=f'Endereço User2 {i+1}',
                status='delivered',
                total_amount=Decimal(f'{50.00 + i*5}')
            )
            
            OrderItem.objects.create(
                order=order,
                product=self.product,
                quantity=1,
                unit_price=self.product.price
            )
            
            self.orders_user2.append(order)
    
    def test_orders_pagination_user_isolation(self):
        """Testar que cada usuário vê apenas seus próprios pedidos"""
        # Autenticar como user1
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User1 deve ver apenas seus 12 pedidos
        self.assertEqual(response.data['count'], 12)
        self.assertEqual(len(response.data['results']), 10)  # Primeira página com 10 itens
        self.assertIsNotNone(response.data['next'])  # Deve ter próxima página
        
        # Verificar que todos os pedidos pertencem ao user1
        for order in response.data['results']:
            order_obj = Order.objects.get(id=order['id'])
            self.assertEqual(order_obj.user, self.user1)
        
        # Autenticar como user2
        self.client.force_authenticate(user=self.user2)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User2 deve ver apenas seus 8 pedidos
        self.assertEqual(response.data['count'], 8)
        self.assertEqual(len(response.data['results']), 8)  # Todos os 8 pedidos na primeira página
        self.assertIsNone(response.data['next'])  # Não deve ter próxima página
        
        # Verificar que todos os pedidos pertencem ao user2
        for order in response.data['results']:
            order_obj = Order.objects.get(id=order['id'])
            self.assertEqual(order_obj.user, self.user2)
    
    def test_orders_pagination_second_page(self):
        """Testar segunda página de pedidos"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-list')
        response = self.client.get(url, {'page': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Restam 2 pedidos na segunda página
        self.assertIsNone(response.data['next'])  # Não deve ter próxima página
        self.assertIsNotNone(response.data['previous'])  # Deve ter página anterior
    
    def test_order_items_pagination(self):
        """Testar paginação de itens de pedido"""
        # Criar um pedido com muitos itens
        order_with_many_items = Order.objects.create(
            user=self.user1,
            shipping_address='Endereço com muitos itens',
            status='pending',
            total_amount=Decimal('500.00')
        )
        
        # Criar produtos adicionais
        products = []
        for i in range(8):
            product = Product.objects.create(
                title=f'Product for OrderItem {i+1}',
                author=f'Author {i+1}',
                isbn=f'978012345678{str(i).zfill(1)}',
                description=f'Product {i+1}',
                price=Decimal(f'{20.00 + i}'),
                stock_quantity=50,
                category=self.category,
                publication_date=date.today() - timedelta(days=i),
                is_active=True
            )
            products.append(product)
            
            # Adicionar item ao pedido
            OrderItem.objects.create(
                order=order_with_many_items,
                product=product,
                quantity=i+1,
                unit_price=product.price
            )
        
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('orderitem-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar paginação dos itens (5 por página)
        self.assertLessEqual(len(response.data['results']), 5)
        
        # Se há mais de 5 itens, deve ter próxima página
        total_items = OrderItem.objects.filter(order__user=self.user1).count()
        if total_items > 5:
            self.assertIsNotNone(response.data['next'])
    
    def test_orders_filtering_with_pagination(self):
        """Testar filtragem de pedidos combinada com paginação"""
        self.client.force_authenticate(user=self.user1)
        
        # Filtrar por status
        url = reverse('order-list')
        response = self.client.get(url, {'status': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todos os pedidos retornados têm status 'pending'
        for order in response.data['results']:
            self.assertEqual(order['status'], 'pending')
        
        # Verificar paginação funciona com filtro
        if response.data['count'] > 10:
            self.assertIsNotNone(response.data['next'])
    
    def test_orders_ordering_with_pagination(self):
        """Testar ordenação de pedidos combinada com paginação"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-list')
        
        # Ordenar por data de criação (mais recente primeiro)
        response = self.client.get(url, {'ordering': '-created_at'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar ordenação (assumindo que temos campo created_at ou similar)
        order_ids = [order['id'] for order in response.data['results']]
        
        # Os IDs devem estar em ordem decrescente se ordenados por criação mais recente
        self.assertEqual(order_ids, sorted(order_ids, reverse=True))
    
    def test_pagination_metadata_format(self):
        """Testar formato dos metadados de paginação"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estrutura da resposta de paginação
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        
        # Verificar tipos corretos
        self.assertIsInstance(response.data['count'], int)
        self.assertIsInstance(response.data['results'], list)
        
        # Se há próxima página, deve ser uma URL válida
        if response.data['next']:
            self.assertTrue(response.data['next'].startswith('http'))
            self.assertIn('page=', response.data['next'])
    
    def test_empty_page_handling(self):
        """Testar tratamento de páginas vazias"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-list')
        
        # Tentar acessar uma página muito alta
        response = self.client.get(url, {'page': 999})
        
        # Deve retornar 404 para página inexistente
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
"""
Testes para a funcionalidade de paginação do Django REST Framework
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from product.models import Category, Product
from order.models import Order, OrderItem


class PaginationTestCase(TestCase):
    """Casos de teste para paginação dos endpoints da API"""
    
    def setUp(self):
        """Configurar dados de teste"""
        self.client = APIClient()
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Criar categorias para testar paginação de categorias (5 por página)
        self.categories = []
        for i in range(12):  # Criar 12 categorias para testar múltiplas páginas
            category = Category.objects.create(
                name=f'Categoria {i+1}',
                description=f'Descrição da categoria {i+1}'
            )
            self.categories.append(category)
        
        # Criar produtos para testar paginação de produtos (10 por página)
        self.products = []
        for i in range(25):  # Criar 25 produtos para testar múltiplas páginas
            product = Product.objects.create(
                title=f'Produto {i+1}',
                author=f'Autor {i+1}',
                isbn=f'978012345678{str(i).zfill(1)}',
                description=f'Descrição do produto {i+1}',
                price=Decimal(f'{19.99 + i}'),
                stock_quantity=10,
                category=self.categories[i % len(self.categories)],
                publication_date=date.today() - timedelta(days=i*30),
                is_active=True
            )
            self.products.append(product)
        
        # Criar pedidos para testar paginação de pedidos (10 por página)
        self.orders = []
        for i in range(22):  # Criar 22 pedidos para testar múltiplas páginas
            order = Order.objects.create(
                user=self.user,
                shipping_address=f'Endereço {i+1}',
                status='pending',
                total_amount=Decimal(f'{50.00 + i*5}')
            )
            
            # Adicionar item ao pedido
            OrderItem.objects.create(
                order=order,
                product=self.products[i % len(self.products)],
                quantity=1,
                unit_price=self.products[i % len(self.products)].price
            )
            
            self.orders.append(order)
    
    def test_categories_pagination_first_page(self):
        """Testar primeira página de categorias (5 itens)"""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
        # Deve retornar 5 categorias na primeira página
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 12)  # Total de categorias
        self.assertIsNotNone(response.data['next'])  # Deve ter próxima página
        self.assertIsNone(response.data['previous'])  # Não deve ter página anterior
    
    def test_categories_pagination_second_page(self):
        """Testar segunda página de categorias"""
        url = reverse('category-list')
        response = self.client.get(url, {'page': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])  # Deve ter próxima página
        self.assertIsNotNone(response.data['previous'])  # Deve ter página anterior
    
    def test_categories_pagination_last_page(self):
        """Testar última página de categorias"""
        url = reverse('category-list')
        response = self.client.get(url, {'page': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Restam 2 categorias
        self.assertIsNone(response.data['next'])  # Não deve ter próxima página
        self.assertIsNotNone(response.data['previous'])  # Deve ter página anterior
    
    def test_products_pagination_first_page(self):
        """Testar primeira página de produtos (10 itens)"""
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Deve retornar 10 produtos na primeira página
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 25)  # Total de produtos
        self.assertIsNotNone(response.data['next'])  # Deve ter próxima página
        self.assertIsNone(response.data['previous'])  # Não deve ter página anterior
    
    def test_products_pagination_third_page(self):
        """Testar terceira página de produtos"""
        url = reverse('product-list')
        response = self.client.get(url, {'page': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)  # Restam 5 produtos
        self.assertIsNone(response.data['next'])  # Não deve ter próxima página
        self.assertIsNotNone(response.data['previous'])  # Deve ter página anterior
    
    def test_orders_pagination_requires_authentication(self):
        """Testar que paginação de pedidos requer autenticação"""
        url = reverse('order-list')
        response = self.client.get(url)
        
        # Deve retornar 401 Unauthorized sem autenticação
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_orders_pagination_with_authentication(self):
        """Testar paginação de pedidos com autenticação"""
        # Autenticar usuário
        self.client.force_authenticate(user=self.user)
        
        url = reverse('order-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Deve retornar 10 pedidos na primeira página
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 22)  # Total de pedidos
        self.assertIsNotNone(response.data['next'])  # Deve ter próxima página
        self.assertIsNone(response.data['previous'])  # Não deve ter página anterior
    
    def test_orders_pagination_third_page_with_authentication(self):
        """Testar terceira página de pedidos com autenticação"""
        # Autenticar usuário
        self.client.force_authenticate(user=self.user)
        
        url = reverse('order-list')
        response = self.client.get(url, {'page': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Restam 2 pedidos
        self.assertIsNone(response.data['next'])  # Não deve ter próxima página
        self.assertIsNotNone(response.data['previous'])  # Deve ter página anterior
    
    def test_invalid_page_number(self):
        """Testar número de página inválido"""
        url = reverse('category-list')
        response = self.client.get(url, {'page': 999})
        
        # Deve retornar 404 Not Found para página inexistente
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_pagination_page_size_info(self):
        """Testar informações de tamanho da página na resposta"""
        # Testar categorias (página pequena - 5 itens)
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        
        # Testar produtos (página média - 10 itens)
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
    
    def test_pagination_urls_format(self):
        """Testar formato das URLs de paginação"""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar se as URLs de paginação estão no formato correto
        if response.data['next']:
            self.assertIn('page=2', response.data['next'])
        
        # Testar segunda página
        response = self.client.get(url, {'page': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data['previous']:
            self.assertIn('page=1', response.data['previous'])
    
    def test_ordering_with_pagination(self):
        """Testar ordenação combinada com paginação"""
        url = reverse('product-list')
        
        # Testar ordenação por preço
        response = self.client.get(url, {'ordering': 'price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar se os resultados estão ordenados
        prices = [Decimal(str(product['price'])) for product in response.data['results']]
        self.assertEqual(prices, sorted(prices))
        
        # Testar ordenação decrescente por preço
        response = self.client.get(url, {'ordering': '-price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prices = [Decimal(str(product['price'])) for product in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))
    
    def test_filtering_with_pagination(self):
        """Testar filtragem combinada com paginação"""
        # Criar categoria específica para teste
        test_category = Category.objects.create(
            name='Test Category',
            description='Categoria para teste de filtragem'
        )
        
        # Criar produtos na categoria de teste
        for i in range(15):
            Product.objects.create(
                title=f'Test Product {i+1}',
                author=f'Test Author {i+1}',
                isbn=f'978987654321{str(i).zfill(1)}',
                description=f'Test product {i+1}',
                price=Decimal('29.99'),
                stock_quantity=5,
                category=test_category,
                is_active=True
            )
        
        url = reverse('product-list')
        response = self.client.get(url, {'category': test_category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)  # Total de produtos filtrados
        self.assertEqual(len(response.data['results']), 10)  # Primeira página com 10 itens
        self.assertIsNotNone(response.data['next'])  # Deve ter próxima página
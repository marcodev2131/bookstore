from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date
from product.models import Category, Product
from product.serializers import CategorySerializer, ProductSerializer


class CategoryViewSetTest(APITestCase):
    """Testes para CategoryViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category_data = {
            'name': 'Fiction',
            'description': 'Fictional books and novels'
        }
        self.category = Category.objects.create(**self.category_data)
        
    def test_list_categories_unauthenticated(self):
        """Teste de listagem de categorias sem autenticação"""
        url = '/api/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_category_authenticated(self):
        """Teste de criação de categoria com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = '/api/categories/'
        new_category = {
            'name': 'Science Fiction',
            'description': 'Sci-fi books and stories'
        }
        response = self.client.post(url, new_category)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)
    
    def test_create_category_unauthenticated(self):
        """Teste de criação de categoria sem autenticação (deve falhar)"""
        url = '/api/categories/'
        new_category = {
            'name': 'Science Fiction',
            'description': 'Sci-fi books and stories'
        }
        response = self.client.post(url, new_category)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_retrieve_category(self):
        """Teste de recuperação de categoria específica"""
        url = f'/api/categories/{self.category.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.category.name)
    
    def test_update_category_authenticated(self):
        """Teste de atualização de categoria com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/categories/{self.category.id}/'
        updated_data = {
            'name': 'Updated Fiction',
            'description': 'Updated description'
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Fiction')
    
    def test_delete_category_authenticated(self):
        """Teste de exclusão de categoria com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/categories/{self.category.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)
    
    def test_search_categories(self):
        """Teste de busca por categorias"""
        Category.objects.create(name='Mystery', description='Mystery books')
        url = '/api/categories/?search=fiction'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_categories_by_name(self):
        """Teste de filtro por nome"""
        url = f'/api/categories/?name={self.category.name}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_categories_with_products_action(self):
        """Teste do endpoint customizado with_products"""
        # Categoria sem produtos
        empty_category = Category.objects.create(name='Empty', description='No products')
        
        # Categoria com produto
        Product.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            description='Test',
            price=Decimal('10.00'),
            stock_quantity=5,
            category=self.category,
            publication_date=date.today()
        )
        
        url = '/api/categories/with_products/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Apenas categoria com produtos


class ProductViewSetTest(APITestCase):
    """Testes para ProductViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.product_data = {
            'title': 'Clean Code',
            'author': 'Robert C. Martin',
            'isbn': '9780132350884',
            'description': 'A handbook of agile software craftsmanship',
            'price': '45.99',
            'stock_quantity': 10,
            'category': self.category.id,
            'publication_date': '2008-08-01',
            'is_active': True
        }
        self.product = Product.objects.create(
            title='Existing Book',
            author='Existing Author',
            isbn='1234567890123',
            description='Existing description',
            price=Decimal('25.99'),
            stock_quantity=5,
            category=self.category,
            publication_date=date(2020, 1, 1)
        )
    
    def test_list_products_unauthenticated(self):
        """Teste de listagem de produtos sem autenticação"""
        url = '/api/products/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_product_authenticated(self):
        """Teste de criação de produto com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = '/api/products/'
        response = self.client.post(url, self.product_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
    
    def test_create_product_unauthenticated(self):
        """Teste de criação de produto sem autenticação (deve falhar)"""
        url = '/api/products/'
        response = self.client.post(url, self.product_data)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_retrieve_product(self):
        """Teste de recuperação de produto específico"""
        url = f'/api/products/{self.product.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.product.title)
    
    def test_update_product_authenticated(self):
        """Teste de atualização de produto"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/products/{self.product.id}/'
        updated_data = {
            'title': 'Updated Book',
            'author': 'Updated Author',
            'isbn': '9876543210987',
            'description': 'Updated description',
            'price': '30.99',
            'stock_quantity': 8,
            'category': self.category.id,
            'publication_date': '2021-01-01',
            'is_active': True
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, 'Updated Book')
    
    def test_delete_product_authenticated(self):
        """Teste de exclusão de produto"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/products/{self.product.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)
    
    def test_search_products(self):
        """Teste de busca por produtos"""
        url = '/api/products/?search=existing'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_products_by_category(self):
        """Teste de filtro por categoria"""
        url = f'/api/products/?category={self.category.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_products_by_price_range(self):
        """Teste de filtro por faixa de preço"""
        url = '/api/products/?min_price=20&max_price=30'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_available_products(self):
        """Teste de filtro por produtos disponíveis"""
        # Criar produto sem estoque
        Product.objects.create(
            title='Out of Stock',
            author='Author',
            isbn='1111111111111',
            description='No stock',
            price=Decimal('10.00'),
            stock_quantity=0,
            category=self.category,
            publication_date=date.today()
        )
        
        url = '/api/products/?available=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Apenas com estoque
    
    def test_available_products_action(self):
        """Teste do endpoint customizado available"""
        url = '/api/products/available/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_bestsellers_action(self):
        """Teste do endpoint customizado bestsellers"""
        url = '/api/products/bestsellers/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_update_stock_action_authenticated(self):
        """Teste do endpoint update_stock com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/products/{self.product.id}/update_stock/'
        data = {'quantity': 15}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 15)
    
    def test_update_stock_action_invalid_quantity(self):
        """Teste do endpoint update_stock com quantidade inválida"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/products/{self.product.id}/update_stock/'
        data = {'quantity': -5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_search_advanced_action(self):
        """Teste do endpoint search_advanced"""
        url = '/api/products/search_advanced/?q=existing&min_price=20'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_product_serializer_selection(self):
        """Teste se o serializer correto é usado em cada ação"""
        # List usa ProductListSerializer
        url = '/api/products/'
        response = self.client.get(url)
        self.assertNotIn('description', response.data['results'][0])
        
        # Retrieve usa ProductDetailSerializer
        url = f'/api/products/{self.product.id}/'
        response = self.client.get(url)
        self.assertIn('description', response.data)
        self.assertIn('category', response.data)
        self.assertIsInstance(response.data['category'], dict)
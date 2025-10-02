from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import Category, Product
from .serializers import (
    CategorySerializer, ProductSerializer, 
    ProductListSerializer, ProductDetailSerializer
)


class CategoryModelTest(TestCase):
    """Testes para o modelo Category"""
    
    def setUp(self):
        self.category_data = {
            'name': 'Fiction',
            'description': 'Fictional books and novels'
        }
    
    def test_create_category(self):
        """Teste de criação de categoria"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(category.name, 'Fiction')
        self.assertEqual(category.description, 'Fictional books and novels')
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)
    
    def test_category_str_method(self):
        """Teste do método __str__ da categoria"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(str(category), 'Fiction')
    
    def test_unique_category_name(self):
        """Teste de nome único para categoria"""
        Category.objects.create(**self.category_data)
        with self.assertRaises(Exception):
            Category.objects.create(**self.category_data)


class ProductModelTest(TestCase):
    """Testes para o modelo Product"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.product_data = {
            'title': 'Clean Code',
            'author': 'Robert C. Martin',
            'isbn': '9780132350884',
            'description': 'A handbook of agile software craftsmanship',
            'price': Decimal('45.99'),
            'stock_quantity': 10,
            'category': self.category,
            'publication_date': date(2008, 8, 1),
            'is_active': True
        }
    
    def test_create_product(self):
        """Teste de criação de produto"""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(product.title, 'Clean Code')
        self.assertEqual(product.author, 'Robert C. Martin')
        self.assertEqual(product.isbn, '9780132350884')
        self.assertEqual(product.price, Decimal('45.99'))
        self.assertEqual(product.stock_quantity, 10)
        self.assertTrue(product.is_active)
    
    def test_product_str_method(self):
        """Teste do método __str__ do produto"""
        product = Product.objects.create(**self.product_data)
        expected_str = f"{self.product_data['title']} - {self.product_data['author']}"
        self.assertEqual(str(product), expected_str)
    
    def test_is_available_property(self):
        """Teste da propriedade is_available"""
        # Produto ativo com estoque
        product = Product.objects.create(**self.product_data)
        self.assertTrue(product.is_available)
        
        # Produto ativo sem estoque
        product.stock_quantity = 0
        product.save()
        self.assertFalse(product.is_available)
        
        # Produto inativo com estoque
        product.stock_quantity = 10
        product.is_active = False
        product.save()
        self.assertFalse(product.is_available)
    
    def test_unique_isbn(self):
        """Teste de ISBN único"""
        Product.objects.create(**self.product_data)
        with self.assertRaises(Exception):
            Product.objects.create(**self.product_data)


class CategorySerializerTest(TestCase):
    """Testes para CategorySerializer"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Science Fiction',
            description='Sci-fi books'
        )
        self.valid_data = {
            'name': 'Fantasy',
            'description': 'Fantasy novels and books'
        }
    
    def test_valid_serializer(self):
        """Teste de serializer válido"""
        serializer = CategorySerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_serializer_save(self):
        """Teste de salvamento via serializer"""
        serializer = CategorySerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.name, 'Fantasy')
        self.assertEqual(category.description, 'Fantasy novels and books')
    
    def test_name_validation(self):
        """Teste de validação do nome"""
        # Nome muito curto
        invalid_data = self.valid_data.copy()
        invalid_data['name'] = 'A'
        serializer = CategorySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_name_title_case(self):
        """Teste de formatação do nome em title case"""
        data = self.valid_data.copy()
        data['name'] = 'mystery books'  # Nome diferente para evitar conflito
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.name, 'Mystery Books')
    
    def test_products_count_field(self):
        """Teste do campo products_count"""
        # Adiciona produtos à categoria
        Product.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            description='Test description',
            price=Decimal('10.00'),
            stock_quantity=5,
            category=self.category,
            publication_date=date.today()
        )
        
        serializer = CategorySerializer(self.category)
        self.assertEqual(serializer.data['products_count'], 1)


class ProductSerializerTest(TestCase):
    """Testes para ProductSerializer"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.valid_data = {
            'title': 'Django for Beginners',
            'author': 'William S. Vincent',
            'isbn': '9781735467207',
            'description': 'Learn Django web development',
            'price': '39.99',
            'stock_quantity': 15,
            'category': self.category.id,
            'publication_date': '2022-01-01',
            'is_active': True
        }
    
    def test_valid_serializer(self):
        """Teste de serializer válido"""
        serializer = ProductSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_isbn_validation(self):
        """Teste de validação do ISBN"""
        # ISBN com formato correto
        serializer = ProductSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        # ISBN muito curto
        invalid_data = self.valid_data.copy()
        invalid_data['isbn'] = '123456789'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('isbn', serializer.errors)
        
        # ISBN com letras
        invalid_data['isbn'] = '123456789012A'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('isbn', serializer.errors)
    
    def test_price_validation(self):
        """Teste de validação do preço"""
        # Preço negativo
        invalid_data = self.valid_data.copy()
        invalid_data['price'] = '-10.00'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
        
        # Preço zero
        invalid_data['price'] = '0.00'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
        
        # Preço muito alto
        invalid_data['price'] = '10000.00'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
    
    def test_stock_validation(self):
        """Teste de validação do estoque"""
        # Estoque negativo
        invalid_data = self.valid_data.copy()
        invalid_data['stock_quantity'] = -1
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('stock_quantity', serializer.errors)
    
    def test_title_validation(self):
        """Teste de validação do título"""
        # Título muito curto
        invalid_data = self.valid_data.copy()
        invalid_data['title'] = 'AB'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
    
    def test_author_validation(self):
        """Teste de validação do autor"""
        # Nome do autor muito curto
        invalid_data = self.valid_data.copy()
        invalid_data['author'] = 'A'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('author', serializer.errors)


class ProductListSerializerTest(TestCase):
    """Testes para ProductListSerializer"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.product = Product.objects.create(
            title='Clean Code',
            author='Robert C. Martin',
            isbn='9780132350884',
            description='A handbook of agile software craftsmanship',
            price=Decimal('45.99'),
            stock_quantity=10,
            category=self.category,
            publication_date=date(2008, 8, 1),
            is_active=True
        )
    
    def test_serializer_fields(self):
        """Teste dos campos do serializer"""
        serializer = ProductListSerializer(self.product)
        data = serializer.data
        
        expected_fields = [
            'id', 'title', 'author', 'isbn', 'price', 
            'stock_quantity', 'category_name', 'is_available'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['category_name'], self.category.name)


class ProductDetailSerializerTest(TestCase):
    """Testes para ProductDetailSerializer"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Programming',
            description='Programming books'
        )
        self.product = Product.objects.create(
            title='Clean Code',
            author='Robert C. Martin',
            isbn='9780132350884',
            description='A handbook of agile software craftsmanship',
            price=Decimal('45.99'),
            stock_quantity=10,
            category=self.category,
            publication_date=date(2008, 8, 1),
            is_active=True
        )
    
    def test_nested_category_serializer(self):
        """Teste do serializer aninhado da categoria"""
        serializer = ProductDetailSerializer(self.product)
        data = serializer.data
        
        self.assertIn('category', data)
        category_data = data['category']
        self.assertEqual(category_data['name'], self.category.name)
        self.assertEqual(category_data['description'], self.category.description)

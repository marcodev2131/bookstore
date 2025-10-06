"""
Comando de gerenciamento Django para criar dados de teste para paginação
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from product.models import Category, Product
from order.models import Order, OrderItem
import random


class Command(BaseCommand):
    help = 'Cria dados de teste para demonstrar a paginação'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            type=int,
            default=8,
            help='Número de categorias a criar (padrão: 8)'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=25,
            help='Número de produtos a criar (padrão: 25)'
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=15,
            help='Número de pedidos a criar (padrão: 15)'
        )

    def handle(self, *args, **options):
        self.stdout.write('Criando dados de teste para paginação...')
        
        # Criar categorias
        categories_data = [
            ('Fiction', 'Livros de ficção em geral'),
            ('Science Fiction', 'Ficção científica e fantasia'),
            ('Mystery', 'Mistério e suspense'),
            ('Romance', 'Romances e histórias de amor'),
            ('Biography', 'Biografias e autobiografias'),
            ('Programming', 'Livros de programação'),
            ('Business', 'Negócios e empreendedorismo'),
            ('Self Help', 'Autoajuda e desenvolvimento pessoal'),
        ]
        
        categories = []
        for i, (name, description) in enumerate(categories_data[:options['categories']]):
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'  Categoria criada: {name}')
        
        # Dados para produtos
        products_data = [
            ('Clean Code', 'Robert C. Martin', 'Um manual de técnicas ágeis de desenvolvimento de software'),
            ('The Pragmatic Programmer', 'Andrew Hunt', 'Guia prático para programadores'),
            ('Design Patterns', 'Gang of Four', 'Padrões de projeto orientados a objetos'),
            ('Refactoring', 'Martin Fowler', 'Melhorando o design de código existente'),
            ('The Art of War', 'Sun Tzu', 'Estratégias militares clássicas'),
            ('1984', 'George Orwell', 'Distopia futurística sobre totalitarismo'),
            ('Pride and Prejudice', 'Jane Austen', 'Romance clássico inglês'),
            ('To Kill a Mockingbird', 'Harper Lee', 'Drama sobre racismo no sul dos EUA'),
            ('The Great Gatsby', 'F. Scott Fitzgerald', 'Crítica social dos anos 1920'),
            ('Dune', 'Frank Herbert', 'Épico de ficção científica'),
            ('Foundation', 'Isaac Asimov', 'Série de ficção científica'),
            ('The Hobbit', 'J.R.R. Tolkien', 'Aventura fantástica'),
            ('Sherlock Holmes', 'Arthur Conan Doyle', 'Coletânea de mistérios'),
            ('Agatha Christie Collection', 'Agatha Christie', 'Mistérios da rainha do crime'),
            ('Steve Jobs', 'Walter Isaacson', 'Biografia do fundador da Apple'),
            ('Thinking Fast and Slow', 'Daniel Kahneman', 'Psicologia comportamental'),
            ('The Lean Startup', 'Eric Ries', 'Metodologia para startups'),
            ('Good to Great', 'Jim Collins', 'Como empresas se tornam excelentes'),
            ('The 7 Habits', 'Stephen Covey', 'Hábitos de pessoas eficazes'),
            ('Atomic Habits', 'James Clear', 'Pequenas mudanças, grandes resultados'),
            ('Python Crash Course', 'Eric Matthes', 'Introdução prática ao Python'),
            ('JavaScript: The Good Parts', 'Douglas Crockford', 'As melhores práticas do JavaScript'),
            ('You Don\'t Know JS', 'Kyle Simpson', 'Série sobre JavaScript avançado'),
            ('Django for Beginners', 'William Vincent', 'Desenvolvimento web com Django'),
            ('React in Action', 'Mark Thomas', 'Construindo interfaces com React'),
        ]
        
        # Criar produtos
        products = []
        for i in range(min(options['products'], len(products_data))):
            title, author, description = products_data[i]
            category = random.choice(categories)
            
            product, created = Product.objects.get_or_create(
                title=title,
                author=author,
                defaults={
                    'isbn': f'97801{str(random.randint(10000000, 99999999))}',
                    'description': description,
                    'price': Decimal(str(random.uniform(19.99, 89.99))).quantize(Decimal('0.01')),
                    'stock_quantity': random.randint(0, 50),
                    'category': category,
                    'publication_date': date.today() - timedelta(days=random.randint(1, 3650)),
                    'is_active': random.choice([True, True, True, False])  # 75% ativos
                }
            )
            products.append(product)
            if created:
                self.stdout.write(f'  Produto criado: {title}')
        
        # Criar usuário de teste se não existir
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write('  Usuário de teste criado: testuser')
        
        # Criar pedidos
        active_products = [p for p in products if p.is_active and p.stock_quantity > 0]
        for i in range(options['orders']):
            order = Order.objects.create(
                user=user,
                shipping_address=f'Rua Teste {i+1}, {random.randint(1, 999)}, Cidade Teste, Estado',
                status=random.choice(['pending', 'processing', 'shipped', 'delivered']),
                total_amount=Decimal('0.00')
            )
            
            # Adicionar itens ao pedido
            num_items = random.randint(1, 5)
            selected_products = random.sample(active_products, min(num_items, len(active_products)))
            
            total = Decimal('0.00')
            for product in selected_products:
                quantity = random.randint(1, min(3, product.stock_quantity))
                if quantity > 0:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price
                    )
                    total += product.price * quantity
            
            order.total_amount = total
            order.save()
            
            if i < 5:  # Mostrar apenas os primeiros 5
                self.stdout.write(f'  Pedido criado: #{order.id} - R$ {total}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Dados de teste criados com sucesso!\n'
                f'- {len(categories)} categorias\n'
                f'- {len(products)} produtos\n'
                f'- {options["orders"]} pedidos\n'
                f'\nPara testar a paginação, visite:\n'
                f'- /api/categories/ (5 por página)\n'
                f'- /api/products/ (10 por página)\n'
                f'- /api/orders/ (10 por página - requer login)\n'
            )
        )
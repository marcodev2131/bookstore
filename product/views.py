from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from bookstore.pagination import SmallResultsSetPagination, MediumResultsSetPagination
from .models import Category, Product
from .serializers import (
    CategorySerializer, ProductSerializer, 
    ProductListSerializer, ProductDetailSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de categorias de produtos.
    
    Operações disponíveis:
    - GET /categories/ - Lista todas as categorias
    - POST /categories/ - Cria nova categoria
    - GET /categories/{id}/ - Detalhes de uma categoria
    - PUT /categories/{id}/ - Atualiza categoria completa
    - PATCH /categories/{id}/ - Atualização parcial
    - DELETE /categories/{id}/ - Remove categoria
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = SmallResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """
        Endpoint customizado para listar produtos de uma categoria específica.
        URL: GET /categories/{id}/products/
        """
        category = self.get_object()
        products = category.products.filter(is_active=True)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def with_products(self, request):
        """
        Endpoint customizado para listar apenas categorias que possuem produtos.
        URL: GET /categories/with_products/
        """
        categories = Category.objects.filter(products__isnull=False).distinct()
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de produtos.
    
    Operações disponíveis:
    - GET /products/ - Lista produtos com paginação
    - POST /products/ - Cria novo produto
    - GET /products/{id}/ - Detalhes de um produto
    - PUT /products/{id}/ - Atualiza produto completo
    - PATCH /products/{id}/ - Atualização parcial
    - DELETE /products/{id}/ - Remove produto
    """
    queryset = Product.objects.select_related('category').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = MediumResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'stock_quantity']
    search_fields = ['title', 'author', 'isbn', 'description']
    ordering_fields = ['title', 'author', 'price', 'publication_date', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    def get_queryset(self):
        """
        Filtra produtos baseado em parâmetros da query string.
        """
        queryset = super().get_queryset()
        
        # Filtro por preço mínimo
        min_price = self.request.query_params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        # Filtro por preço máximo
        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Filtro por disponibilidade
        available = self.request.query_params.get('available')
        if available and available.lower() in ['true', '1']:
            queryset = queryset.filter(is_active=True, stock_quantity__gt=0)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Endpoint para listar apenas produtos disponíveis.
        URL: GET /products/available/
        """
        products = self.get_queryset().filter(is_active=True, stock_quantity__gt=0)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        """
        Endpoint para produtos mais vendidos (simulado por data de criação recente).
        URL: GET /products/bestsellers/
        """
        products = self.get_queryset().filter(is_active=True).order_by('-created_at')[:10]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """
        Endpoint para atualizar estoque de um produto.
        URL: POST /products/{id}/update_stock/
        Body: {"quantity": number}
        """
        product = self.get_object()
        quantity = request.data.get('quantity')
        
        if quantity is None:
            return Response(
                {'error': 'Quantidade é obrigatória'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                return Response(
                    {'error': 'Quantidade não pode ser negativa'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            product.stock_quantity = quantity
            product.save()
            
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        
        except ValueError:
            return Response(
                {'error': 'Quantidade deve ser um número inteiro'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def search_advanced(self, request):
        """
        Busca avançada com múltiplos critérios.
        URL: GET /products/search_advanced/?q=termo&category=id&min_price=10&max_price=100
        """
        queryset = self.get_queryset()
        
        # Termo de busca geral
        q = request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(author__icontains=q) |
                Q(description__icontains=q) |
                Q(isbn__icontains=q)
            )
        
        # Aplicar filtros de preço e categoria via get_queryset
        queryset = self.filter_queryset(queryset)
        
        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data)

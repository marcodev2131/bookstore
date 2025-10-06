from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from decimal import Decimal
from bookstore.pagination import MediumResultsSetPagination, SmallResultsSetPagination
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer, OrderDetailSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderItemDetailSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de pedidos.
    
    Operações disponíveis:
    - GET /orders/ - Lista pedidos do usuário autenticado
    - POST /orders/ - Cria novo pedido
    - GET /orders/{id}/ - Detalhes de um pedido
    - PUT /orders/{id}/ - Atualiza pedido completo
    - PATCH /orders/{id}/ - Atualização parcial (principalmente status)
    - DELETE /orders/{id}/ - Cancela pedido (apenas se pending)
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MediumResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'created_at']
    search_fields = ['shipping_address']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retorna apenas pedidos do usuário autenticado.
        """
        return Order.objects.filter(user=self.request.user).select_related('user')
    
    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        """
        Associa o pedido ao usuário autenticado ao criar.
        """
        serializer.save(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """
        Permite cancelar pedido apenas se estiver com status 'pending'.
        """
        instance = self.get_object()
        
        if instance.status != 'pending':
            return Response(
                {'error': 'Apenas pedidos pendentes podem ser cancelados'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restaura o estoque dos produtos
        for item in instance.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()
        
        # Marca como cancelado em vez de deletar
        instance.status = 'cancelled'
        instance.save()
        
        return Response(
            {'message': 'Pedido cancelado com sucesso'}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Endpoint específico para atualização de status.
        URL: PATCH /orders/{id}/update_status/
        Body: {"status": "processing"}
        """
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'Status é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validação usando o serializer
        serializer = OrderSerializer(order, data={'status': new_status}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """
        Lista todos os pedidos do usuário com informações resumidas.
        URL: GET /orders/my_orders/
        """
        orders = self.get_queryset()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estatísticas de pedidos do usuário.
        URL: GET /orders/statistics/
        """
        orders = self.get_queryset()
        
        total_orders = orders.count()
        total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        status_counts = {}
        for status_choice in Order.STATUS_CHOICES:
            status_key = status_choice[0]
            status_counts[status_key] = orders.filter(status=status_key).count()
        
        return Response({
            'total_orders': total_orders,
            'total_spent': total_spent,
            'orders_by_status': status_counts,
            'average_order_value': total_spent / total_orders if total_orders > 0 else Decimal('0')
        })
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        Lista itens de um pedido específico.
        URL: GET /orders/{id}/items/
        """
        order = self.get_object()
        items = order.items.all()
        serializer = OrderItemDetailSerializer(items, many=True)
        return Response(serializer.data)


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de itens de pedidos.
    Permite operações CRUD em itens individuais (usado principalmente para admin).
    """
    queryset = OrderItem.objects.select_related('order', 'product').all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'product']
    ordering_fields = ['created_at', 'quantity', 'unit_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filtra itens apenas de pedidos do usuário autenticado.
        """
        return super().get_queryset().filter(order__user=self.request.user)
    
    def get_serializer_class(self):
        """
        Usa serializer detalhado para visualização individual.
        """
        if self.action == 'retrieve':
            return OrderItemDetailSerializer
        return OrderItemSerializer
    
    def perform_create(self, serializer):
        """
        Valida se o pedido pertence ao usuário antes de criar item.
        """
        order = serializer.validated_data['order']
        if order.user != self.request.user:
            raise permissions.PermissionDenied("Você não pode adicionar itens a este pedido")
        
        if order.status != 'pending':
            raise permissions.PermissionDenied("Apenas pedidos pendentes podem ser modificados")
        
        serializer.save()
    
    def perform_update(self, serializer):
        """
        Valida se o item pode ser atualizado.
        """
        if self.get_object().order.status != 'pending':
            raise permissions.PermissionDenied("Apenas itens de pedidos pendentes podem ser modificados")
        
        serializer.save()
    
    def perform_destroy(self, serializer):
        """
        Valida se o item pode ser removido.
        """
        item = self.get_object()
        if item.order.status != 'pending':
            raise permissions.PermissionDenied("Apenas itens de pedidos pendentes podem ser removidos")
        
        # Restaura o estoque
        item.product.stock_quantity += item.quantity
        item.product.save()
        
        item.delete()

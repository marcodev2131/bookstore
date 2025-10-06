"""
Classes de paginação customizadas para o Django REST Framework
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class SmallResultsSetPagination(PageNumberPagination):
    """
    Paginação para conjuntos pequenos de resultados - 5 itens por página
    """
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })


class MediumResultsSetPagination(PageNumberPagination):
    """
    Paginação para conjuntos médios de resultados - 10 itens por página
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })


class LargeResultsSetPagination(PageNumberPagination):
    """
    Paginação para conjuntos grandes de resultados - 20 itens por página
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })


class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginação padrão com tamanho configurável via query parameter
    """
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'pagination_info': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                    'first': self.get_first_link() if hasattr(self, 'get_first_link') else None,
                    'last': self.get_last_link() if hasattr(self, 'get_last_link') else None,
                },
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            },
            'results': data
        })
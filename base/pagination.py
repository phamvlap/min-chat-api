from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class ItemIndexPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 1000


class StandardCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 1000
    cursor_query_param = "cursor"
    ordering = "-created_at"

    def get_paginated_response(self, data):
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

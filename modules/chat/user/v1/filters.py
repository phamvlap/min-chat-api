from django_filters import rest_framework as filters

from modules.chat.models import Message


class ListMessageFilter(filters.FilterSet):
    creation_time_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    creation_time_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gt")

    class Meta:
        model = Message
        fields = ["creation_time_before", "creation_time_after"]

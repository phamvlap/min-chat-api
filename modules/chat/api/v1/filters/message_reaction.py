from django_filters import rest_framework as filters

from modules.chat.models import MessageReaction


class ListMessageReactionFilter(filters.FilterSet):
    class Meta:
        model = MessageReaction
        fields = ["reaction_type"]

from email.message import Message
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
import json

from wpp_messages.models import (
    WhatsappMessage
)

from wpp_messages.api.serializers import (
    WhatsappMessageSerializer,
    WhatsappMessageListSerializer
)

class WhatsappMessageViewset(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["consumer_system", "is_canceled", "was_sent"]
    pagination_class = None
    queryset = WhatsappMessage.objects.all().order_by("-created_at")
    serializer_class = WhatsappMessageSerializer
    
    def get_serializer_class(self):
        actions = ["list", "retrieve", "cancel"]
        if self.action in actions:
            return WhatsappMessageListSerializer
        return super().get_serializer_class()
    
    def get_perform_create(self, serializer):
        self.perform_create(serializer)
        self.get_success_headers(serializer.data)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = WhatsappMessage(**serializer.validated_data)

        response_graph_api = None
        if msg.send_now:
            response_graph_api = msg.send_message()
        
            if response_graph_api.status_code == 200:
                return self.get_perform_create(serializer)
            
            return Response(json.loads(response_graph_api.text))

        return self.get_perform_create(serializer)
        

    @action(detail=True, methods=["put", "get"])
    def cancel(self, request, pk=None):
        message_obj = self.get_object()
        if message_obj.is_canceled:
            return Response({"Detail":"Message already canceled."}, status=400)
        
        if not message_obj.was_sent:
            message_obj.is_canceled = True
            message_obj.save()
            serializer = self.get_serializer(message_obj)
            return Response(serializer.data)

        return Response({"Detail":"Can't cancel, this message already sent."}, status=400)


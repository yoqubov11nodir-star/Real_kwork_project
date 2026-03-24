from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, Profile
from .serializers import OrderSerializer, ProfileSerializer
from .ai_matching import get_top_freelancers_for_order, calculate_match_score


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'required_skills']
    ordering_fields = ['created_at', 'initial_budget']

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    @action(detail=True, methods=['get'])
    def top_freelancers(self, request, pk=None):
        order = self.get_object()
        results = get_top_freelancers_for_order(order, limit=10)
        return Response([{
            'username': r['profile'].user.username,
            'full_name': r['profile'].user.get_full_name(),
            'level': r['profile'].level,
            'rating': r['profile'].rating,
            'match_score': r['score_percent'],
        } for r in results])


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def match_score(self, request, pk=None):
        profile = self.get_object()
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response({'error': 'order_id kerak'}, status=400)
        try:
            order = Order.objects.get(pk=order_id)
            score = calculate_match_score(profile, order)
            return Response({'match_score': round(score * 100, 1)})
        except Order.DoesNotExist:
            return Response({'error': 'Buyurtma topilmadi'}, status=404)

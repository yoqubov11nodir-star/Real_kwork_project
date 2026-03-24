from rest_framework import generics, permissions, serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True)
    freelancer_username = serializers.CharField(source='freelancer.username', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'reviewer_username', 'freelancer_username',
            'stars', 'comment', 'communication_score',
            'quality_score', 'deadline_score', 'created_at'
        ]


class ReviewListAPIView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        username = self.request.query_params.get('username')
        qs = Review.objects.all()
        if username:
            qs = qs.filter(freelancer__username=username)
        return qs.order_by('-created_at')

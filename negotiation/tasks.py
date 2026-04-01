from celery import shared_task
from django.utils import timezone


@shared_task
def check_order_deadline(order_pk):
    """
    Buyurtma deadlinini tekshirish.
    Kelishilgan vaqt o'tsa, statusni DELAYED ga o'zgartirish.
    """
    from marketplace.models import Order
    try:
        order = Order.objects.get(pk=order_pk)

        if order.status == 'COMPLETED':
            return f"Order {order_pk} already completed."

        if order.status == 'IN_PROGRESS':
            if order.agreed_deadline and timezone.now() > order.agreed_deadline:
                order.status = 'DELAYED'
                order.save()

                _notify_delay(order)

                return f"Order {order_pk} marked as DELAYED."

        return f"Order {order_pk} status: {order.status}"

    except Order.DoesNotExist:
        return f"Order {order_pk} not found."


@shared_task
def update_freelancer_rating(freelancer_pk):
    """
    Frilanser reytingini qayta hisoblash.
    Barcha review lar o'rtachasini olish.
    """
    from django.contrib.auth.models import User
    from reputation.models import Review

    try:
        user = User.objects.get(pk=freelancer_pk)
        reviews = Review.objects.filter(freelancer=user)

        if reviews.exists():
            avg_rating = reviews.aggregate(
                avg=__import__('django.db.models', fromlist=['Avg']).Avg('stars')
            )['avg']
            user.profile.rating = round(avg_rating, 2)
            user.profile.save(update_fields=['rating'])
            user.profile.update_level()

        return f"Rating updated for {user.username}: {user.profile.rating}"

    except User.DoesNotExist:
        return f"User {freelancer_pk} not found."


@shared_task
def send_deadline_reminders():
    """
    Har kuni ishlaydigan task: yaqinlashayotgan deadline larni tekshirish.
    Celery Beat bilan birga ishlatiladi.
    """
    from marketplace.models import Order
    from datetime import timedelta

    tomorrow = timezone.now() + timedelta(days=1)
    orders = Order.objects.filter(
        status='IN_PROGRESS',
        agreed_deadline__date=tomorrow.date()
    )

    for order in orders:
        _notify_deadline_tomorrow(order)

    return f"{orders.count()} ta buyurtma uchun eslatma yuborildi."


def _notify_delay(order):
    """Kechikish haqida bildirishnoma (email yoki in-app notification)."""
    # Bu yerda email yoki push notification qo'shishingiz mumkin
    from negotiation.models import ChatRoom, Message
    rooms = ChatRoom.objects.filter(order=order)
    for room in rooms:
        # System user sifatida xabar qo'shish
        if room.client:
            Message.objects.create(
                room=room,
                sender=room.client,
                content=f"⚠️ Diqqat! '{order.title}' buyurtmasi uchun belgilangan muddat o'tdi. Holat: KECHIKDI",
                message_type='system'
            )


def _notify_deadline_tomorrow(order):
    """Ertaga deadline haqida eslatma."""
    from negotiation.models import ChatRoom, Message
    rooms = ChatRoom.objects.filter(order=order)
    for room in rooms:
        if room.client:
            Message.objects.create(
                room=room,
                sender=room.client,
                content=f"🔔 Eslatma: '{order.title}' buyurtmasi muddati ertaga tugaydi!",
                message_type='system'
            )

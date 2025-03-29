from django.core.management.base import BaseCommand
from webpush import send_user_notification
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Send scheduled notifications'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        payload = {"head": "Scheduled Notification", "body": "This is your scheduled message."}

        for user in users:
            send_user_notification(user=user, payload=payload, ttl=1000)

        self.stdout.write(self.style.SUCCESS('Successfully sent notifications'))
from team_dashboard.models import Post_Training_Data
from django.core.management.base import BaseCommand

# Clear all rows from the table
class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        Post_Training_Data.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Data has been deleted!!!'))
from django.core.management.base import BaseCommand
from django.db.models import Avg
from team_dashboard.models import Wake_Up_Data  # Change this to your actual model

class Command(BaseCommand):
    help = "Replace None values in a given field with the user's mean"

    def add_arguments(self, parser):
        parser.add_argument("field", type=str, help="The field to clean up (must be a numeric field)")

    def handle(self, *args, **kwargs):
        field_name = kwargs["field"]

        # Check if the field exists in the model
        if not hasattr(Wake_Up_Data, field_name):
            self.stderr.write(self.style.ERROR(f"Field '{field_name}' does not exist in Wake_Up_Data."))
            return

        # Get all unique users
        users = Wake_Up_Data.objects.values_list("user", flat=True).distinct()

        updated_count = 0  # Track number of updates

        for user in users:
            # Calculate mean per user, ignoring None values
            mean_value = Wake_Up_Data.objects.filter(user=user).aggregate(avg_value=Avg(field_name))["avg_value"]

            if mean_value is not None:
                # Update None values with the calculated mean
                num_updated = Wake_Up_Data.objects.filter(user=user, **{f"{field_name}__isnull": True}).update(**{field_name: mean_value})
                updated_count += num_updated

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} rows in field '{field_name}'"))


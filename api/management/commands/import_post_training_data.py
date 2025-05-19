import csv
from django.core.management.base import BaseCommand
from api.models import Post_Training_Data
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Import data from txt file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, newline='') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                
                username = row['user']
                
                try:
                    userObject= User.objects.get(username=username)
                except User.DoesNotExist:
                    print(f"User '{username}' does not exist.")

                Post_Training_Data.objects.update_or_create(
                    date=row['date'],
                    user=userObject,

                    defaults={
                        "type_of_activity":row['type_of_activity'],
                        "time_of_activity":row['time_of_activity'],
                        "perceived_strain_of_activity":row['perceived_strain_of_activity'],
                        "pain":row['pain'],
                        "comments":row['comments']
                    }
                )
        self.stdout.write(self.style.SUCCESS('Data imported successfully!'))
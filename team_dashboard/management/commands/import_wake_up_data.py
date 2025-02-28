import csv
from django.core.management.base import BaseCommand
from team_dashboard.models import Wake_Up_Data
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Import data from txt file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, encoding='latin-1', newline='') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:

                username = row['user']
                
                try:
                    userObject= User.objects.get(username=username)
                except User.DoesNotExist:
                    print(f"User '{username}' does not exist.")

                
                try:
                    Wake_Up_Data.objects.update_or_create(
                        
                        date=row['date'],
                        user=userObject,

                        defaults={
                            "measurement_quality":row['measurement_quality'],
                            "RMSSD":float(row['RMSSD'].replace(",", ".")) if row['RMSSD'] != '' else None, 
                            "SDNN":float(row['SDNN'].replace(",", ".")) if row['SDNN'] != '' else None,
                            "HR":float(row['HR '].replace(",", ".")) if row['HR '] != '' else None,
                            "emotional_wellness":float(row['emotional_wellness'].replace(",", ".")) if row['emotional_wellness'] != '' else None,
                            "hours_of_sleep":float(row['hours_of_sleep'].replace(",", ".")) if row['hours_of_sleep'] != '' else None,
                            "quality_of_sleep":float(row['quality_of_sleep'].replace(",", ".")) if row['quality_of_sleep'] != '' else None,
                            "muscle_pain":float(row['muscle_pain'].replace(",", ".")) if row['muscle_pain'] != '' else None,
                            "tiredness":float(row['tiredness'].replace(",", ".")) if row['tiredness'] != '' else None,
                            "menstruation":row['menstruation'],
                            "injury":row['injury'],
                            "comments":row['comments']
                        }
                    )
                except Exception as e:
                    print(f'date: {row['date']} \n user: {username}')
                    print(f'Error: {e}')
                    print(f'{row}')

                
        self.stdout.write(self.style.SUCCESS('Data imported successfully!'))

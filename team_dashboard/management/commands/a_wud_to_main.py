from django.core.management.base import BaseCommand
from team_dashboard.models import Wake_Up_Data
from team_dashboard.models import Main_data
from django.forms.models import model_to_dict
from decimal import Decimal

class Command(BaseCommand):
    help = 'move data from Wake_Up_Data and Post_training_data to Main_Data'

    def is_instance(self, dict, type):
        for key, value in dict.items():
            if isinstance(value, type):
                dict[key] = float(value)
        return dict
    
    def add_arguments(self, parser):
        parser.add_argument(
            'date',
            type=str,
            help='The date for the wud.'
        )

        parser.add_argument(
            'username',
            type=str,
            help='The username for the user.'
        )

    def handle(self, *args, **options):
        date = options['date']
        username = options['username']

        print(date)
        print(username)
        wake_up_data = Wake_Up_Data.objects.filter(date=date, user__username=username)
        print(wake_up_data)
        
        for entry in wake_up_data:
            try:
                print(entry)
                entry_dict = model_to_dict(entry,exclude=['user','slug', 'date'])

                entry_dict = self.is_instance(entry_dict, Decimal)

                # entry_dict = self.is_instance(entry_dict, Integer)

                Main_data.objects.update_or_create(
                    date=entry.date,
                    user=entry.user,
                    data_collection='wellness',
                    defaults={
                        "data": entry_dict
                    }
                )
            except Exception as e:
                print(e)
                continue
            
        self.stdout.write(self.style.SUCCESS('Finished moving Wake Up Data'))
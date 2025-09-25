from django.core.management.base import BaseCommand
from team_dashboard.models import Wake_Up_Data
from team_dashboard.models import Post_Training_Data
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

    def handle(self, *args, **kwargs):
        wake_up_data = Wake_Up_Data.objects.all()
        
        for entry in wake_up_data:
            try:
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

        post_training_data = Post_Training_Data.objects.all()
        for entry in post_training_data:
            try:
                entry_dict = model_to_dict(entry,exclude=['user','slug', 'date'])
                Main_data.objects.update_or_create(
                    date=entry.date,
                    user=entry.user,
                    data_collection='training',
                    defaults={
                        "data": entry_dict
                    }
                )
            except Exception as e:
                print(e)
                continue
        
        self.stdout.write(self.style.SUCCESS('Finished moving Post Training Data'))
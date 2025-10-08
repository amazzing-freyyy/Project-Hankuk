from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import numpy as np
from team_dashboard.models import *
from django.forms.models import model_to_dict
from decimal import Decimal

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()

# @receiver(post_save, sender=Wake_Up_Data)
# def new_WUD(sender, instance, created, **kwargs):
#     if created:
#         user= instance.user
#         date= instance.date

#         channel_layer = get_channel_layer()

#         # notify for new WUD
#         async_to_sync(channel_layer.group_send)(
#             'newWud',
#             {
#                 'type':'send.notifications',
#                 'message': {
#                     'user': user,
#                     'date': date
#                 }
#             }
#         )

#         data = Wake_Up_Data.objects.filter(user=user, date=date).order_by('-date').all()[0:7].values('date', 'HR', 'RMSSD', 'SDNN')

#         hr= np.array(list(data.values_list('HR',flat=True)))

#         rmssd= np.array(list(data.values_list('RMSSD'))).flatten()

#         sdnn= np.array(list(data.values_list('SDNN'))).flatten()

#         lnrmssd= np.log(rmssd)
#         lnrmssd_target= lnrmssd[-1]

#         linfrmssd= np.abs(0.06 + np.std(lnrmssd) - np.mean(lnrmssd))
#         lsuprmssd= np.abs(0.06 + np.std(lnrmssd) + np.mean(lnrmssd))

#         hr_mean= np.mean(hr)
#         hr_std= np.std(hr)
#         hr_target= hr[0]
#         hr_z_score= (hr_target - hr_mean) / hr_std

#         ss= 1000 / (sdnn / 0.7995) + 5.1174

#         ss_mean= np.mean(ss)
#         ss_std= np.std(ss)
#         ss_target= ss[0]
#         ss_z_score= (ss_target + ss_mean) / ss_std

#         lnrmssd_alert=lnrmssd_target > lsuprmssd or lnrmssd_target < linfrmssd
#         hr_alert=np.abs(hr_z_score) > 2.5
#         ss_alert=np.abs(ss_z_score) > 2.5

#         alerts={
#             'lnrmssd_alert': lnrmssd_alert,
#             'hr_alert': hr_alert,
#             'ss_alert': ss_alert
#         }

#         # notify if any alert
#         if lnrmssd_alert or hr_alert or ss_alert:
#             async_to_sync(channel_layer.group_send)(
#             'alert',
#             {
#                 'type':'send.notifications',
#                 'message': {
#                     'user': user,
#                     'date': date,
#                     'alert': alerts
#                 }
#             }
#         )

def is_instance(dict, type):
        for key, value in dict.items():
            if isinstance(value, type):
                dict[key] = float(value)
        return dict

@receiver(post_save, sender=Wake_Up_Data)
def new_wellness_main_data(sender, instance, created, **kwargs):
    if not created:
        return
    
    user= instance.user
    date= instance.date

    my_dict = model_to_dict(instance,exclude=['user','slug', 'date'])

    my_dict = is_instance(my_dict, Decimal)

    Main_data.objects.update_or_create(
        date=date,
        user=user,
        data_collection='wellness',
        defaults={
            "data": dict
        }
    )


@receiver(post_save, sender=Post_Training_Data)
def new_training_main_data(sender, instance, created, **kwargs):
    if not created:
        return
    
    user= instance.user
    date= instance.date

    dict = model_to_dict(instance,exclude=['user','slug', 'date'])

    dict = is_instance(dict, Decimal)

    Main_data.objects.update_or_create(
        date=date,
        user=user,
        data_collection='training',
        defaults={
            "data": dict
        }
    )

@receiver(post_save, sender=Main_data)
def new_training_main_data(sender, instance, created, **kwargs):
    if not created:
        return
    
    user= instance.user
    date= instance.date
    collection= instance.data_collection

    data = instance.data or {}
    
    if collection == 'wellness':
        Wake_Up_Data.objects.update_or_create(
            date=date,
            user=user,
            defaults = {
                'measurement_quality': data.get('measurement_quality'),
                'RMSSD': data.get('RMSSD'),
                'SDNN': data.get('SDNN'),
                'HR': data.get('HR'),
                'emotional_wellness': data.get('emotional_wellness'),
                'chispa': data.get('chispa'),
                'hours_of_sleep': data.get('hours_of_sleep'),
                'quality_of_sleep': data.get('quality_of_sleep'),
                'muscle_pain': data.get('muscle_pain'),
                'tiredness': data.get('tiredness'),
                'menstruation': data.get('menstruation'),
                'injury': data.get('injury'),
                'comments': data.get('comments', ''),
            }
        )
    elif collection == 'training':
        Post_Training_Data.objects.update_or_create(
            date=date,
            user=user,
            defaults={
                'type_of_activity': data.get('type_of_activity'),
                'time_of_activity': data.get('time_of_activity'),
                'perceived_strain_of_activity': data.get('perceived_strain_of_activity'),
                'pain': data.get('pain'),
                'comments': data.get('comments'),
            }
        )
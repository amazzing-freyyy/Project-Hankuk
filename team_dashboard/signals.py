from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Wake_Up_Data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import numpy as np

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Wake_Up_Data)
def new_WUD(sender, instance, created, **kwargs):
    if created:
        user= instance.user
        date= instance.date

        channel_layer = get_channel_layer()

        # notify for new WUD
        async_to_sync(channel_layer.group_send)(
            'newWud',
            {
                'type':'send.notifications',
                'message': {
                    'user': user,
                    'date': date
                }
            }
        )

        data = Wake_Up_Data.objects.filter(user=user, date=date).order_by(-date).all()[-7:].values('date', 'HR', 'RMSSD', 'SDNN')

        hr= np.array(list(data.values_list('HR',flat=True)))

        rmssd= np.array(list(data.values_list('RMSSD'))).flatten()

        sdnn= np.array(list(data.values_list('SDNN'))).flatten()

        lnrmssd= np.log(rmssd)
        lnrmssd_target= lnrmssd[-1]

        linfrmssd= np.abs(0.06 + np.std(lnrmssd) - np.mean(lnrmssd))
        lsuprmssd= np.abs(0.06 + np.std(lnrmssd) + np.mean(lnrmssd))

        hr_mean= np.mean(hr)
        hr_std= np.std(hr)
        hr_target= hr[-1]
        hr_z_score= (hr_target - hr_mean) / hr_std

        ss= 1000 / (sdnn / 0.7995) + 5.1174

        ss_mean= np.mean(ss)
        ss_std= np.std(ss)
        ss_target= ss[-1]
        ss_z_score= (ss_target + ss_mean) / ss_std

        lnrmssd_alert=lnrmssd_target > lsuprmssd or lnrmssd_target < linfrmssd
        hr_alert=np.abs(hr_z_score) > 2.5
        ss_alert=np.abs(ss_z_score) > 2.5

        alerts={
            'lnrmssd_alert': lnrmssd_alert,
            'hr_alert': hr_alert,
            'ss_alert': ss_alert
        }

        # notify if any alert
        if lnrmssd_alert or hr_alert or ss_alert:
            async_to_sync(channel_layer.group_send)(
            'alert',
            {
                'type':'send.notifications',
                'message': {
                    'user': user,
                    'date': date,
                    'alert': alerts
                }
            }
        )
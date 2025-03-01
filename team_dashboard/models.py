from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from PIL import Image

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    M_OR_F = [
        ('m', 'M'),
        ('f', 'F')
    ]

    gender = models.CharField( max_length=1, choices=M_OR_F, blank= False, default=M_OR_F[0][0])
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_avatar_url(self):
        if self.avatar:
             return self.avatar.url
        return '/static/images/default_avatar.png'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)

class Wake_Up_Data(models.Model):
    YES_OR_NO=[
        ('yes', 'Yes'),
        ('no', 'No')
    ]
    MEASUREMENT_QUALITY= [
        ('good', 'Good'),
        ('okay', 'Okay'),
        ('poor', 'Poor')
    ]

    date= models.DateField(null=False)
    user= models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='user_wake_up')

    slug= models.SlugField(unique=True, blank=True)

    measurement_quality= models.CharField(max_length=5, choices=MEASUREMENT_QUALITY, blank=True, null=True)
    RMSSD=  models.FloatField(blank=True, null=True)
    SDNN= models.FloatField(blank=True, null=True)
    HR= models.FloatField(blank=True, null=True)
    emotional_wellness= models.DecimalField(max_digits= 10, decimal_places=2,blank=True, null=True)
    chispa= models.DecimalField(max_digits= 10, decimal_places=2,blank=True, null=True)
    hours_of_sleep= models.DecimalField(max_digits= 10, decimal_places=2,blank=True, null=True)
    quality_of_sleep= models.DecimalField(max_digits= 10, decimal_places=2,blank=True, null=True)
    muscle_pain= models.DecimalField(max_digits= 10, decimal_places=2,blank=True, null=True)
    tiredness= models.DecimalField(max_digits= 10, decimal_places=2,blank=True, null=True)
    menstruation= models.CharField(max_length=20, choices= YES_OR_NO, blank=True, null=True)
    injury= models.CharField(max_length=20, choices= YES_OR_NO, blank=True, null=True)
    comments= models.TextField()


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user.get_username() + str(self.date))
        super().save(*args, **kwargs)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['date', 'user'], name='unique_wake_up')
        ]

class Post_Training_Data(models.Model):
    date= models.DateTimeField(null= False)
    user= models.ForeignKey(User, on_delete= models.CASCADE, null= False, related_name='user_post_training')
    type_of_activity= models.TextField(blank=True, null=True)
    time_of_activity= models.DecimalField(max_digits= 10, decimal_places=2, blank=True, null=True)
    perceived_strain_of_activity= models.DecimalField(max_digits= 10, decimal_places=2,blank=True, null=True)
    pain= models.TextField(null=True, blank=True)
    comments= models.TextField(null=True, blank=True)
    slug= models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user.get_username() + str(self.date))
        super().save(*args, **kwargs)

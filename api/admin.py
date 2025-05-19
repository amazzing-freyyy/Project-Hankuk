from django.contrib import admin
from .models import Profile, Wake_Up_Data, Post_Training_Data

class Wake_Up_Data_Admin(admin.ModelAdmin):
    list_display = ('date', 'user')  # Fields to display in the list view
    search_fields = ('date', 'user')  # Fields that you can search by
    list_filter= ('date', 'user')

class Post_Training_Data_Admin(admin.ModelAdmin):
    list_display = ('date', 'user')  # Fields to display in the list view
    search_fields = ('date', 'user')  # Fields that you can search by
    list_filter= ('date', 'user')

admin.site.register(Profile)
admin.site.register(Wake_Up_Data, Wake_Up_Data_Admin)
admin.site.register(Post_Training_Data, Post_Training_Data_Admin) 

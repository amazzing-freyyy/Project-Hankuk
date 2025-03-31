from rest_framework import serializers
from .models import *

class WUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wake_Up_Data
        fields = ['date', 'measurement_quality', 'RMSSD', 'HR', 'emotional_wellness', 'chispa', 'hours_of_sleep', 'quality_of_sleep', 'muscle_pain', 'tiredness', 'menstruation', 'injury', 'comments']

class PTDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post_Training_Data
        fields = ['date', 'type_of_activity', 'time_of_activity', 'perceived_strain_of_activity', 'pain', 'comments']
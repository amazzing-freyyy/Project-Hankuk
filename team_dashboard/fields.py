from django import forms
from .widgets import TimeSplit, DateTimeSplit, TrainingType
import datetime

class TimeMultiField(forms.MultiValueField):
    widget= TimeSplit

    def __init__(self, *args, **kwargs):
        fields = [forms.IntegerField(min_value=0, attrs={'inputmode':'numeric'}), forms.IntegerField(min_value=0, max_value=59, attrs={'inputmode':'numeric'})]
        super().__init__(fields, *args, **kwargs)

    def compress(self, values):
        if values:
            hours, minutes = values
            return float(hours) + float(minutes)/60
        else:
            return 0

class DateTimeField(forms.MultiValueField):
    widget= DateTimeSplit

    def __init__(self, *args, **kwargs):
        fields = [forms.DateField(), forms.TimeField()]
        super().__init__(fields, *args, **kwargs)

    def compress(self, values):
        if values and values[0] and values[1]:
            return datetime.datetime.combine(values[0], values[1])
        else:
            return None

class TrainingField(forms.MultiValueField):
    widget= TrainingType

    def __init__(self, *args, **kwargs):
        fields = [forms.CharField(max_length=20, required=True), forms.CharField(max_length=20, required=False), forms.CharField(max_length=20, required=False)]
        super().__init__(fields, *args, **kwargs)

    def compress(self, values):
        if values:
            return f'{values[0]}, {values[1]}, {values[2]}'
        else:
            return f' , , '

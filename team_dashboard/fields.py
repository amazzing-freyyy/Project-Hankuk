from django import forms
from .widgets import TimeSplit, DateTimeSplit
import datetime

class TimeMultiField(forms.MultiValueField):
    widget= TimeSplit

    def __init__(self, *args, **kwargs):
        fields = [forms.IntegerField(min_value=0, required=False), forms.IntegerField(min_value=0, max_value=59, required=False)]
        super().__init__(fields, *args, **kwargs)

    def compress(self, values):
        if values:
            hours = values[0] if values[0] is not None  else 0
            minutes = values[1] if values[1]is not None  else 0

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

class LocalDecField(forms.DecimalField):
    def clean(self, value):
        if isinstance(value, str):
            value = value.replace(',', '.')  # Convert comma to dot
        return super().clean(value)

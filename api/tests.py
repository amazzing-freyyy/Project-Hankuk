from django.test import SimpleTestCase
from api.forms import TestTimeSplitForm, TestDateTimeForm

class TestTimeSplit(SimpleTestCase):
   def test_form_submission(self):
      form_data={'time_0':8, 'time_1':0}
      form = TestTimeSplitForm(form_data)

#      print(form.cleaned_data['time'])
      self.assertTrue(form.is_valid())
      self.assertEqual(form.cleaned_data['time'], 8.0)

class TestDateTime(SimpleTestCase):
   def test_form_submission(self):
      form_data={'date_0':'2025-01-01', 'date_1':'12:00'}
      form = TestDateTimeForm(form_data)

#      print(form.cleaned_data['date'])
      self.assertTrue(form.is_valid())
      self.assertEqual(form.cleaned_data['date'].strftime("%m/%d/%Y %H:%M:%S"), '01/01/2025 12:00:00')

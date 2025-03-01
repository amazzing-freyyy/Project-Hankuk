from django import forms
from team_dashboard.widgets import StarRating, DateTimeSplit, DateBtn, TimeSplit
from .models import Profile
from .fields import TimeMultiField, DateTimeField, TrainingField

class WakeUpForm(forms.Form):
    YES_OR_NO=[
        ('no', 'No'),
        ('yes', 'Yes')
    ]
    MEASUREMENT_QUALITY= [ 
        ('good', 'Good'),
        ('okay', 'Okay'), 
        ('poor', 'Poor') 
    ]
    SCALE=[
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ]

    date= forms.DateField(widget=DateBtn(), error_messages={'required':'Hace falta la fecha'} ,)
    measurement_quality= forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-select'}), choices=MEASUREMENT_QUALITY, required=False)
    RMSSD= forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class': 'form-control'}), error_messages={'invalid':'Valor de RMSSD inválido. (Usa punto, no coma.)'}, required=False)
    SDNN= forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class': 'form-control'}), error_messages={'invalid':'Valor de SDNN inválido. (Usa punto, no coma)'}, required=False)
    HR= forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class': 'form-control'}), error_messages={'invalid':'Valor de HR inválido'}, required=False)
    emotional_wellness= forms.IntegerField(widget=StarRating(attrs={'class':'star-rating'}, max_stars=5, tags=['Motivado', 'Normal', 'Desmotivado']), error_messages={'required':'Hace falta el ánimo','invalid':'Valor de ánimo inválido'} ,)
    chispa= forms.IntegerField(widget=StarRating(attrs={'class':'star-rating'}, max_stars=5, tags=['Mucha', 'Moderada', 'Nada']), error_messages={'required':'Hace falta la chispa','invalid':'Valor de chispa inválido'} ,)
    hours_of_sleep= TimeMultiField(error_messages={'required':'Hace falta un valor en las horas de sueño'})
    quality_of_sleep= forms.IntegerField(widget=StarRating(attrs={'class':'star-rating'}, max_stars=5, tags=['Muy Buena', 'Buena', 'Problemas al dormir', 'Muy Mala', 'No dormí']), error_messages={'required':'Hace falta la calidad de sueño.', 'invalid':'Valor de calidad de sueño inválido'} ,)
    muscle_pain= forms.IntegerField(widget=StarRating(attrs={'class':'star-rating'}, max_stars=5, tags=['Nada', 'Bajo', 'Normal', 'Dolorido', 'Muy Dolorido']), error_messages={'required':'Hace falta saber cuanto te duele.', 'invalid':'Valor de dolor inválido'} ,)
    tiredness= forms.IntegerField(widget=StarRating(attrs={'class':'star-rating'}, max_stars=5, tags=['Recuperado', 'Normal', 'Fatigado']), error_messages={'required':'Hace falta saber cuanto haz recuperado.', 'inválid':'Valor de Cansancio inválido'} ,)
    menstruation= forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-select'}), choices=YES_OR_NO)
    injury= forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-select'}), choices=YES_OR_NO)
    comments= forms.CharField(widget=forms.Textarea(attrs={'class':'form-control'}), required=False)

class PostTrainingForm(forms.Form):
    date= DateTimeField()
    type_of_activity= TrainingField(required=False, error_messages={'required':'Hace falta el tipo de actividad'} )
    time_of_activity= forms.DecimalField(widget=forms.TextInput(attrs={'class': 'form-control'}), error_messages={'invalid':'Valor de tiempo inválido.','required':'Hace falta la duración de la actividad'})
    perceived_strain_of_activity= forms.IntegerField(widget=StarRating(attrs={'class':'star-rating'}, max_stars=10, tags=['Max. Esfuerzo', 'Moderado', 'Leve']), error_messages={'invalid':'Valor de esfuerzo inválido.','required':'Hace falta el valor de esfuerzo'}, required=True)
    pain= forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)
    comments= forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)


class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']

class TestTimeSplitForm(forms.Form):
    time= TimeMultiField()

class TestDateTimeForm(forms.Form):
    date = DateTimeField()

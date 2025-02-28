from django.forms.widgets import Widget, MultiWidget, DateInput, TimeInput, NumberInput, Select
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

class StarRating(Widget):
    template_name = 'widgets/starRating.html'

    def __init__(self, attrs = None, max_stars=5, tags=[]):
        super().__init__(attrs)
        self.max_stars = max_stars
        self.tags = tags

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['max_stars'] = self.max_stars
        context['tags'] = self.tags
        context['value'] = value or 0
        context['range'] = list(range(1, self.max_stars+1))[::-1]
        return context

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        context['name'] = name
        return render_to_string(self.template_name, context)

    def value_from_datadict(self, data, files, name):
        return data.get(name, 0)

class DateTimeSplit(MultiWidget):
    template_name= "widgets/timeDate.html"
    def __init__(self, widgets=None, attrs = None):
        widgets=[DateInput(attrs={'type':'date'}),
                 TimeInput(attrs={'type':'time'})]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return[value[0], value[1]]
        return [None, None]

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value=[None, None]
        else:
            value=self.decompress(value)

        rendered_widgets = [widget.render(f'{name}_{i}', value[i], attrs) for i, widget in enumerate(self.widgets)]

        context = {
            'widgets': rendered_widgets,
            'name': name,
            'attrs': self.build_attrs(attrs),
        }
        return render_to_string(self.template_name, context)
    
class DateBtn(Widget):
    template_name= "widgets/date.html"
    def __init__(self, attrs = None):
        super().__init__(attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        context['name'] = name
        return render_to_string(self.template_name, context)
    
class TimeSplit(MultiWidget):
    template_name= "widgets/time.html"

    def __init__(self, widgets=None, attrs = None):
        widgets=[NumberInput(attrs=attrs),
                 NumberInput(attrs=attrs)]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            hours = int(value)
            minutes = (int(value)-hours) * 60
            return [hours, minutes]
        return [0, 0]

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value=[0, 0]
        elif isinstance(value, (float, int)):
            value = self.decompress(value)

        rendered_widgets = [widget.render(f'{name}_{i}', value[i], attrs) for i, widget in enumerate(self.widgets)]

        context = {
            'widgets': rendered_widgets,
            'name': name,
            'attrs': self.build_attrs(attrs),
        }
        return render_to_string(self.template_name, context)

class TrainingType(MultiWidget):
    template_name= 'widgets/trainingtype.html'

    TYPE_OF_TRAINING=[
        ('',''),
        ('taekwondo', 'Taekwondo'),
        ('físico', 'Físico'),
        ('competición', 'Competición'),
        ('recovery', 'Recovery'),
        ('mental coaching', 'Mental Coaching'),
    ]

    PHYSICAL_TRAINING_TYPE=[
        ('',' '),
        ('fuerza','Fuerza'),
        ('específico','Específico'),
        ('alterofilia', 'Arterofilia'),
        ('test','Test'),
    ]

    TAEKWONDO_TRAINING_TYPE=[
        ('',' '),
        ('velocidad','Velocidad'),
        ('soltura','Soltura'),
        ('libre','Libre'),
        ('técnico táctico','Técnico Táctico'),
        ('paos','Paos'),
        ('combate', 'Combate'),
    ]

    def __init__(self, widgets=None, attrs= None):
        widgets= [Select(choices=self.TYPE_OF_TRAINING),Select(choices=self.PHYSICAL_TRAINING_TYPE),Select(choices=self.TAEKWONDO_TRAINING_TYPE)]
        super().__init__(widgets, attrs) 

    def decompress(self, value):
        if value:
            [training, physical_training, tkd_training] = value.split(", ")
            return [training, physical_training, tkd_training]
        return ['', '','']

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value=["", "", ""]
        elif isinstance(value, (str, bytes)):
            value = self.decompress(value)

        rendered_widgets = [widget.render(f'{name}_{i}', value[i], attrs) for i, widget in enumerate(self.widgets)]

        context = {
            'widgets': rendered_widgets,
            'name': name,
            'attrs': self.build_attrs(attrs),
        }
        return render_to_string(self.template_name, context)

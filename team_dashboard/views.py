from django.http.response import HttpResponse as HttpResponse
from django.views.generic.list import ListView
from django.views.generic.edit import FormView
from django.contrib.auth.models import User, Group
from team_dashboard.models import Wake_Up_Data, Post_Training_Data
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import WakeUpForm, PostTrainingForm, AvatarUploadForm
from django.views.generic import TemplateView
import plotly.graph_objs as go
from django.db.models import Avg, F, Window, StdDev, RowRange
from django.db.models.functions import Ln, RowNumber
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from datetime import datetime
import json
from plotly.subplots import make_subplots
import logging

logger = logging.getLogger(__name__) 

class RedirectView(LoginRequiredMixin, TemplateView):
    template_name= 'redirect.html'

    def get(self, request, *args, **kwargs):
        if request.user.groups.filter(name='coaches').exists():
            return redirect('coach_home')
        if request.user.groups.filter(name='athletes'):
            return redirect('athlete_home')
        else:
            return redirect('admin:index')

class Wellness_Dashboard(LoginRequiredMixin, TemplateView):
    template_name= 'wellness_dashboard.html'

    def get_chart_data(self, start_date=datetime.now()):
        #get selected athlete
        athlete_id = self.kwargs.get('user')
        athlete = User.objects.filter(id= athlete_id).first()

        #get all entries
        row_data = Wake_Up_Data.objects.filter(user=athlete).all().annotate(
            lnrmssd=Ln('RMSSD'),
            row_num=Window(
                expression=RowNumber(),
                order_by=F('date').asc()
            )

        )
        
        #calculate values, then filter entries based on desired interval
        interval = 30
        graph_data= (
            row_data
            .values('date', 'lnrmssd', 'SDNN', 'RMSSD', 'HR','hours_of_sleep', 'emotional_wellness', 'quality_of_sleep', 'tiredness', 'comments', 'menstruation', 'muscle_pain', 'chispa')
            .annotate(
                    rolling_avgs_lnrmssd= Window(
                        expression=Avg('lnrmssd'),
                        frame=RowRange(start=-interval, end=0),
                        order_by=F('date').asc()
                    ), 
                    rolling_stds_lnrmssd= Window(
                        expression=StdDev('lnrmssd'),
                        frame=RowRange(start=-interval, end=0),
                        order_by=F('date').asc()),
                    rolling_avg_sleep= Window(
                        expression=Avg('hours_of_sleep'),
                        frame=RowRange(start=-interval, end=0),
                        order_by=F('date').asc())
            ).filter(date__lte= start_date).order_by('-date')
        )

        dates= sorted(set(measurement['date'] for measurement in graph_data))
        s_sp_by_date = {date: 0 for date in dates}
        lnrmssd_by_date = {date: 0 for date in dates}
        linfrmssd_by_date = {date: 0 for date in dates}
        lsuprmssd_by_date = {date: 0 for date in dates}
        hr_by_date = {date: 0 for date in dates}
        hrs_sleep = graph_data[0]['hours_of_sleep'] if graph_data[0]['hours_of_sleep'] else 0
        emo_wellness = graph_data[0]['emotional_wellness'] if graph_data[0]['emotional_wellness'] else 0
        q_sleep = graph_data[0]['quality_of_sleep'] if graph_data[0]['quality_of_sleep'] else 0
        tiredness = graph_data[0]['tiredness'] if graph_data[0]['tiredness'] else 0
        muscle_pain= 5 - graph_data[0]['muscle_pain'] if graph_data[0]['muscle_pain'] else 0
        chispa= graph_data[0]['chispa'] if graph_data[0]['chispa'] else 0
        sum= emo_wellness + q_sleep + tiredness - muscle_pain + chispa
        comments= graph_data[0]['comments']
        menstruation= graph_data[0]['menstruation']
        
        def indicator_sleep(value):
            if value > 7.5:
                return "&#128309;"
            elif value < 6.5:
                return "&#128308;"
            else:
                return "&#128310;"

        def indicator(value, red=2, blue=4):
            if value >= blue:
                return "&#128309;"
            elif value <= red:
                return "&#128308;"
            else:
                return "&#128310;"
            
        def m_indicator(value):
            if value == 'No' or value == 'no':
                return "&#128309;"
            else:
                return "&#128310;"

        for measurement in graph_data:
            date = measurement['date']
            lnrmssd = measurement['lnrmssd'] 
            linfrmssd = abs(0.6 + measurement['rolling_stds_lnrmssd'] - measurement['rolling_avgs_lnrmssd'])
            lsuprmssd = abs(0.6 + measurement['rolling_stds_lnrmssd'] + measurement['rolling_avgs_lnrmssd'])
            sd1= 0.7071 * measurement['RMSSD']
            sd2= (measurement['SDNN'] / 0.7995)+5.1174
            ss = 1000 / sd2
            s_sp = ss/sd1


            lnrmssd_by_date[date] = lnrmssd
            linfrmssd_by_date[date] = linfrmssd
            lsuprmssd_by_date[date] = lsuprmssd
            s_sp_by_date[date] = s_sp
            hr_by_date[date] = measurement['HR']

        fig = make_subplots(rows=6, cols=1,
                            subplot_titles=("Radar de Wellness", "Tabla de Wellness I", "Tabla de Wellness II", "Comentarios","LnRMSSD", "Stress Score"),
                            specs=[[{'type':'polar'}],
                                   [{'type':'table'}],
                                   [{'type':'table'}],
                                   [{'type':'table'}],
                                   [{'type':'xy', 'secondary_y': True}],
                                   [{'type':'xy', 'secondary_y':False}]],)
        fig.update_layout(
            showlegend=False,
            autosize=True,
            dragmode= 'pan',
            hovermode='closest',
        )

        lnrmssd_trace= go.Scatter(
            x=list(lnrmssd_by_date.keys()),
            y=list(lnrmssd_by_date.values()),
            mode='lines+markers',
            name='LnRMSSD',
            yaxis='y1'
        )
        linfrmssd_trace= go.Scatter(
            x=list(linfrmssd_by_date.keys()),
            y=list(linfrmssd_by_date.values()),
            mode='lines+markers',
            name='Límite Inferior',
            yaxis='y1'
        )
        lsuprmssd_trace= go.Scatter(
            x=list(lsuprmssd_by_date.keys()),
            y=list(lsuprmssd_by_date.values()),
            mode='lines+markers',
            name='Límite Superior',
            yaxis='y1'
        )
        hr_trace= go.Bar(
            x=list(hr_by_date.keys()),
            y=list(hr_by_date.values()),
            name= 'HR',
            yaxis='y2',
            marker=dict(color='#5c2d02')
        )

        xaxis_layout=dict(
                type="date",
                rangeselector=dict(
                    buttons=list([
                        dict(count=14,
                             label='1w',
                             step="day",
                             stepmode="backward"),
                        dict(count=1.3,
                             label='1m',
                             step="month",
                             stepmode="backward"),
                        dict(count=6,
                            label="6m",
                            step="month",
                            stepmode="backward"),
                        dict(count=1,
                            label="1y",
                            step="year",
                            stepmode="backward"),
                        dict(step="all")
                    ])
                ),
            )
        
        lnrmssd_traces= [lnrmssd_trace, linfrmssd_trace, lsuprmssd_trace, hr_trace]
        # lnrmssd_traces= [lnrmssd_trace, linfrmssd_trace, lsuprmssd_trace]
        fig.add_traces(data=lnrmssd_traces, rows=5, cols=1, secondary_ys=[True,True,True,False])
        fig.update_layout(
            xaxis=xaxis_layout,
            xaxis_title="Fecha",
            yaxis_title='LnRMSSD + HR'
        )

        s_sp_trace= go.Scatter(
            x=list(s_sp_by_date.keys()),
            y=list(s_sp_by_date.values()),
            mode='lines+markers',
            name='SDNN',
        )

        fig.add_trace(trace=s_sp_trace, row=6, col=1)
        fig.update_layout(
            xaxis2=xaxis_layout,
            xaxis2_title="Fecha",
        )

        radar_trace = go.Scatterpolar(
            r= [q_sleep, emo_wellness, tiredness, chispa],
            theta=['calidad de sueño','ánimo', 'recuperación', 'chispa'],
            fill= 'toself',
            name= 'Medida actual'
        )

        fig.add_traces(radar_trace, rows=1,cols=1)
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                ),angularaxis=dict(
                    rotation=45
                )),
            margin=dict(
                t=80, 
            )
        )
        
        lightgrey= 'aliceblue'
        white= 'lightblue'
        table_trace = go.Table(
            header=dict(values=["Variable", "Valor", "Indicador"]),
            cells= dict(values=[['calidad de sueño', 'ánimo', 'recuperación', 'chispa', 'dolor', 'suma'],
                                [ q_sleep, emo_wellness, tiredness, chispa, muscle_pain, sum],
                                [indicator(q_sleep), indicator(emo_wellness), indicator(tiredness), indicator(chispa), indicator(muscle_pain+5), indicator(sum, red=9, blue=15)]],
                        fill_color = [[lightgrey,lightgrey,lightgrey,lightgrey, lightgrey,white]],)
        )
        fig.add_trace(trace=table_trace, row=2, col=1)

        table_trace = go.Table(
            header=dict(values=["Variable", "Valor", "Indicador"]),
            cells= dict(values=[['horas de sueño', 'menstruación'],
                                [hrs_sleep, menstruation],
                                [indicator_sleep(hrs_sleep), m_indicator(menstruation)]],
                        fill_color = [[lightgrey,lightgrey]],)
        )
        fig.add_trace(trace=table_trace, row=3, col=1)

        comments_trace = go.Table(
            cells= dict(values=[comments])
        )
        fig.add_trace(trace=comments_trace, row=4, col=1)

        data = {'report': json.loads(fig.to_json())}

        return data

    def get_context_data(self, **kwargs): 
        if self.request.user.is_authenticated: 
            context = super().get_context_data(**kwargs)
            context['chart_data'] = json.dumps(self.get_chart_data())
            context['athlete'] = User.objects.filter(id= self.kwargs.get('user')).first()
            context['avatar_url'] = User.objects.filter(id= self.kwargs.get('user')).first().profile.get_avatar_url()

        return context
    
    def post(self, request, *args, **kargs):
        data = json.loads(request.body)
        print(request)
        start_date = data.get('start_date')
        chart_data = self.get_chart_data(start_date=start_date)
        return JsonResponse(chart_data)

class Coach_Home(LoginRequiredMixin, ListView):
    model = Wake_Up_Data
    template_name= 'coach_home.html'
    context_object_name= 'wake_up_data'
  
    def get_context_data(self, **kwargs): 
        if self.request.user.is_authenticated:
            context = super().get_context_data(**kwargs)
            # get all athletes
            athletes = Group.objects.get(name= 'athletes').user_set.all()
            
            context['data'] = []
            #last three entries
            for athlete in athletes:
                query = Wake_Up_Data.objects.filter(user=athlete).order_by("-date").first()
                
                date = query.date
                animo= query.emotional_wellness if query.emotional_wellness else 0
                dolor= -query.muscle_pain if query.muscle_pain else 0
                chispa= query.chispa if query.chispa else 0
                recuperacion= query.tiredness if query.tiredness else 0
                calidad_s= query.quality_of_sleep if query.quality_of_sleep else 0
                suma= animo + dolor + chispa + recuperacion + calidad_s
                
                if suma > 14:
                    alert = 'green'
                elif suma < 10:
                    alert = 'red'
                else:
                    alert = 'yellow'

                

                # if len(query) ==3:
                #     wellness_values = [entry.emotional_wellness for entry in query]
                #     date = query[0].date
                #     consecutives = 0
                #     for i in wellness_values:
                #         if i <= 2.0:
                #             consecutives = consecutives + 1

                #     if consecutives < 2:
                #         alert = 'green'
                #     elif consecutives == 2:
                #         alert = 'yellow'
                #     else:
                #         alert = 'red'  

                context['data'].append({'user': athlete, 'alert': alert, 'date':date})

                context['full_name'] = self.request.user.get_full_name()
                context['is_staff']= self.request.user.groups.filter(name='coaching_staff').exists()
        return context

class WakeUpFormView(LoginRequiredMixin, FormView):
    template_name= 'wake_up_form.html'
    form_class= WakeUpForm
    success_url= '/home/'

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            userObject= self.request.user

            Wake_Up_Data.objects.update_or_create(
                date= form.cleaned_data['date'],
                user=userObject,

                defaults={
                    "measurement_quality":form.cleaned_data['measurement_quality'],
                    "RMSSD":form.cleaned_data['RMSSD'], 
                    "SDNN":form.cleaned_data['SDNN'],
                    "HR":form.cleaned_data['HR'],
                    "emotional_wellness":form.cleaned_data['emotional_wellness'],
                    'chispa':form.cleaned_data['chispa'],
                    "hours_of_sleep":form.cleaned_data['hours_of_sleep'],
                    "quality_of_sleep":form.cleaned_data['quality_of_sleep'],
                    "muscle_pain":form.cleaned_data['muscle_pain'],
                    "tiredness":form.cleaned_data['tiredness'],
                    "menstruation":form.cleaned_data['menstruation'],
                    "injury":form.cleaned_data['injury'],
                    "comments":form.cleaned_data['comments']
                }
            )
        return super().form_valid(form) 
    
    def form_invalid(self, form):
        # Call the parent class's method to maintain the normal behavior
        response = super().form_invalid(form)
        
        # You can add any other context data you want here if needed
        response.context_data['form_errors'] = form.errors
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context['username'] = self.request.user.get_username()
            context['full_name'] = self.request.user.get_full_name()
        else:
            context['username'] = ''
            context['full_name'] = ''

        return context
    
class PostTrainingFormView(LoginRequiredMixin, FormView):
    template_name= 'post_training_form.html'
    form_class= PostTrainingForm
    success_url= '/home/'

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            userObject= self.request.user

            Post_Training_Data.objects.update_or_create(
                    date=form.cleaned_data['date'],
                    user=userObject,

                    defaults={
                        "type_of_activity":form.cleaned_data['type_of_activity'],
                        "time_of_activity":form.cleaned_data['time_of_activity'],
                        "perceived_strain_of_activity":form.cleaned_data['perceived_strain_of_activity'],
                        "pain":form.cleaned_data['pain'],
                        "comments":form.cleaned_data['comments']
                    }
            )

        return super().form_valid(form)
        
    def form_invalid(self, form):
        # Call the parent class's method to maintain the normal behavior
        response = super().form_invalid(form)
        print(form.errors)
        # You can add any other context data you want here if needed
        response.context_data['form_errors'] = form.errors
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated: 
            context['username'] = self.request.user.get_username()
            context['full_name'] = self.request.user.get_full_name()
        else:
            context['username'] = ''
            context['full_name'] = ''

        return context
   
class Athlete_Home(LoginRequiredMixin, TemplateView):
    template_name= 'athlete_home.html'
    
    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)

        if self.request.user.is_authenticated: 
            context['username'] = self.request.user.get_username()
            context['full_name'] = self.request.user.get_full_name()
            context['user_group'] = str(self.request.user.groups.all()[0])
            context['id'] = self.request.user.id 
        
        return context

class Login(LoginView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('redirect')
        return super().get(request,*args, **kwargs)

#class AvatarUpdateView(UpdateView):
#    model = Profile
#    form_class = AvatarUploadForm
#    template_name = 'upload_avatar.html'
#    success_url = reverse_lazy('athlete_home')

#    def get_object(self, queryset=None):
#        return self.request.user.profile

def profile(request):
    if request.method == 'POST':
        form = AvatarUploadForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            return redirect('admin')  # Redirect to profile page after upload
    else:
        form = AvatarUploadForm(instance=request.user.profile)

    return render(request, 'upload_avatar.html', {'form': form})

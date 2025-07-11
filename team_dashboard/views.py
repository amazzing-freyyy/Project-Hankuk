from django.views.generic.list import ListView
from django.views.generic.edit import FormView
from django.contrib.auth.models import User, Group
from team_dashboard.models import Wake_Up_Data, Post_Training_Data
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import WakeUpForm, PostTrainingForm, AvatarUploadForm
from django.views.generic import TemplateView
import plotly.graph_objs as go
from django.db.models import Avg, F, Window, StdDev, RowRange, Sum, Min, Max, ExpressionWrapper, FloatField
from django.db.models.functions import Ln, RowNumber, TruncDate, ExtractYear, ExtractWeek
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView
from datetime import datetime, time, timedelta
import json
from plotly.subplots import make_subplots
import logging
import numpy as np
from collections import Counter

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

    def get_chart_data(self, start_date=None):
        if not start_date:
            start_date= datetime.now()

        #get selected athlete
        athlete_id = self.kwargs.get('user')
        athlete = User.objects.filter(id= athlete_id).first()

        #get all entries
        row_data = Wake_Up_Data.objects.filter(user=athlete).all().annotate(
            lnrmssd=Ln('RMSSD'),
            ss= ExpressionWrapper(
                    1000 / (F('SDNN') / 0.7995) + 5.1174,
                    output_field=FloatField()),
            row_num=Window(
                expression=RowNumber(),
                order_by=F('date').asc()
            )
        )
        
        #calculate values, then filter entries based on desired interval
        interval = 7
        graph_data= (
            row_data
            .values('date', 'lnrmssd', 'ss', 'SDNN', 'RMSSD', 'HR','hours_of_sleep', 'emotional_wellness', 'quality_of_sleep', 'tiredness', 'comments', 'menstruation', 'muscle_pain', 'chispa')
            .annotate(
                    rolling_avgs_lnrmssd= Window(
                        expression=Avg('lnrmssd'),
                        frame=RowRange(start=-interval, end=0),
                        order_by=F('date').asc()), 
                    rolling_stds_lnrmssd= Window(
                        expression=StdDev('lnrmssd'),
                        frame=RowRange(start=-interval, end=0),
                        order_by=F('date').asc()),
                    hr_z_score= ExpressionWrapper(
                        (F('HR') - Window(expression=Avg('HR'), frame=RowRange(start=-interval, end=0), order_by=F('date').asc())) / Window(expression=StdDev('HR'), frame=RowRange(start=-interval, end=0), order_by=F('date').asc()),
                        output_field=FloatField()),
                    ss_z_score= ExpressionWrapper(
                        (F('ss') - Window(expression=Avg('ss'), frame=RowRange(start=-interval, end=0), order_by=F('date').asc())) / Window(expression=StdDev('ss'), frame=RowRange(start=-interval, end=0), order_by=F('date').asc()),
                        output_field=FloatField())
            ).filter(date__lte= start_date).order_by('-date')
        )
        if graph_data.exists():

            dates= sorted(set(measurement['date'] for measurement in graph_data))
            s_sp_by_date = {date: 0 for date in dates}
            ss_by_date = {date: 0 for date in dates}
            ss_z_by_date = {date: 0 for date in dates}
            lnrmssd_by_date = {date: 0 for date in dates}
            linfrmssd_by_date = {date: 0 for date in dates}
            lsuprmssd_by_date = {date: 0 for date in dates}
            hr_by_date = {date: 0 for date in dates}
            hr_z_by_date = {date: 0 for date in dates}

            hrs_sleep = graph_data[0]['hours_of_sleep'] if graph_data[0]['hours_of_sleep'] else 0
            emo_wellness = graph_data[0]['emotional_wellness'] if graph_data[0]['emotional_wellness'] else 0
            q_sleep = graph_data[0]['quality_of_sleep'] if graph_data[0]['quality_of_sleep'] else 0
            tiredness = graph_data[0]['tiredness'] if graph_data[0]['tiredness'] else 0
            muscle_pain= 5 - graph_data[0]['muscle_pain'] if graph_data[0]['muscle_pain'] else 0
            chispa= graph_data[0]['chispa'] if graph_data[0]['chispa'] else 0
            suma= emo_wellness + q_sleep + tiredness - muscle_pain + chispa
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
                linfrmssd = abs(0.06 + measurement['rolling_stds_lnrmssd'] - measurement['rolling_avgs_lnrmssd'])
                lsuprmssd = abs(0.06 + measurement['rolling_stds_lnrmssd'] + measurement['rolling_avgs_lnrmssd'])
                sd1= 0.7071 * measurement['RMSSD']
                ss = measurement['ss']
                s_sp = ss/sd1


                lnrmssd_by_date[date] = lnrmssd
                linfrmssd_by_date[date] = linfrmssd
                lsuprmssd_by_date[date] = lsuprmssd
                ss_by_date[date] = ss

                s_sp_by_date[date] = s_sp
                hr_by_date[date] = measurement['HR']
                hr_z_by_date[date] = measurement['hr_z_score']
                ss_z_by_date[date] = measurement['ss_z_score']

                def check_z_score(value):
                    if abs(value) >=2 and abs(value) < 3:
                        return '#86CE00'
                    elif abs(value) >= 3:
                        return 'red'
                    else:
                        return 'cyan'

            ss_colors = [check_z_score(ss_z_by_date[date]) if not ss_z_by_date[date] == None else 'cyan' for date in list(ss_by_date.keys())]
            hr_colors= [check_z_score(hr_z_by_date[date]) if not hr_z_by_date[date] == None else 'cyan' for date in list(hr_by_date.keys())]

            fig = make_subplots(rows=6, cols=1,
                                subplot_titles=("Radar de Wellness", "Tabla de Wellness I", "Tabla de Wellness II", "Comentarios","HR + LnRMSSD", "S:SP + Stress Score"),
                                specs=[[{'type':'polar'}],
                                    [{'type':'table'}],
                                    [{'type':'table'}],
                                    [{'type':'table'}],
                                    [{'type':'xy', 'secondary_y': True}],
                                    [{'type':'xy', 'secondary_y':True}]],)
            fig.update_layout(
                showlegend=False,
                autosize=True,
                dragmode= 'pan',
                hovermode='closest',
                title= f'Fecha: {graph_data.first()['date'].strftime("%m/%d/%Y")}',
            )

            lnrmssd_trace= go.Scatter(
                x=list(lnrmssd_by_date.keys()),
                y=list(lnrmssd_by_date.values()),
                mode='lines+markers',
                name='LnRMSSD',
                yaxis='y1',
                marker=dict(color='blue')
            )
            linfrmssd_trace= go.Scatter(
                x=list(linfrmssd_by_date.keys()),
                y=list(linfrmssd_by_date.values()),
                mode='lines+markers',
                name='Límite Inferior',
                yaxis='y1',
                marker=dict(color='purple')
            )
            lsuprmssd_trace= go.Scatter(
                x=list(lsuprmssd_by_date.keys()),
                y=list(lsuprmssd_by_date.values()),
                mode='lines+markers',
                name='Límite Superior',
                yaxis='y1',
                marker=dict(color='purple')
            )
            hr_trace= go.Bar(
                x=list(hr_by_date.keys()),
                y=list(hr_by_date.values()),
                name= 'HR',
                yaxis='y2',
                marker=dict(color=hr_colors)
            )

            xaxis_layout=dict(
                    type="date",
                    range=[dates[-1]-timedelta(days=15), dates[-1]+timedelta(days=1)],
                    rangeselector=dict(
                        buttons=list([
                            dict(count=15, label="2W", step="day", stepmode="todate"),   # Last 7 days
                            dict(count=30, label="1M", step="day", stepmode="todate"),
                            dict(count=6, label="6M", step="month", stepmode="todate"),
                            dict(count=1, label="1Y", step="year", stepmode="todate"),
                        ])
                    ),
                )
            
            lnrmssd_traces= [lnrmssd_trace, linfrmssd_trace, lsuprmssd_trace, hr_trace]
            fig.add_traces(data=lnrmssd_traces, rows=5, cols=1, secondary_ys=[True,True,True,False])
            fig.update_layout(
                xaxis=xaxis_layout,
                xaxis_title="Fecha",
                yaxis_title='HR',
                yaxis2_title='LnRMSSD',
            )

            s_sp_trace= go.Scatter(
                x=list(s_sp_by_date.keys()),
                y=list(s_sp_by_date.values()),
                mode='lines+markers',
                name='S:SP',
                yaxis='y3',
                marker=dict(color='blue')
            )

            ss_trace= go.Bar(
                x=list(ss_by_date.keys()),
                y=list(ss_by_date.values()),
                name='Stress Score',
                yaxis='y4',
                marker=dict(color=ss_colors)
            )

            ss_sp_traces= [s_sp_trace, ss_trace]
            fig.add_traces(data=ss_sp_traces, rows=6, cols=1, secondary_ys=[True,False])
            fig.update_layout(
                xaxis2=xaxis_layout,
                xaxis2_title="Fecha",
                yaxis4_title='Stress Score',
                yaxis3_title='S:SP'
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
                                    [ q_sleep, emo_wellness, tiredness, chispa, muscle_pain, suma],
                                    [indicator(q_sleep), indicator(emo_wellness), indicator(tiredness), indicator(chispa), indicator(muscle_pain+5), indicator(suma, red=9, blue=15)]],
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

            data = {'report': json.loads(fig.to_json()), 'config': {'displayModeBar': False, "responsive": True}}
        else:
            
            data= {'report': '', 'config': ''}
        

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
        start_date = data.get('start_date')
        chart_data = self.get_chart_data(start_date=start_date)
        return JsonResponse(chart_data)

class Training_Dashboard(LoginRequiredMixin, TemplateView):
    template_name= 'training_dashboard.html'
    
    def get_chart_data(self, start_date=None):        
        if not start_date:
            start_date= datetime.now()

        interval= 7

        #get selected athlete
        athlete_id = self.kwargs.get('user')
        athlete = User.objects.filter(id= athlete_id).first()

        fields = ['time_of_activity']

        data = {field: list(Post_Training_Data.objects.filter(user=athlete).values_list(field, flat=True)) for field in fields}
        
        bounds = {}
        for field, values in data.items():
            if values:  # Ensure there is data
                q1 = np.percentile(values, 25)
                q3 = np.percentile(values, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                bounds[field] = (lower_bound, upper_bound)

        filters = {}
        for field, (lower, upper) in bounds.items():
            filters[f"{field}__gte"] = lower
            filters[f"{field}__lte"] = upper

        filtered_objects = Post_Training_Data.objects.filter(**filters, user=athlete
                                ).annotate(time_x_rpe_per_day=F("time_of_activity") * F("perceived_strain_of_activity") * F("perceived_strain_of_activity")  # Calculate the average of the product
                                ).values("date", "time_x_rpe_per_day", 'type_of_activity','pain', 'comments'
                                ).order_by("-date")

        time_threshold= time(13,0) 
        time_separated = [filtered_objects.filter(date__time__lt=time_threshold).all().annotate(
            date_only=TruncDate("date")
        ).values(
            "date_only", "time_x_rpe_per_day", 'type_of_activity', 'date','pain', 'comments'
        ), filtered_objects.filter(date__time__gt=time_threshold).all().annotate(
            date_only=TruncDate("date")
        ).values(
            "date_only", "time_x_rpe_per_day", 'type_of_activity', 'date','pain', 'comments'
        )]

        dates= [sorted(set(measurement['date_only'] for measurement in time_separated[0])),
                       sorted(set(measurement['date_only'] for measurement in time_separated[1]))]
        
        time_x_strain2_daily_by_date = [{date: 0 for date in dates[0]},
                                       {date: 0 for date in dates[1]}]

        activities_by_date = [{date: 0 for date in dates[0]},
                            {date: 0 for date in dates[1]}]
        
        for workout  in time_separated:
            i = time_separated.index(workout)
            for measurement in workout:
                date= measurement['date_only']

                time_x_strain2_daily_by_date[i][date] = measurement['time_x_rpe_per_day']
                activities_by_date[i][date] = measurement['type_of_activity']
        
        weekly_data= (filtered_objects
                .annotate(year=ExtractYear('date'), week= ExtractWeek('date'), date_only=TruncDate('date'))
                .values('year', 'week')
                .annotate(
                    total=Sum(F('time_of_activity') * F('perceived_strain_of_activity') * F('perceived_strain_of_activity')),
                    start_date=Min('date_only'),
                    end_date=Max('date_only')
                ).order_by('-start_date'))

        weeks= sorted(set(entry['start_date'] for entry in weekly_data))

        time_x_rpe2_by_week= {week: 0 for week in weeks}
        week_dates= {week: 0 for week in weeks}
        percent_diff= {week: 0 for week in weeks}

        prev_total = None
        for measurement in weekly_data.order_by('start_date'):
            date= measurement['start_date']

            time_x_rpe2_by_week[date] = measurement['total']
            week_dates[date]= f'{measurement['start_date'].strftime("%d-%b-%Y")} a {measurement['end_date'].strftime("%d-%b-%Y")}'

            if prev_total is not None:
                percent_diff[date] = ((measurement['total'] - prev_total)/ prev_total) * 100
            else:
                percent_diff[date] = 0
            
            prev_total= measurement['total']

        last_week= datetime.now() - timedelta(days=7)
        last_week_activities= Post_Training_Data.objects.filter(user=athlete, date__gte=last_week).values('type_of_activity', 'time_of_activity').all()

        activities= {"Fuerza": last_week_activities.filter(type_of_activity__contains="fuerza").aggregate(time=Sum('time_of_activity'))['time'],
                     "Específico": last_week_activities.filter(type_of_activity__contains="específico").aggregate(time=Sum('time_of_activity'))['time'],
                     "Halterofilia": last_week_activities.filter(type_of_activity__contains="halterofilia").aggregate(time=Sum('time_of_activity'))['time'],
                     "Test": last_week_activities.filter(type_of_activity__contains="test").aggregate(time=Sum('time_of_activity'))['time'],
                     "Velocidad": last_week_activities.filter(type_of_activity__contains="velocidad").aggregate(time=Sum('time_of_activity'))['time'],
                     "Soltura": last_week_activities.filter(type_of_activity__contains="soltura").aggregate(time=Sum('time_of_activity'))['time'],
                     "Libre": last_week_activities.filter(type_of_activity__contains="libre").aggregate(time=Sum('time_of_activity'))['time'],
                     "Téc. táctico": last_week_activities.filter(type_of_activity__contains="técnico táctico").aggregate(time=Sum('time_of_activity'))['time'],
                     "Técnico": last_week_activities.filter(type_of_activity__contains="tecnico").aggregate(time=Sum('time_of_activity'))['time'],
                     "Paos": last_week_activities.filter(type_of_activity__contains="paos").aggregate(time=Sum('time_of_activity'))['time'],
                     "Combate": last_week_activities.filter(type_of_activity__contains="combate").aggregate(time=Sum('time_of_activity'))['time'],
                     "Competición": last_week_activities.filter(type_of_activity__contains="competición").aggregate(time=Sum('time_of_activity'))['time'],
                     "Recovery": last_week_activities.filter(type_of_activity__contains="recovery").aggregate(time=Sum('time_of_activity'))['time'],}
        
        comments= filtered_objects.first()['comments']
        pain= filtered_objects.first()['pain']
        
        fig = make_subplots(rows=5, cols=1,
                            subplot_titles=("RPE^2 x Minutos Diario", "RPE^2 x Minutos Semanal", "Resumen de entrenos en la semana",  "Dolores", "Comentarios"),
                            specs=[[{'type':'xy'}],
                                   [{'type':'xy', 'secondary_y': True}],
                                   [{'type':'domain'}],
                                   [{'type':'table'}],
                                   [{'type':'table'}],])

        time_x_rpe2_daily_trace= [go.Bar(
            x=list(time_x_strain2_daily_by_date[0].keys()),
            y=list(time_x_strain2_daily_by_date[0].values()),
            hovertemplate=[f'<b>Minutos x RPE^2:</b> {time_x_strain2_daily_by_date[0][i]}<br><b>Fecha:</b> {i.strftime("%d-%b-%Y")}<br><b>Actividad:</b> {activities_by_date[0][i]}' for i in list(time_x_strain2_daily_by_date[0].keys())],
            textposition='inside',
            name='',
            marker=dict(color="cyan"),
            showlegend=False
        ),go.Bar(
            x=list(time_x_strain2_daily_by_date[1].keys()),
            y=list(time_x_strain2_daily_by_date[1].values()),
            hovertemplate=[f'<b>Minutos x RPE^2:</b> {time_x_strain2_daily_by_date[1][i]}<br><b>Fecha:</b> {i.strftime("%d-%b-%Y")}<br><b>Actividad:</b> {activities_by_date[1][i]}' for i in list(time_x_strain2_daily_by_date[1].keys())],
            textposition='inside',
            name='',
            marker=dict(color="magenta"),
            showlegend=False
        )]

        xaxis_layout=dict(
                type="date",
                range=[dates[0][-1]-timedelta(days=15), dates[0][-1]+timedelta(days=1)],
                rangeselector=dict(
                    buttons=list([
                        dict(count=15, label="2W", step="day", stepmode="todate"),   # Last 7 days
                        dict(count=30, label="1M", step="day", stepmode="todate"),
                        dict(count=6, label="6M", step="month", stepmode="todate"),
                        dict(count=1, label="1Y", step="year", stepmode="todate"),
                    ])
                ),
            )
        
        fig.add_traces(data=time_x_rpe2_daily_trace, rows=1, cols=1)

        time_x_rpe2_weekly_trace= go.Bar(
            x=list(time_x_rpe2_by_week.keys()),
            y=list(time_x_rpe2_by_week.values()),
            width= [1000 * 60 * 60 * 24 * 7] * len(time_x_rpe2_by_week),
            hovertemplate= [f'<b>Minutos x RPE^2:</b> {time_x_rpe2_by_week[i]}<br><b>Fechas:</b> {week_dates[i]}' for i in list(time_x_rpe2_by_week.keys())],
            textposition='inside',
            name='',
            showlegend=False
        )
        percent_diff_trace= go.Scatter(
            x= list(percent_diff.keys()),
            y= list(percent_diff.values()),
            hovertemplate=[f'<b>Diferencia:</b> {percent_diff[i]:.2f}%' for i in list(percent_diff.keys())],
            name='',
            showlegend=False
        )
        
        fig.add_traces(data=[time_x_rpe2_weekly_trace, percent_diff_trace], rows=2, cols=1, secondary_ys=[False, True])
        fig.update_layout(
                    autosize=True,
                    dragmode= 'pan',
                    hovermode='closest',
                    title= f'Fecha: {filtered_objects.first()['date'].strftime("%m/%d/%Y")}',
                    xaxis=xaxis_layout,
                    xaxis_title="Fecha",
                    barmode= 'stack',
                    xaxis2= dict(type='date', range=[weeks[-1]-timedelta(days=60), weeks[-1]+timedelta(days=4)],
                                 rangeselector=dict(
                                    buttons=list([
                                        dict(count=60, label="2M", step="day", stepmode="todate"),
                                        dict(count=180, label="6M", step="day", stepmode="todate"),
                                        dict(count=365, label="1Y", step="day", stepmode="todate"),
                                    ])
                ),)
        )

        weekly_summary_trace = go.Pie(
            labels=list(activities.keys()),
            values=list(activities.values()),
            textposition='inside',
            hovertemplate=[f'<b>Actividad:</b> {i}<br><b>Tiempo:</b> {activities[i]}min' for i in list(activities.keys())],
            name='',
            textinfo= 'label+percent',
            insidetextorientation='radial',
            showlegend=False
        )
        fig.add_trace(trace=weekly_summary_trace, row=3, col=1)

        pain_trace = go.Table(
            cells= dict(values=[pain]),
        )
        fig.add_trace(trace=pain_trace, row=4, col=1)

        comments_trace = go.Table(
            cells= dict(values=[comments]),
        )
        fig.add_trace(trace=comments_trace, row=5, col=1)

        data = {'report': json.loads(fig.to_json()), 'config': {'displayModeBar': False}}

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
            
            interval = 7
            context['data'] = []
            #last three entries
            for athlete in athletes:
                query = Wake_Up_Data.objects.filter(user=athlete).order_by("-date").annotate(
                lnrmssd=Ln('RMSSD'),
                ss= ExpressionWrapper(
                    1000 / (F('SDNN') / 0.7995) + 5.1174,
                    output_field=FloatField()),
                row_num=Window(
                    expression=RowNumber(),
                    order_by=F('date').asc())
                ).annotate(
                    rolling_avgs_lnrmssd= Window(
                        expression=Avg('lnrmssd'),
                        frame=RowRange(start=-interval, end=0),
                        order_by=F('date').asc()), 
                    rolling_stds_lnrmssd= Window(
                        expression=StdDev('lnrmssd'),
                        frame=RowRange(start=-interval, end=0),
                        order_by=F('date').asc()),
                    hr_z_score= ExpressionWrapper(
                        (F('HR') - Window(expression=Avg('HR'), frame=RowRange(start=-interval, end=0), order_by=F('date').asc())) / Window(expression=StdDev('HR'), frame=RowRange(start=-interval, end=0), order_by=F('date').asc()),
                        output_field=FloatField()),
                    ss_z_score= ExpressionWrapper(
                        (F('ss') - Window(expression=Avg('ss'), frame=RowRange(start=-interval, end=0), order_by=F('date').asc())) / Window(expression=StdDev('ss'), frame=RowRange(start=-interval, end=0), order_by=F('date').asc()),
                        output_field=FloatField())
                ).first()

                if query:

                    date = query.date
                    animo= query.emotional_wellness if query.emotional_wellness else 0
                    dolor= query.muscle_pain-5 if query.muscle_pain else 0
                    chispa= query.chispa if query.chispa else 0
                    recuperacion= query.tiredness if query.tiredness else 0
                    calidad_s= query.quality_of_sleep if query.quality_of_sleep else 0
                    suma= animo + dolor + chispa + recuperacion + calidad_s

                    lnrmssd = query.lnrmssd
                    linfrmssd = abs(0.06 + query.rolling_stds_lnrmssd - query.rolling_avgs_lnrmssd)
                    lsuprmssd = abs(0.06 + query.rolling_stds_lnrmssd + query.rolling_avgs_lnrmssd)
                    hr_z = query.hr_z_score
                    ss_z = query.ss_z_score
                    
                    cause=[]
                    try:
                        alert_counter = 0
                        if lnrmssd > lsuprmssd or lnrmssd < linfrmssd:
                            alert_counter = alert_counter + 1
                            cause.append('LnRMSSD')
                            
                        if abs(hr_z) >= 2.5:
                            alert_counter = alert_counter + 1
                            cause.append('HR')

                        if suma < 10:
                            alert_counter = alert_counter + 1
                            cause.append('Suma')

                        if dolor < -2:
                            alert_counter = alert_counter + 1
                            cause.append('Dolor')
                        
                        if abs(ss_z) >= 2.5:
                            alert_counter = alert_counter + 1
                            cause.append('Stress Score')
                    except Exception as e:
                        logger.error(e)

                    alert = 'blue'
                    if alert_counter > 2:
                        alert = 'red'
                    elif alert_counter == 2:
                        alert = 'yellow'
                    elif alert_counter == 1:
                        alert = 'green'
                
                else: 
                    alert= 'grey'
                    date= ''
                    cause=''

                context['data'].append({'user': athlete, 'alert': alert, 'date':date, 'cause':', '.join(cause)})

                context['full_name'] = self.request.user.get_full_name()
                context['is_staff']= self.request.user.groups.filter(name='coaching_staff').exists()
        return context

class Training_Data(LoginRequiredMixin, ListView):
    model = Post_Training_Data
    template_name= 'training_data.html'
    context_object_name= 'post_training_data'
  
    def get_context_data(self, **kwargs): 
        if self.request.user.is_authenticated and self.request.user.is_staff:
            context = super().get_context_data(**kwargs)
            # get all athletes
            athletes = Group.objects.get(name= 'athletes').user_set.all()
            
            context['data'] = []
            #last three entries
            for athlete in athletes:
                query = Post_Training_Data.objects.filter(user=athlete).order_by("-date").first()
                
                date = query.date
                
                context['data'].append({'user': athlete, 'date':date})

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

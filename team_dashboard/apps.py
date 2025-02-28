from django.apps import AppConfig

class TeamDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'team_dashboard'

    def ready(self):
        import team_dashboard.signals

from django.contrib import admin
from .models import (
    ResponsableQSCentral, EvenementQS, RecommendationQS, ActionQS, 
    AuditQS, EvaluationRisqueQS, NotificationQS
)

# Register your models here.
# ==============================================================================
# SECTION VI : QUALITE/SECURITE DES VOLS (QS/SMS)
# ==============================================================================

@admin.register(EvenementQS)
class EvenementQSAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'centre', 'rapporteur', 'niveau_gravite', 'statut')
    list_filter = ('statut', 'niveau_gravite', 'centre')
    search_fields = ('description', 'analyse', 'rapporteur__trigram')

admin.site.register(ResponsableQSCentral)
admin.site.register(RecommendationQS)
admin.site.register(ActionQS)
admin.site.register(AuditQS)
admin.site.register(EvaluationRisqueQS)
admin.site.register(NotificationQS)

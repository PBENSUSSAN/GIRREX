# Generated migration for ArretMaladie enhancements

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0004_certificatmed_date_saisie_certificatmed_saisi_par_and_more'),
    ]

    operations = [
        # Ajouter le champ statut
        migrations.AddField(
            model_name='arretmaladie',
            name='statut',
            field=models.CharField(
                choices=[
                    ('EN_COURS', 'En cours'),
                    ('CLOTURE', 'Clôturé (reprise effective)'),
                    ('ANNULE', 'Annulé (erreur de saisie)')
                ],
                default='EN_COURS',
                max_length=20,
                verbose_name='Statut'
            ),
        ),
        
        # Ajouter cloture_par
        migrations.AddField(
            model_name='arretmaladie',
            name='cloture_par',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='arrets_clotures',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Clôturé par'
            ),
        ),
        
        # Ajouter date_cloture
        migrations.AddField(
            model_name='arretmaladie',
            name='date_cloture',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Date de clôture'
            ),
        ),
    ]

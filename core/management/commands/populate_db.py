# Fichier : core/management/commands/populate_db.py

import datetime
# ==========================================================
#                      LIGNE MANQUANTE À AJOUTER
# ==========================================================
from datetime import date

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
# ... (le reste des imports)```




# Fichier : core/management/commands/populate_db.py

import datetime
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

# Importer tous les modèles nécessaires
from core.models import Agent, Centre, CertificatMed, Role, AgentRole
from competences.models import Brevet, Qualification, MentionUniteAnnuelle, MentionLinguistique, FormationReglementaire, SuiviFormationReglementaire, RegleDeRenouvellement
from activites.models import Vol, SaisieActivite

class Command(BaseCommand):
    help = 'Peuple la base de données avec un jeu de données de test complet et cohérent.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Début du peuplement de la base de données ---'))

        # --- 0. Nettoyage Robuste de la base de données ---
        self.stdout.write('Nettoyage des anciennes données de test...')
        SaisieActivite.objects.all().delete()
        Vol.objects.all().delete()
        MentionUniteAnnuelle.objects.all().delete()
        Qualification.objects.all().delete()
        SuiviFormationReglementaire.objects.all().delete()
        MentionLinguistique.objects.all().delete()
        CertificatMed.objects.all().delete()
        Brevet.objects.all().delete()
        AgentRole.objects.all().delete()
        Role.objects.all().delete()
        RegleDeRenouvellement.objects.all().delete()
        Agent.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Centre.objects.all().delete()
        FormationReglementaire.objects.all().delete()
        Group.objects.all().delete()

        # --- 1. Création des Objets de Base ---
        self.stdout.write('Création des objets de base (Centres, Formations)...')
        istres = Centre.objects.create(nom_centre="DGA EV Istres", code_centre="IST", gere_aps=False, gere_tour=False)
        cazaux = Centre.objects.create(nom_centre="DGA EV Cazaux", code_centre="CAZ", gere_aps=True, gere_tour=True)
        
        raf_aero, _ = FormationReglementaire.objects.get_or_create(nom="RAF AERO", slug='fh-raf-aero', defaults={'periodicite_ans': 3})
        
        # --- 2. Création des Rôles et des Groupes de Permissions ---
        self.stdout.write('Création des Rôles et des Groupes de Permissions...')
        
        grp_controleur, _ = Group.objects.get_or_create(name='Contrôleurs')
        perm_view_centre = Permission.objects.get(codename='view_centre_brevets')
        grp_controleur.permissions.add(perm_view_centre)

        role_controleur, _ = Role.objects.get_or_create(
            nom=Role.RoleName.CONTROLEUR,
            defaults={'scope': Role.RoleScope.OPERATIONNEL, 'level': Role.RoleLevel.EXECUTION}
        )
        role_controleur.groups.add(grp_controleur)

        # --- 3. Création de l'Agent GJN ---
        self.stdout.write('Création de l\'agent GJN, de son socle, et de ses assignations...')
        user_gjn, _ = User.objects.get_or_create(username='gjn', defaults={'first_name': 'Gael', 'last_name': 'JONSON'})
        user_gjn.set_password('password')
        user_gjn.save()
        
        agent_gjn, _ = Agent.objects.get_or_create(
            id_agent=1,
            defaults={'user': user_gjn, 'centre': istres, 'trigram': 'GJN', 'nom': 'JONSON', 'prenom': 'Gael', 'type_agent': 'controleur'}
        )
        AgentRole.objects.create(agent=agent_gjn, role=role_controleur, centre=istres)

        brevet_gjn = Brevet.objects.create(agent=agent_gjn, numero_brevet='B-GJN-2025', date_delivrance=date(2025, 1, 1))
        CertificatMed.objects.create(agent=agent_gjn, date_visite=date(2025, 6, 1), resultat='APTE', date_expiration_aptitude=date(2026, 5, 31))
        MentionLinguistique.objects.create(brevet=brevet_gjn, langue='ANGLAIS', niveau_oaci=4, date_evaluation=date(2025, 5, 1), date_echeance=date(2028, 4, 30))
        SuiviFormationReglementaire.objects.create(brevet=brevet_gjn, formation=raf_aero, date_realisation=date(2025, 4, 1), date_echeance=date(2028, 3, 31))
        
        qual_cam = Qualification.objects.create(brevet=brevet_gjn, centre=istres, type_flux='CAM', type_qualification='CAER', date_obtention=date(2025, 8, 1))
        qual_cag = Qualification.objects.create(brevet=brevet_gjn, centre=istres, type_flux='CAG_ACS', type_qualification='ACS', date_obtention=date(2025, 8, 1))

        MentionUniteAnnuelle.objects.create(qualification=qual_cam, type_flux='CAM', date_debut_cycle=date(2025, 8, 20), date_fin_cycle=date(2026, 8, 19))
        MentionUniteAnnuelle.objects.create(qualification=qual_cag, type_flux='CAG', date_debut_cycle=date(2025, 8, 20), date_fin_cycle=date(2026, 8, 19))
        
        # --- 4. Création de la Règle de Renouvellement ---
        self.stdout.write('Création de la règle de renouvellement...')
        regle, _ = RegleDeRenouvellement.objects.get_or_create(
            nom="Standard National 2025",
            defaults={'seuil_heures_total': 90, 'seuil_heures_cam': 40, 'seuil_heures_cag_acs': 50}
        )
        regle.centres.add(istres, cazaux)

        # --- 5. Création d'un Vol de test avec GJN ---
        self.stdout.write('Création d\'un vol de test pour GJN...')
        vol_test = Vol.objects.create(
            centre=istres, date_vol=date(2025, 8, 21),
            heure_debut_prevue='10:00', duree_prevue=datetime.timedelta(hours=2),
            heure_debut_reelle='10:05', heure_fin_reelle='12:05',
            flux='CAM', indicatif='F-TEST1'
        )
        SaisieActivite.objects.create(vol=vol_test, agent=agent_gjn, role='CONTROLEUR')
        
        self.stdout.write(self.style.SUCCESS('--- Base de données peuplée avec succès ! ---'))
        self.stdout.write(f'Utilisateur créé : gjn / mot de passe : password')
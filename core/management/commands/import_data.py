# core/management/commands/import_data.py

import csv
import os
import re
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Centre, Agent, Licence, Module, Formation

# Chemin vers le dossier contenant les fichiers CSV
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data')

class Command(BaseCommand):
    help = 'Importe les données initiales depuis les fichiers CSV dans le dossier /data'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Début de l'importation des données..."))

        # L'ordre est important à cause des clés étrangères (ForeignKey)
        self.cleanup_data()
        centres_map = self.import_centres_from_agents()
        self.import_agents(centres_map)
        self.import_modules()
        self.import_licences()
        self.import_formations()

        self.stdout.write(self.style.SUCCESS("Importation terminée avec succès !"))

    def cleanup_data(self):
        """ Supprime les anciennes données pour garantir un import propre. """
        self.stdout.write("Nettoyage des anciennes données...")
        Formation.objects.all().delete()
        Licence.objects.all().delete()
        Module.objects.all().delete()
        Agent.objects.all().delete()
        Centre.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Nettoyage terminé."))

    def import_centres_from_agents(self):
        """
        Le fichier centres.csv est vide. On déduit les centres depuis agents.csv.
        Un centre est identifié par les 2 premières lettres du champ 'Nom' (ex: BO, TO, AI).
        """
        self.stdout.write("Création des Centres à partir de agents.csv...")
        filepath = os.path.join(DATA_DIR, 'agents.csv')
        centre_codes = set()
        
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nom = row.get('Nom')
                    if nom:
                        # Extrait les lettres au début du nom (ex: 'BO' de 'BO3')
                        match = re.match(r'([A-Z]+)', nom)
                        if match:
                            centre_codes.add(match.group(1))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Fichier non trouvé: {filepath}"))
            return {}

        centres_map = {}
        for code in sorted(list(centre_codes)):
            centre, created = Centre.objects.get_or_create(
                code_centre=code,
                defaults={'nom_centre': f'Centre {code}'}
            )
            centres_map[code] = centre
            if created:
                self.stdout.write(f"  Centre '{code}' créé.")
        
        self.stdout.write(self.style.SUCCESS(f"{len(centres_map)} centres créés/trouvés."))
        return centres_map

    def import_agents(self, centres_map):
        """ Importe les agents depuis agents.csv """
        self.stdout.write("Importation des Agents...")
        filepath = os.path.join(DATA_DIR, 'agents.csv')
        count = 0
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                id_agent_str = row.get('id_agent')
                if not id_agent_str or not id_agent_str.strip():
                    continue

                try:
                    id_agent = int(id_agent_str)
                    
                    # Déterminer le centre de l'agent
                    centre = None
                    nom_ref = row.get('Nom')
                    if nom_ref:
                        match = re.match(r'([A-Z]+)', nom_ref)
                        if match and match.group(1) in centres_map:
                            centre = centres_map[match.group(1)]

                    Agent.objects.update_or_create(
                        id_agent=id_agent,
                        defaults={
                            'reference': nom_ref,
                            'trigram': row.get('Trigram') or None,
                            'centre': centre
                        }
                    )
                    count += 1
                except (ValueError, TypeError):
                    self.stdout.write(self.style.WARNING(f"  Ligne agent ignorée (ID invalide): {row}"))
        self.stdout.write(self.style.SUCCESS(f"{count} agents importés/mis à jour."))

    def import_modules(self):
        """ Importe les modules depuis modules.csv en gérant les valeurs héritées. """
        self.stdout.write("Importation des Modules...")
        filepath = os.path.join(DATA_DIR, 'modules.csv')
        count = 0
        
        current_module, current_item, current_module_type = "", "", ""

        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                id_module_str = row.get('id_module')
                if not id_module_str:
                    continue
                
                if row.get('MODULE', '').strip(): current_module = row['MODULE'].strip()
                if row.get('ITEM', '').strip(): current_item = row['ITEM'].strip()
                if row.get('module_type', '').strip(): current_module_type = row['module_type'].strip()

                try:
                    date_val = None
                    if row.get('DATE'):
                        date_val = datetime.strptime(row['DATE'], '%Y-%m-%d').date()
                except ValueError:
                    date_val = None
                
                Module.objects.update_or_create(
                    id_module=int(id_module_str),
                    defaults={
                        'module': current_module,
                        'item': current_item,
                        'module_type': current_module_type,
                        'numero': row.get('N°'),
                        'sujet': row.get('SUJET'),
                        'date': date_val,
                        'support': row.get('Support'),
                        'precisions': row.get('Sujet / Précisions'),
                    }
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} modules importés/mis à jour."))

    def import_licences(self):
        """ Importe les licences depuis licences.csv """
        self.stdout.write("Importation des Licences...")
        filepath = os.path.join(DATA_DIR, 'licences.csv')
        count = 0
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                id_agent_str = row.get('id_agent')
                id_licence_str = row.get('id_licence')
                if not id_agent_str or not id_licence_str:
                    continue

                try:
                    agent = Agent.objects.get(id_agent=int(id_agent_str))
                    
                    date_validite = None
                    if row.get('date_validite'):
                        date_validite = datetime.strptime(row['date_validite'], '%Y-%m-%d').date()

                    Licence.objects.create(
                        id_licence=int(id_licence_str),
                        agent=agent,
                        num_licence=row.get('num_licence'),
                        date_validite=date_validite
                    )
                    count += 1
                except Agent.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Agent ID {id_agent_str} non trouvé pour la licence. Ligne ignorée."))
                except (ValueError, TypeError):
                    self.stdout.write(self.style.WARNING(f"  Ligne licence ignorée (données invalides): {row}"))
        self.stdout.write(self.style.SUCCESS(f"{count} licences importées."))

    def import_formations(self):
        """ Importe les formations depuis formations.csv """
        self.stdout.write("Importation des Formations...")
        filepath = os.path.join(DATA_DIR, 'formations.csv')
        count = 0
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                id_agent_str = row.get('id_agent')
                id_formation_str = row.get('id_formation')

                if not id_agent_str or not id_agent_str.strip() or not id_formation_str:
                    continue

                try:
                    agent = Agent.objects.get(id_agent=int(float(id_agent_str)))
                    
                    Formation.objects.create(
                        id_formation=int(id_formation_str),
                        agent=agent,
                        annee=int(row['annee']) if row.get('annee') else None,
                        duree=row.get('duree'),
                    )
                    count += 1
                except Agent.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Agent ID {id_agent_str} non trouvé pour la formation. Ligne ignorée."))
                except (ValueError, TypeError) as e:
                     self.stdout.write(self.style.WARNING(f"  Ligne formation ignorée (données invalides: {e}): {row}"))
        self.stdout.write(self.style.SUCCESS(f"{count} formations importées."))
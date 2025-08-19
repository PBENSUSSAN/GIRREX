# Fichier : competences/management/commands/verifier_competences.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date

# On importe tous les modèles nécessaires de manière explicite
from core.models import Agent
from competences.models import (
    Licence, MentionUnite, SuiviFormationReglementaire, 
    MentionLinguistique, HistoriqueCompetence
)

class Command(BaseCommand):
    help = 'Vérifie les échéances de toutes les compétences et met à jour les statuts si nécessaire.'

    @transaction.atomic # Garantit que toutes les opérations pour un agent réussissent ou échouent ensemble
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"--- Début de la vérification des compétences ({timezone.now()}) ---"))
        today = timezone.now().date()
        
        # On ne vérifie que les licences actuellement considérées comme VALIDES
        licences_a_verifier = Licence.objects.select_related(
            'agent'
        ).prefetch_related(
            'agent__certificats_medicaux',
            'mentions_linguistiques', 
            'formations_suivies__formation'
        ).filter(statut=Licence.Statut.VALIDE)
        
        self.stdout.write(f"-> {licences_a_verifier.count()} licences actives à vérifier...")

        for licence in licences_a_verifier:
            agent = licence.agent
            inapte = False
            motifs = []

            # === VÉRIFICATION DES PRÉREQUIS FONDAMENTAUX (le "socle") ===

            # 1. Vérifier l'aptitude médicale
            certificat_medical = agent.certificats_medicaux.order_by('-date_visite').first()
            if not certificat_medical or not certificat_medical.date_expiration_aptitude or certificat_medical.date_expiration_aptitude < today:
                inapte = True
                motif = "Aptitude médicale expirée ou manquante."
                motifs.append(motif)
                
                # On crée l'historique seulement si ce n'est pas déjà fait pour cette raison
                HistoriqueCompetence.objects.get_or_create(
                    licence=licence, type_evenement=HistoriqueCompetence.TypeEvenement.APTITUDE_MEDICALE_EXPIREE,
                    defaults={'details': {'message': motif, 'date_echeance': str(getattr(certificat_medical, 'date_expiration_aptitude', 'N/A'))}}
                )
                self.stdout.write(self.style.WARNING(f"  - {agent.trigram}: {motif}"))

            # 2. Vérifier les formations réglementaires (ex: Facteurs Humains)
            for suivi in licence.formations_suivies.all():
                if suivi.date_echeance < today:
                    inapte = True
                    motif = f"Formation réglementaire '{suivi.formation.nom}' échue."
                    motifs.append(motif)
                    HistoriqueCompetence.objects.get_or_create(
                        licence=licence, type_evenement=HistoriqueCompetence.TypeEvenement.FORMATION_ECHOUE,
                        defaults={'details': {'message': motif, 'formation_suivi_id': suivi.id, 'date_echeance': str(suivi.date_echeance)}}
                    )
                    self.stdout.write(self.style.WARNING(f"  - {agent.trigram}: {motif}"))

            # 3. Vérifier les aptitudes linguistiques
            for ml in licence.mentions_linguistiques.all():
                if ml.date_echeance < today:
                    inapte = True
                    motif = f"Aptitude linguistique ({ml.get_langue_display()}) expirée."
                    motifs.append(motif)
                    HistoriqueCompetence.objects.get_or_create(
                        licence=licence, type_evenement=HistoriqueCompetence.TypeEvenement.APTITUDE_LINGUISTIQUE_EXPIREE,
                        defaults={'details': {'message': motif, 'mention_id': ml.id, 'date_echeance': str(ml.date_echeance)}}
                    )
                    self.stdout.write(self.style.WARNING(f"  - {agent.trigram}: {motif}"))

            # === MISE À JOUR DU STATUT DE LA LICENCE SI NÉCESSAIRE ===
            if inapte:
                licence.statut = Licence.Statut.INAPTE_TEMPORAIRE
                licence.motif_inaptitude = " / ".join(motifs)
                licence.date_debut_inaptitude = today
                licence.save()
                
                HistoriqueCompetence.objects.create(
                    licence=licence,
                    type_evenement=HistoriqueCompetence.TypeEvenement.STATUT_LICENCE_CHANGE,
                    details={'message': f"Licence passée au statut INAPTE TEMPORAIRE. Motifs: {licence.motif_inaptitude}"}
                )
                self.stdout.write(self.style.ERROR(f"  => Licence de {agent.trigram} déclarée INAPTE."))
                continue # On passe à la licence suivante, car si la licence est inapte, les mentions le sont aussi.

            # === VÉRIFICATION DES MENTIONS D'UNITÉ (uniquement si la licence est toujours valide) ===
            mentions_actives = MentionUnite.objects.filter(licence=licence, statut=MentionUnite.StatutMention.ACTIVE)
            for mention in mentions_actives:
                if mention.date_echeance < today:
                    mention.statut = MentionUnite.StatutMention.EXPIREE
                    mention.save()
                    HistoriqueCompetence.objects.create(
                        licence=licence,
                        type_evenement=HistoriqueCompetence.TypeEvenement.MENTION_EXPIREE,
                        details={
                            'message': f"La mention {mention.type_flux} ({mention.mention_particuliere}) de {agent.trigram} au centre {mention.centre.code_centre} a expiré.",
                            'mention_id': mention.id,
                            'date_echeance': str(mention.date_echeance)
                        }
                    )
                    self.stdout.write(self.style.WARNING(f"  - Mention expirée pour {agent.trigram} (ID: {mention.id})"))

        self.stdout.write(self.style.SUCCESS("--- Vérification des compétences terminée. ---"))
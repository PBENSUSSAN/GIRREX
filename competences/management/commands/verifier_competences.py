# Fichier : competences/management/commands/verifier_competences.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from competences.models import Licence, MentionUnite, SuiviFormationReglementaire, MentionLinguistique, HistoriqueCompetence

class Command(BaseCommand):
    help = 'Vérifie les échéances de toutes les compétences et met à jour les statuts si nécessaire.'

    @transaction.atomic # On englobe toute la logique dans une transaction pour garantir l'intégrité des données
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Début de la vérification nocturne des compétences ---"))
        today = timezone.now().date()
        
        licences_a_verifier = Licence.objects.select_related('agent', 'certificat_medical').prefetch_related(
            'mentions_linguistiques', 'formations_suivies'
        ).filter(statut=Licence.Statut.VALIDE)
        
        self.stdout.write(f"-> {licences_a_verifier.count()} licences actives à vérifier...")

        for licence in licences_a_verifier:
            agent_trigram = licence.agent.trigram
            inapte = False
            motifs = []

            # 1. Vérifier l'aptitude médicale
            if not licence.agent.certificat_medical or licence.agent.certificat_medical.validite < today:
                inapte = True
                motif = "Aptitude médicale expirée ou manquante."
                motifs.append(motif)
                HistoriqueCompetence.objects.get_or_create(
                    licence=licence, type_evenement=HistoriqueCompetence.TypeEvenement.APTITUDE_MEDICALE_EXPIREE,
                    defaults={'details': {'message': motif, 'date_echeance': str(licence.agent.certificat_medical.validite if licence.agent.certificat_medical else 'N/A')}}
                )
                self.stdout.write(self.style.WARNING(f"  - {agent_trigram}: {motif}"))

            # 2. Vérifier l'aptitude linguistique
            for ml in licence.mentions_linguistiques.all():
                if ml.date_echeance < today:
                    inapte = True
                    motif = f"Aptitude linguistique ({ml.langue}) expirée."
                    motifs.append(motif)
                    HistoriqueCompetence.objects.get_or_create(
                        licence=licence, type_evenement=HistoriqueCompetence.TypeEvenement.APTITUDE_LINGUISTIQUE_EXPIREE,
                        defaults={'details': {'message': motif, 'mention_id': ml.id, 'date_echeance': str(ml.date_echeance)}}
                    )
                    self.stdout.write(self.style.WARNING(f"  - {agent_trigram}: {motif}"))

            # 3. Vérifier les formations réglementaires
            for suivi in licence.formations_suivies.all():
                if suivi.date_echeance < today:
                    inapte = True # Une formation réglementaire échue rend inapte
                    motif = f"Formation réglementaire '{suivi.formation.nom}' échue."
                    motifs.append(motif)
                    HistoriqueCompetence.objects.get_or_create(
                        licence=licence, type_evenement=HistoriqueCompetence.TypeEvenement.FORMATION_ECHOUE,
                        defaults={'details': {'message': motif, 'formation_suivi_id': suivi.id, 'date_echeance': str(suivi.date_echeance)}}
                    )
                    self.stdout.write(self.style.WARNING(f"  - {agent_trigram}: {motif}"))
            
            # 4. Mettre à jour la licence si une inaptitude a été détectée
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
                self.stdout.write(self.style.ERROR(f"  => Licence de {agent_trigram} déclarée INAPTE TEMPORAIRE."))
                continue # On passe à la licence suivante, inutile de vérifier les mentions si la licence est inapte

            # 5. Vérifier les mentions d'unité (uniquement si la licence est apte)
            mentions_expirees = MentionUnite.objects.filter(licence=licence, statut=MentionUnite.StatutMention.ACTIVE, date_echeance__lt=today)
            for mention in mentions_expirees:
                mention.statut = MentionUnite.StatutMention.EXPIREE
                mention.save()
                HistoriqueCompetence.objects.create(
                    licence=licence,
                    type_evenement=HistoriqueCompetence.TypeEvenement.MENTION_EXPIREE,
                    details={'message': f"La mention {mention.type_flux} ({mention.mention_particuliere}) de {agent_trigram} a expiré.", 'mention_id': mention.id}
                )
                self.stdout.write(self.style.WARNING(f"  - Mention expirée pour {agent_trigram} (ID: {mention.id})"))

        self.stdout.write(self.style.SUCCESS("--- Vérification des compétences terminée. ---"))
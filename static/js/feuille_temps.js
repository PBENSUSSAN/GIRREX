// ==============================================================================
// Fichier : static/js/feuille_temps.js (VERSION FINALE AVEC RECAPITULATIF SIMPLE)
// ==============================================================================

class FeuilleTempsApp {
    constructor(config) {
        this.config = config;
        this.elements = {
            loader: document.getElementById('loader'),
            table: document.getElementById('feuille-temps-table'),
            tableBody: document.getElementById('feuille-temps-table').querySelector('tbody'),
            errorMessage: document.getElementById('error-message'),
            forceVerrouBtn: document.getElementById('force-verrou-btn'),
            reouvrirBtn: document.getElementById('reouvrir-btn'),
            confirmationModalEl: document.getElementById('confirmation-nuit-modal'),
            modalBtnCorriger: document.getElementById('modal-btn-corriger'),
            modalBtnConfirmerNuit: document.getElementById('modal-btn-confirmer-nuit'),
        };
        this.confirmationModal = this.elements.confirmationModalEl ? new bootstrap.Modal(this.elements.confirmationModalEl) : null;
        this.activeInputElement = null;
        this.data = [];
    }

    async init() {
        this.showLoader();
        await this.fetchData();
        this.hideLoader();
        this.renderTable();
        this.attachEventListeners();
    }

    showLoader() { if (this.elements.loader) this.elements.loader.style.display = 'block'; }
    hideLoader() { if (this.elements.loader) this.elements.loader.style.display = 'none'; }
    showError(message) { if (this.elements.errorMessage) { this.elements.errorMessage.textContent = message; this.elements.errorMessage.style.display = 'block'; } }

    async fetchData() {
        try {
            const response = await fetch(`/api/feuille-temps/${this.config.centreId}/${this.config.jourStr}/`);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `Erreur serveur ${response.status}` }));
                throw new Error(errorData.error || `Erreur ${response.status}`);
            }
            const jsonData = await response.json();
            this.data = jsonData.planning_du_jour;
            this.config.estCloturee = jsonData.est_cloturee;
        } catch (error) {
            console.error("Erreur de chargement:", error);
            this.showError(`Impossible de charger les données : ${error.message}`);
        }
    }

    renderTable() {
        this.elements.tableBody.innerHTML = '';
        if (!this.data || this.data.length === 0) {
            this.elements.tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Aucun agent planifié pour ce jour dans la dernière version validée du TDS.</td></tr>';
            this.elements.table.style.display = 'table';
            return;
        }

        const isPageEditable = this.config.canEdit && !this.config.estCloturee;

        this.data.forEach(agent => {
            const row = document.createElement('tr');
            row.dataset.agentId = agent.agent_id;
            const isRowEditable = isPageEditable && agent.categorie !== 'NON_TRAVAIL';
            row.innerHTML = `
                <td><strong>${agent.trigram}</strong></td>
                <td class="text-center">${agent.position_matin}</td>
                <td class="text-center">${agent.position_apres_midi}</td>
                <td><em>${agent.commentaire_tds || '-'}</em></td>
                <td><input type="time" class="form-control form-control-sm" data-field="heure_arrivee" value="${agent.heure_arrivee}" ${!isRowEditable ? 'disabled' : ''}></td>
                <td><input type="time" class="form-control form-control-sm" data-field="heure_depart" value="${agent.heure_depart}" ${!isRowEditable ? 'disabled' : ''}></td>
                <td class="text-center">
                    <span class="validation-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="">⚠️</span>
                </td>
            `;
            this.elements.tableBody.appendChild(row);
        });
        this.elements.table.style.display = 'table';
        
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    async handleFieldBlur(inputElement) {
        const row = inputElement.closest('tr');
        const arriveeInput = row.querySelector('[data-field="heure_arrivee"]');
        const departInput = row.querySelector('[data-field="heure_depart"]');

        if (inputElement.dataset.field === 'heure_depart' && arriveeInput.value && departInput.value && departInput.value < arriveeInput.value) {
            this.activeInputElement = inputElement;
            document.getElementById('modal-heure-arrivee').textContent = arriveeInput.value;
            document.getElementById('modal-heure-depart').textContent = departInput.value;
            this.confirmationModal.show();
        } else {
            await this.saveField(inputElement);
            if (arriveeInput.value && departInput.value) {
                await this.validateRow(row, false);
            } else {
                const icon = row.querySelector('.validation-icon');
                if (icon) icon.style.display = 'none';
            }
        }
    }

    async saveField(inputElement) {
        const row = inputElement.closest('tr');
        const agentId = row.dataset.agentId;
        inputElement.style.transition = 'background-color 0.3s ease';
        inputElement.style.backgroundColor = '#fff3cd';
        try {
            const response = await fetch('/api/feuille-temps/update/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.config.csrfToken },
                body: JSON.stringify({
                    agent_id: agentId, date_jour: this.config.jourStr,
                    champ: inputElement.dataset.field, valeur: inputElement.value
                })
            });
            if (!response.ok) throw new Error('La sauvegarde a échoué');
            inputElement.style.backgroundColor = '#d1e7dd';
        } catch (error) {
            console.error("Erreur de sauvegarde:", error);
            inputElement.style.backgroundColor = '#f8d7da';
        } finally {
            if (inputElement.style.backgroundColor !== 'rgb(248, 215, 218)') {
                setTimeout(() => { inputElement.style.backgroundColor = ''; }, 1500);
            }
        }
    }

    async validateRow(row, est_j_plus_1) {
        const agentId = row.dataset.agentId;
        const arriveeInput = row.querySelector('[data-field="heure_arrivee"]');
        const departInput = row.querySelector('[data-field="heure_depart"]');
        const icon = row.querySelector('.validation-icon');
        if (!arriveeInput.value || !departInput.value) {
            icon.style.display = 'none'; return;
        }
        try {
            const response = await fetch('/api/feuille-temps/valider-horaires/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.config.csrfToken },
                body: JSON.stringify({
                    agent_id: agentId, date_jour: this.config.jourStr,
                    heure_arrivee: arriveeInput.value, heure_depart: departInput.value,
                    est_j_plus_1: est_j_plus_1
                })
            });
            const data = await response.json();
            if (data.erreurs && data.erreurs.length > 0) {
                icon.style.display = 'inline';
                const tooltip = bootstrap.Tooltip.getInstance(icon);
                if (tooltip) tooltip.setContent({ '.tooltip-inner': data.erreurs.join('<br>') });
            } else {
                icon.style.display = 'none';
            }
        } catch (error) {
            console.error("Erreur de validation:", error);
        }
    }

    
      
    attachEventListeners() {
        if(this.config.canEdit && !this.config.estCloturee) {
            this.elements.tableBody.addEventListener('blur', (event) => {
                if (event.target.matches('input[type="time"]')) this.handleFieldBlur(event.target);
            }, true);
        }

        if (this.elements.confirmationModalEl) {
            this.elements.modalBtnCorriger.addEventListener('click', () => {
                this.confirmationModal.hide();
                this.activeInputElement.focus(); this.activeInputElement.select();
            });
            this.elements.modalBtnConfirmerNuit.addEventListener('click', async () => {
                const inputElement = this.activeInputElement;
                const row = inputElement.closest('tr');
                await this.saveField(inputElement);
                await this.validateRow(row, true);
                this.confirmationModal.hide();
            });
        }

        if (this.elements.forceVerrouBtn) {
            this.elements.forceVerrouBtn.addEventListener('click', async () => {
                if (confirm("Forcer la prise de main va déconnecter l'autre utilisateur. Êtes-vous sûr ?")) {
                    await fetch('/api/feuille-temps/verrou/forcer/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.config.csrfToken },
                        body: JSON.stringify({ centre_id: this.config.centreId })
                    });
                    location.reload();
                }
            });
        }

        
        if (this.elements.reouvrirBtn) {
            this.elements.reouvrirBtn.addEventListener('click', async () => {
                if (confirm("Êtes-vous sûr de vouloir rouvrir cette journée ? Les données seront à nouveau modifiables.")) {
                     await fetch('/api/feuille-temps/reouvrir/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.config.csrfToken },
                        body: JSON.stringify({ centre_id: this.config.centreId, date_jour: this.config.jourStr })
                    });
                    location.reload();
                }
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('feuille-temps-container');
    if (container) {
        const config = {
            centreId: container.dataset.centreId,
            jourStr: container.dataset.jourStr,
            canEdit: container.dataset.canEdit === 'true',
            estCloturee: container.dataset.estCloturee === 'true',
            canReouvrir: container.dataset.canReouvrir === 'true',
            csrfToken: document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : container.dataset.csrfToken
        };
        const app = new FeuilleTempsApp(config);
        app.init();
    }
});
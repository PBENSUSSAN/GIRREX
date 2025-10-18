// ==============================================================================
// Fichier : static/js/tour_de_service.js (VERSION INTÉGRALE ET FINALE CORRIGÉE)
// Inclut la logique pour : chargement async, couleurs, modale de commentaire,
// et modale de configuration des positions avec édition/suppression.
// ==============================================================================

class PlanningApp {
    constructor(config) {
        this.config = config;
        
        // ✅ NOUVEAU : Config arrêt à traiter
        const container = document.getElementById('planning-container');
        this.config.arretAgentId = container.dataset.arretAgentId || null;
        this.config.arretDateDebut = container.dataset.arretDateDebut || null;
        this.config.arretDateFin = container.dataset.arretDateFin || null;
        
        // 🐞 DEBUG : Afficher les données d'arrêt
        if (this.config.arretAgentId) {
            console.log('=== ARRÊT DÉTECTÉ ===')
            console.log('Agent ID:', this.config.arretAgentId);
            console.log('Date début:', this.config.arretDateDebut);
            console.log('Date fin:', this.config.arretDateFin);
        }
        
        this.elements = {
            grid: document.getElementById('planning-grid'),
            gridHead: document.getElementById('planning-grid-head'),
            gridBody: document.getElementById('planning-grid-body'),
            loader: document.getElementById('planning-loader'),
            commentModalEl: document.getElementById('comment-modal'),
            configModalEl: document.getElementById('config-positions-modal'),
            positionsListBody: document.getElementById('positions-list-body'),
            addPositionForm: document.getElementById('add-position-form'),
        };
        this.state = {
            isViewInverted: false,
            activeCell: null,
            agents: [],
            days: [],
            planningData: {},
            positions: [],
        };
        this.commentModal = this.elements.commentModalEl ? new bootstrap.Modal(this.elements.commentModalEl) : null;
    }

    async init() {
        this.showLoader();
        await this.fetchData();
        this.hideLoader();
        this.renderTable();
        this.attachEventListeners();
    }

    showLoader() { this.elements.loader.style.display = 'flex'; }
    hideLoader() { this.elements.loader.style.display = 'none'; }

    async fetchData() {
        try {
            const planningPromise = fetch(`/api/planning/${this.config.centreId}/${this.config.year}/${this.config.month}/`);
            const positionsPromise = fetch(`/api/centre/${this.config.centreId}/positions/`);
            
            const [planningResponse, positionsResponse] = await Promise.all([planningPromise, positionsPromise]);

            if (!planningResponse.ok) throw new Error(`Erreur planning: ${planningResponse.statusText}`);
            if (!positionsResponse.ok) throw new Error(`Erreur positions: ${positionsResponse.statusText}`);

            const planningJson = await planningResponse.json();
            this.state.agents = planningJson.agents;
            this.state.days = planningJson.days;
            this.state.planningData = planningJson.planning_data;
            this.state.positions = await positionsResponse.json();

        } catch (error) {
            console.error("Erreur lors de la récupération des données:", error);
            this.elements.grid.innerHTML = `<div class="alert alert-danger">Impossible de charger les données du planning. Veuillez réessayer.</div>`;
        }
    }

    createCell(agent, day) {
        const tour = this.state.planningData[agent.id_agent]?.[day.date_iso] || {};
        const cell = document.createElement('td');
        cell.className = `planning-cell ${day.weekday >= 5 ? 'weekend' : ''} ${this.config.canEdit ? 'editable' : ''}`;
        cell.dataset.agentId = agent.id_agent;
        cell.dataset.date = day.date_iso;
        cell.dataset.positionMatinId = tour.position_matin_id || '';
        cell.dataset.positionApremId = tour.position_apres_midi_id || '';
        cell.dataset.comment = tour.commentaire || '';
        cell.title = tour.commentaire || '';

        // ✅ NOUVEAU : Surligner si c'est un jour d'arrêt à traiter
        if (this.config.arretAgentId && this.config.arretAgentId == agent.id_agent) {
            const cellDate = new Date(day.date_iso + 'T00:00:00');  // 🐞 FIX : Forcer l'heure à 00:00
            const debutArret = new Date(this.config.arretDateDebut + 'T00:00:00');
            const finArret = new Date(this.config.arretDateFin + 'T00:00:00');
            
            // 🐞 DEBUG : Logger les comparaisons
            console.log('Test cellule:', day.date_iso, 'pour agent', agent.id_agent);
            console.log('  cellDate:', cellDate);
            console.log('  debutArret:', debutArret);
            console.log('  finArret:', finArret);
            console.log('  Dans la plage?', cellDate >= debutArret && cellDate <= finArret);
            
            if (cellDate >= debutArret && cellDate <= finArret) {
                console.log('✅ SURLIGNAGE APPLIQUÉ pour', day.date_iso);
                cell.classList.add('arret-a-traiter');
                cell.style.border = '3px solid #e74c3c';
                cell.style.boxShadow = '0 0 10px rgba(231, 76, 60, 0.8)';
                cell.style.animation = 'pulse 2s infinite';
            }
        }

        if (tour.position_matin_id) {
            const position = this.state.positions.find(p => p.id == tour.position_matin_id);
            if (position && position.couleur && position.couleur !== '#ffffff') {
                cell.style.backgroundColor = position.couleur;
            }
        }

        cell.innerHTML = `
            <span class="view-mode ${tour.commentaire ? 'has-comment' : ''}">
                <span class="morning">${tour.position_matin_nom || ""}</span>
                <span class="afternoon" style="display:none;">${tour.position_apres_midi_nom || ""}</span>
            </span>
            <span class="edit-mode" style="display:none;"></span>`;
        return cell;
    }

    renderTable() {
        this.elements.gridHead.innerHTML = '';
        this.elements.gridBody.innerHTML = '';
        const headerRow = document.createElement('tr');
        if (!this.state.isViewInverted) {
            headerRow.innerHTML = `<th class="agent-col">Agent</th>` + this.state.days.map(d => `<th class="day-col ${d.weekday >= 5 ? 'weekend' : ''}">${d.jour_court}<br>${d.num}</th>`).join('');
            this.elements.gridHead.appendChild(headerRow);
            this.state.agents.forEach(agent => {
                const bodyRow = document.createElement('tr');
                bodyRow.innerHTML = `<td class="agent-col">${agent.trigram || agent.reference}</td>`;
                this.state.days.forEach(day => { bodyRow.appendChild(this.createCell(agent, day)); });
                this.elements.gridBody.appendChild(bodyRow);
            });
        } else {
            headerRow.innerHTML = `<th class="agent-col">Date</th>` + this.state.agents.map(a => `<th class="day-col">${a.trigram || a.reference}</th>`).join('');
            this.elements.gridHead.appendChild(headerRow);
            this.state.days.forEach(day => {
                const bodyRow = document.createElement('tr');
                bodyRow.className = `${day.weekday >= 5 ? 'weekend' : ''}`;
                bodyRow.innerHTML = `<td class="agent-col date-col">${day.jour_court} ${day.num}</td>`;
                this.state.agents.forEach(agent => { bodyRow.appendChild(this.createCell(agent, day)); });
                this.elements.gridBody.appendChild(bodyRow);
            });
        }
    }

    switchToEditMode(cell) {
        if (!this.config.canEdit || cell === this.state.activeCell) return;
        if (this.state.activeCell) this.switchToViewMode(this.state.activeCell);
        this.state.activeCell = cell;
        const viewMode = cell.querySelector('.view-mode');
        const editMode = cell.querySelector('.edit-mode');
        const matinId = cell.dataset.positionMatinId;
        const apremId = cell.dataset.positionApremId || matinId;
        const createSelect = (id, selectedValue) => {
            let options = '<option value="">---</option>';
            this.state.positions.forEach(p => { options += `<option value="${p.id}" ${p.id == selectedValue ? 'selected' : ''}>${p.nom}</option>`; });
            return `<select id="${id}" class="form-control-sm">${options}</select>`;
        };
        editMode.innerHTML = `<div>${createSelect('edit-matin', matinId)}</div><div>${createSelect('edit-aprem', apremId)}</div>`;
        viewMode.style.display = 'none';
        editMode.style.display = 'block';
        editMode.querySelector('#edit-matin').focus();
        editMode.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', () => this.saveCell(cell));
        });
    }

    switchToViewMode(cell) {
        if (!cell) return;
        const viewMode = cell.querySelector('.view-mode');
        const editMode = cell.querySelector('.edit-mode');
        editMode.innerHTML = '';
        viewMode.style.display = 'block';
        editMode.style.display = 'none';
        if (cell === this.state.activeCell) this.state.activeCell = null;
    }

    async saveCell(cell) {
        const matinSelect = cell.querySelector('#edit-matin');
        const apremSelect = cell.querySelector('#edit-aprem');
        if (apremSelect.value === '' && matinSelect.value !== '') apremSelect.value = matinSelect.value;
        cell.dataset.positionMatinId = matinSelect.value;
        cell.dataset.positionApremId = apremSelect.value;
        const matinPos = this.state.positions.find(p => p.id == matinSelect.value);
        cell.querySelector('.morning').textContent = matinPos ? matinPos.nom : '';
        cell.querySelector('.afternoon').textContent = apremSelect.options[apremSelect.selectedIndex].text.replace('---','');
        cell.style.backgroundColor = '#ffc107'; // Jaune: en cours
        try {
            const response = await fetch("/ajax/update-tour/", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.config.csrfToken },
                body: JSON.stringify({
                    agent_id: cell.dataset.agentId, date: cell.dataset.date,
                    position_matin_id: cell.dataset.positionMatinId || null,
                    position_apres_midi_id: cell.dataset.positionApremId || null,
                })
            });
            if (!response.ok) throw new Error('Sauvegarde échouée');
            cell.style.backgroundColor = matinPos && matinPos.couleur !== '#ffffff' ? matinPos.couleur : ''; // Applique la couleur après sauvegarde
            setTimeout(() => { if (!matinPos || matinPos.couleur === '#ffffff') cell.style.backgroundColor = ''; }, 200); // Flash vert puis retour couleur
        } catch (error) {
            console.error('Erreur sauvegarde cellule:', error);
            cell.style.backgroundColor = '#f8d7da'; // Rouge: erreur
        }
    }

    async saveComment(agentId, date, commentText) {
        const cell = this.elements.grid.querySelector(`[data-agent-id='${agentId}'][data-date='${date}']`);
        if(!cell) return;
        try {
            const response = await fetch("/ajax/update-comment/", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.config.csrfToken },
                body: JSON.stringify({ agent_id: agentId, date: date, commentaire: commentText })
            });
            const data = await response.json();
            cell.dataset.comment = commentText;
            cell.title = commentText;
            cell.querySelector('.view-mode').classList.toggle('has-comment', data.comment_exists);
            if(this.commentModal) this.commentModal.hide();
        } catch (error) { console.error('Erreur sauvegarde commentaire:', error); }
    }

    renderPositionsModal() {
        const positionsData = this.state.positions;
        this.elements.positionsListBody.innerHTML = '';
        const categorieChoices = {'CONTROLE': 'Contrôle', 'AUTRES': 'Autres', 'ABSENT': 'Absent'};
        if (positionsData.length === 0) {
            this.elements.positionsListBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Aucune position configurée.</td></tr>`;
            return;
        }
        positionsData.forEach(pos => {
            const row = document.createElement('tr');
            row.dataset.posId = pos.id;
            const categorieDisplay = categorieChoices[pos.categorie] || pos.categorie;
            row.innerHTML = `
                <td data-field="nom">${pos.nom}</td>
                <td data-field="description">${pos.description || ''}</td>
                <td data-field="categorie" data-value="${pos.categorie}">${categorieDisplay}</td>
                <td data-field="couleur"><div style="width: 20px; height: 20px; background-color: ${pos.couleur}; border: 1px solid #ccc; margin: auto;"></div></td>
                <td>
                    <button class="btn btn-sm btn-primary btn-edit-pos" title="Modifier"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-danger btn-delete-pos" title="Supprimer"><i class="bi bi-trash"></i></button>
                </td>
            `;
            this.elements.positionsListBody.appendChild(row);
        });
    }

    editPosition(button) {
        const row = button.closest('tr');
        if (row.classList.contains('editing')) return;
        row.classList.add('editing');
        const nomCell = row.querySelector('[data-field="nom"]');
        const descCell = row.querySelector('[data-field="description"]');
        const catCell = row.querySelector('[data-field="categorie"]');
        const colorCell = row.querySelector('[data-field="couleur"]');
        const nomValue = nomCell.textContent;
        const descValue = descCell.textContent;
        const catValue = catCell.dataset.value;
        const posId = row.dataset.posId;
        const currentColor = this.state.positions.find(p => p.id == posId)?.couleur || '#FFFFFF';
        nomCell.innerHTML = `<input type="text" class="form-control form-control-sm" value="${nomValue}">`;
        descCell.innerHTML = `<input type="text" class="form-control form-control-sm" value="${descValue}">`;
        catCell.innerHTML = `<select class="form-select form-select-sm"><option value="CONTROLE" ${catValue === 'CONTROLE' ? 'selected' : ''}>Contrôle</option><option value="AUTRES" ${catValue === 'AUTRES' ? 'selected' : ''}>Autres</option><option value="ABSENT" ${catValue === 'ABSENT' ? 'selected' : ''}>Absent</option></select>`;
        colorCell.innerHTML = `<input type="color" class="form-control form-control-color form-control-sm" value="${currentColor}">`;
        button.innerHTML = '<i class="bi bi-check-lg"></i>';
        button.classList.replace('btn-primary', 'btn-success');
        button.title = "Enregistrer";
    }

    async savePosition(button) {
        const row = button.closest('tr');
        const positionId = row.dataset.posId;
        const nom = row.querySelector('[data-field="nom"] input').value;
        const description = row.querySelector('[data-field="description"] input').value;
        const categorie = row.querySelector('[data-field="categorie"] select').value;
        const couleur = row.querySelector('[data-field="couleur"] input').value;
        await fetch(`/api/position/${positionId}/update/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.config.csrfToken },
            body: JSON.stringify({ nom, description, categorie, couleur })
        });
        await this.fetchData(); 
        this.renderPositionsModal();
    }

    async deletePosition(button) {
        const row = button.closest('tr');
        const positionId = row.dataset.posId;
        const positionNom = row.querySelector('[data-field="nom"]').textContent;
        if (confirm(`Êtes-vous sûr de vouloir supprimer la position "${positionNom}" ?`)) {
            await fetch(`/api/position/${positionId}/delete/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': this.config.csrfToken }
            });
            await this.fetchData();
            this.renderPositionsModal();
        }
    }

    attachEventListeners() {
        document.addEventListener('click', e => { if (this.state.activeCell && !this.state.activeCell.contains(e.target)) { this.switchToViewMode(this.state.activeCell); } }, true);
        this.elements.grid.addEventListener('click', e => { const cell = e.target.closest('.planning-cell.editable'); if (cell) { e.stopPropagation(); this.switchToEditMode(cell); } });
        this.elements.grid.addEventListener('contextmenu', e => {
            e.preventDefault();
            const cell = e.target.closest('.planning-cell.editable');
            if (!cell || !this.commentModal) return;
            const agent = this.state.agents.find(a => a.id_agent == cell.dataset.agentId);
            const identifier = agent ? (agent.trigram || agent.reference) : 'N/A';
            this.elements.commentModalEl.querySelector('#comment-agent-id').value = cell.dataset.agentId;
            this.elements.commentModalEl.querySelector('#comment-date').value = cell.dataset.date;
            this.elements.commentModalEl.querySelector('#comment-textarea').value = cell.dataset.comment;
            this.elements.commentModalEl.querySelector('#comment-modal-title').textContent = `${identifier} - ${cell.dataset.date}`;
            this.commentModal.show();
        });
        if (this.elements.commentModalEl) {
            const saveBtn = this.elements.commentModalEl.querySelector('#save-comment-btn');
            const deleteBtn = this.elements.commentModalEl.querySelector('#delete-comment-btn');
            const getIdsFromModal = () => ({agentId: this.elements.commentModalEl.querySelector('#comment-agent-id').value, date: this.elements.commentModalEl.querySelector('#comment-date').value});
            saveBtn.addEventListener('click', () => { const { agentId, date } = getIdsFromModal(); const comment = this.elements.commentModalEl.querySelector('#comment-textarea').value; this.saveComment(agentId, date, comment); });
            deleteBtn.addEventListener('click', () => { const { agentId, date } = getIdsFromModal(); this.saveComment(agentId, date, ''); });
        }
        if (this.elements.configModalEl) {
            this.elements.configModalEl.addEventListener('show.bs.modal', () => { this.renderPositionsModal(); });
            this.elements.configModalEl.addEventListener('hidden.bs.modal', () => { location.reload(); });
            this.elements.addPositionForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const nomInput = document.getElementById('new-pos-nom'), descInput = document.getElementById('new-pos-desc'), catInput = document.getElementById('new-pos-cat'), colorInput = document.getElementById('new-pos-color');
                if (!nomInput.value || !catInput.value) { alert('Le nom et la catégorie sont obligatoires.'); return; }
                await fetch(`/api/centre/${this.config.centreId}/positions/add/`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.config.csrfToken },
                    body: JSON.stringify({ nom: nomInput.value, description: descInput.value, categorie: catInput.value, couleur: colorInput.value })
                });
                this.elements.addPositionForm.reset();
                await this.fetchData();
                this.renderPositionsModal();
            });
            this.elements.positionsListBody.addEventListener('click', (e) => {
                const editButton = e.target.closest('.btn-edit-pos'), deleteButton = e.target.closest('.btn-delete-pos');
                if (editButton) { if (editButton.classList.contains('btn-success')) { this.savePosition(editButton); } else { this.editPosition(editButton); } }
                if (deleteButton) { this.deletePosition(deleteButton); }
            });
        }
        document.getElementById('invert-view-btn').addEventListener('click', () => { this.state.isViewInverted = !this.state.isViewInverted; this.renderTable(); });
        document.getElementById('toggle-detailed-view').addEventListener('click', () => this.elements.grid.classList.toggle('detailed-view'));
        document.getElementById('toggle-weekends').addEventListener('click', () => document.body.classList.toggle('hide-weekends'));
        document.getElementById('print-btn').addEventListener('click', () => window.print());
        const validateBtn = document.getElementById('validate-planning-btn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => {
                if (confirm("Êtes-vous sûr de vouloir valider la version actuelle de ce planning ?")) {
                    fetch(`/planning/centre/${this.config.centreId}/${this.config.year}/${this.config.month}/valider/`, {
                        method: 'POST', headers: { 'X-CSRFToken': this.config.csrfToken }
                    }).then(res => res.json()).then(data => alert(data.message || "Erreur.")).catch(() => alert("Erreur critique."));
                }
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const planningContainer = document.getElementById('planning-container');
    if (planningContainer) {
        const config = {
            centreId: planningContainer.dataset.centreId,
            year: planningContainer.dataset.year,
            month: planningContainer.dataset.month,
            canEdit: planningContainer.dataset.canEdit === 'True',
            csrfToken: planningContainer.dataset.csrfToken,
        };
        const app = new PlanningApp(config);
        app.init();
    }
});
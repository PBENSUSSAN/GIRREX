// Fichier : static/js/gestion_zone.js (VERSION FINALE ET ROBUSTE)

document.addEventListener('DOMContentLoaded', function() {
    const editModalEl = document.getElementById('editZonesModal');
    if (!editModalEl) return;

    const container = document.querySelector('[data-centre-id]');
    const CENTRE_ID = container.dataset.centreId;
    const CSRF_TOKEN = container.dataset.csrfToken;

    const modalTbody = document.getElementById('modal-zones-tbody');
    const addForm = document.getElementById('add-zone-form');

    // --- Fonctions ---

    async function fetchAndRenderZones() {
        modalTbody.innerHTML = '<tr><td colspan="3" class="text-center"><div class="spinner-border spinner-border-sm"></div></td></tr>';
        try {
            const response = await fetch(`/api/zones/list/${CENTRE_ID}/`);
            if (!response.ok) throw new Error('Erreur réseau');
            
            const zones = await response.json();
            
            modalTbody.innerHTML = '';
            if (zones.length === 0) {
                modalTbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Aucune zone configurée.</td></tr>';
            } else {
                zones.forEach(zone => {
                    const row = modalTbody.insertRow();
                    row.dataset.zoneId = zone.id;
                    row.innerHTML = `
                        <td data-field="nom">${escapeHTML(zone.nom)}</td>
                        <td data-field="description">${escapeHTML(zone.description || '')}</td>
                        <td class="text-center">
                            <button class="btn btn-primary btn-sm btn-edit-zone" title="Modifier"><i class="bi bi-pencil-fill"></i></button>
                            <button class="btn btn-danger btn-sm btn-delete-zone" title="Supprimer"><i class="bi bi-trash-fill"></i></button>
                        </td>
                    `;
                });
            }
        } catch (error) {
            modalTbody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Erreur de chargement.</td></tr>';
            console.error(error);
        }
    }

    function escapeHTML(str) {
        return str.replace(/[&<>"']/g, function(match) {
            return { '&': '&amp;', '<': '&lt', '>': '&gt', '"': '&quot', "'": '&#39' }[match];
        });
    }

    // --- Écouteurs d'événements ---

    editModalEl.addEventListener('show.bs.modal', fetchAndRenderZones);

    addForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const nomInput = document.getElementById('zone-nom-input');
        const descInput = document.getElementById('zone-desc-input');
        const data = {
            nom: nomInput.value.trim(),
            description: descInput.value.trim()
        };
        if (!data.nom) { alert('Le nom est obligatoire.'); return; }

        try {
            const response = await fetch(`/api/zones/add/${CENTRE_ID}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (response.ok) {
                window.location.reload();
            } else {
                alert(`Erreur : ${result.message}`);
            }
        } catch (error) {
            alert('Une erreur réseau est survenue lors de l\'ajout.');
        }
    });

    modalTbody.addEventListener('click', async function(event) {
        const button = event.target.closest('button');
        if (!button) return;

        const row = button.closest('tr');
        const zoneId = row.dataset.zoneId;

        // Clic sur le bouton "Supprimer"
        if (button.classList.contains('btn-delete-zone')) {
            const nom = row.querySelector('[data-field="nom"]').textContent;
            if (confirm(`Êtes-vous sûr de vouloir supprimer la zone "${nom}" ?`)) {
                try {
                    const response = await fetch(`/api/zones/delete/${zoneId}/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': CSRF_TOKEN }
                    });
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        const result = await response.json();
                        alert(`Erreur : ${result.message}`);
                    }
                } catch (error) {
                    alert('Une erreur réseau est survenue lors de la suppression.');
                }
            }
        }
        
        // Clic sur le bouton "Modifier" / "Enregistrer"
        if (button.classList.contains('btn-edit-zone')) {
            // Si on est déjà en mode édition, on sauvegarde
            if (row.classList.contains('editing')) {
                const nomInput = row.querySelector('input[data-field="nom"]');
                const descInput = row.querySelector('input[data-field="description"]');
                const data = {
                    nom: nomInput.value.trim(),
                    description: descInput.value.trim()
                };
                if (!data.nom) { alert('Le nom est obligatoire.'); return; }

                try {
                    const response = await fetch(`/api/zones/update/${zoneId}/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                        body: JSON.stringify(data)
                    });
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        const result = await response.json();
                        alert(`Erreur : ${result.message}`);
                    }
                } catch (error) {
                    alert('Une erreur réseau est survenue lors de la sauvegarde.');
                }

            } else { // Sinon, on passe en mode édition
                // Annuler les autres lignes en édition
                const currentlyEditing = modalTbody.querySelector('tr.editing');
                if (currentlyEditing) {
                    fetchAndRenderZones(); // Recharge et annule tout
                    return; // On attend que l'utilisateur reclique
                }

                row.classList.add('editing');
                const nomCell = row.querySelector('td[data-field="nom"]');
                const descCell = row.querySelector('td[data-field="description"]');
                const nom = nomCell.textContent;
                const desc = descCell.textContent;

                nomCell.innerHTML = `<input type="text" class="form-control form-control-sm" data-field="nom" value="${nom}">`;
                descCell.innerHTML = `<input type="text" class="form-control form-control-sm" data-field="description" value="${desc}">`;

                button.classList.replace('btn-primary', 'btn-success');
                button.innerHTML = '<i class="bi bi-check-lg"></i>';
            }
        }
    });
});
// Fichier : static/js/girrex_app.js (NOUVEAU FICHIER)

document.addEventListener('DOMContentLoaded', function() {
    
    // ===================================================================================
    // == DEBUT : BLOC JAVASCRIPT POUR LA GESTION DU SERVICE JOURNALIER                 ==
    // ===================================================================================

    // On récupère les données préparées par Django dans les attributs data-* du body
    const body = document.body;
    const csrfToken = body.dataset.csrfToken;
    const apiServiceUrl = body.dataset.apiServiceUrl;
    const centreId = body.dataset.centreAgentId;
    const todayStr = body.dataset.todayStr;

    // Fonction générique pour appeler l'API de gestion
    async function callServiceAPI(action, details = '') {
        // On s'assure que l'URL a bien été passée par le template
        if (!apiServiceUrl) {
            console.error("URL de l'API de service non trouvée. Vérifiez l'attribut data-api-service-url sur le tag <body>.");
            alert("Erreur de configuration de l'application.");
            return;
        }

        try {
            const response = await fetch(apiServiceUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ action: action, details: details })
            });
            const data = await response.json();
            if (response.ok) {
                // Recharger la page pour voir les changements partout (sidebar, contenu, etc.)
                window.location.reload();
            } else {
                alert(`Erreur: ${data.message || 'Une erreur inconnue est survenue.'}`);
            }
        } catch (error) {
            console.error("Erreur lors de l'appel API:", error);
            alert('Erreur de communication avec le serveur.');
        }
    }

    // --- Gestion de l'ouverture ---
    const openServiceBtn = document.getElementById('open-service-btn');
    if (openServiceBtn) {
        const openModal = new bootstrap.Modal(document.getElementById('open-service-modal'));
        openServiceBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openModal.show();
        });
        document.getElementById('confirm-open-service-btn').addEventListener('click', () => {
            callServiceAPI('ouvrir');
        });
    }

    // --- Gestion de la clôture ---
    const closeServiceBtn = document.getElementById('close-service-btn');
    if (closeServiceBtn) {
        const closeModal = new bootstrap.Modal(document.getElementById('close-service-modal'));
        const recapLoader = document.getElementById('recap-cloture-loader');
        const recapBody = document.getElementById('recap-cloture-table-body');
        
        closeServiceBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            closeModal.show();
            recapLoader.style.display = 'block';
            recapBody.innerHTML = ''; // Vider l'ancien contenu

            // On construit l'URL de l'API des données de la feuille de temps
            const dataUrl = `/api/feuille-temps/${centreId}/${todayStr}/`;
            
            try {
                const response = await fetch(dataUrl);
                const data = await response.json();
                
                if (data.planning_du_jour && data.planning_du_jour.length > 0) {
                    data.planning_du_jour.forEach(agent => {
                        const row = `<tr>
                            <td>${agent.trigram}</td>
                            <td>${agent.heure_arrivee || 'N/A'} - ${agent.heure_depart || 'N/A'}</td>
                        </tr>`;
                        recapBody.innerHTML += row;
                    });
                } else {
                    recapBody.innerHTML = '<tr><td colspan="2" class="text-muted">Aucun pointage trouvé pour aujourd\'hui.</td></tr>';
                }
            } catch (error) {
                console.error("Erreur lors de la récupération du récapitulatif:", error);
                recapBody.innerHTML = '<tr><td colspan="2" class="text-danger">Impossible de charger le récapitulatif.</td></tr>';
            } finally {
                recapLoader.style.display = 'none';
            }
        });
        document.getElementById('confirm-close-service-btn').addEventListener('click', () => {
            callServiceAPI('cloturer');
        });
    }
    
    // --- Gestion de la réouverture ---
    const reopenServiceBtn = document.getElementById('reopen-service-btn');
    if (reopenServiceBtn) {
        const reopenModal = new bootstrap.Modal(document.getElementById('reopen-service-modal'));
        reopenServiceBtn.addEventListener('click', (e) => {
            e.preventDefault();
            reopenModal.show();
        });
        document.getElementById('confirm-reopen-service-btn').addEventListener('click', () => {
            const details = document.getElementById('reopen-details').value;
            callServiceAPI('reouvrir', details);
        });
    }
    
    // --- Gestion de la déconnexion (peut rester ici ou être dans son propre fichier) ---
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault();
            const logoutForm = document.getElementById('logout-form');
            if (logoutForm) {
                logoutForm.submit();
            }
        });
    }
});
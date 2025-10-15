// Fichier : static/js/timeline-cca.js

document.addEventListener('DOMContentLoaded', function() {
    
    // On cible le conteneur HTML où la timeline sera dessinée
    const timelineEl = document.getElementById('timeline-container');
    if (!timelineEl) {
        // Si on n'est pas sur la bonne page, on ne fait rien.
        return; 
    }

    // On récupère la date cible passée par le template Django via un attribut data-*
    const targetDate = timelineEl.dataset.targetDate;
    const dataUrl = `/activites/api/cca/planning-data/${targetDate}/`;

    // --- Configuration de la Timeline ---
    const options = {
        // Configuration de l'axe du temps
        start: `${targetDate}T06:00:00`, // La timeline démarre à 6h du matin
        end: `${targetDate}T20:00:00`,   // et se termine à 20h
        min: `${targetDate}T00:00:00`,     // Limite de dézoom minuit
        max: `${targetDate}T23:59:59`,     // Limite de dézoom 23h59
        
        // Configuration de l'affichage
        stack: false,           // Permet aux événements de se superposer (important pour les conflits visuels)
        orientation: 'top',     // La barre de temps est en haut
        
        // Configuration des interactions
        editable: {
            add: true,         // Autoriser l'ajout de nouveaux items par double-clic
            updateTime: true,  // Autoriser le drag & drop en temps
            updateGroup: true, // Autoriser le déplacement d'un item vers une autre cabine
            remove: true,      // Autoriser la suppression (avec la touche Suppr)
        },

        // On peut définir un template pour personnaliser l'apparence des items (blocs)
        // Pour l'instant, on garde le défaut qui est déjà très bien.
    };

    // --- Chargement des Données et Création de la Timeline ---
    console.log("Timeline: Tentative de chargement des données depuis", dataUrl);

    fetch(dataUrl)
        .then(response => {
            if (!response.ok) {
                // Si le serveur répond avec une erreur (4xx, 5xx), on la capture
                throw new Error(`Erreur réseau ou serveur : ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Timeline: Données reçues du serveur :", data); // Affiche les données dans la console pour déboguer

            // On vérifie que les données reçues sont correctes
            if (!data.groups || !data.items) {
                console.error("Timeline: Le format des données est incorrect. Les clés 'groups' ou 'items' sont manquantes.");
                return;
            }

            // On crée les "groupes" (les lignes de nos cabines)
            const groups = new vis.DataSet(data.groups);

            // On crée les "items" (les blocs de vol et d'indisponibilité)
            const items = new vis.DataSet(data.items);
            
            console.log("Timeline: Initialisation de la timeline avec les groupes et les items.");
            
            // On crée l'instance de la timeline et on la dessine
            const timeline = new vis.Timeline(timelineEl, items, groups, options);

            // Peupler le panneau des demandes non planifiées (logique à venir)
            // ...
        })
        .catch(error => {
            console.error('Timeline: Erreur fatale lors de l\'initialisation :', error);
            timelineEl.innerHTML = `<div class="alert alert-danger">Impossible de charger les données de la timeline. Vérifiez la console (F12) et le terminal Django pour plus de détails.</div>`;
        });
});
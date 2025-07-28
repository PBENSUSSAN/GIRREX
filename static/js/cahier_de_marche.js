/**
 * Fichier : static/js/cahier_de_marche.js
 * Auteur : Gemini pour GIRREX
 * Description : Gère l'interactivité de la page du Cahier de Marche,
 * notamment la logique de résolution des pannes.
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Fonction utilitaire pour récupérer le token CSRF depuis les cookies de la page.
    // C'est la méthode recommandée par Django pour les requêtes AJAX.
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Le cookie ressemble-t-il à ce que nous voulons ?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // On sélectionne tous les boutons qui ont la classe "resolve-panne-btn"
    const resolveButtons = document.querySelectorAll('.resolve-panne-btn');

    // Pour chaque bouton trouvé, on attache un gestionnaire d'événement "click"
    resolveButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault(); // Empêche le comportement par défaut du bouton

            // Demande de confirmation à l'utilisateur
            if (!confirm("Êtes-vous sûr de vouloir marquer cette panne comme résolue ?")) {
                return; // Si l'utilisateur annule, on arrête tout
            }

            // On récupère les informations stockées dans les attributs data-* du bouton
            const url = this.dataset.url;

            // On désactive le bouton et on affiche un spinner pour le retour visuel
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Résolution...';
            
            // On exécute l'appel API avec fetch
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken, // Le token est crucial pour la sécurité
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                // Si la réponse HTTP n'est pas un succès (ex: 403, 404, 500), on lève une erreur
                if (!response.ok) {
                    throw new Error(`Erreur HTTP ${response.status}`);
                }
                return response.json(); // On convertit la réponse en JSON
            })
            .then(data => {
                // Si notre application renvoie un statut "ok"
                if (data.status === 'ok') {
                    alert(data.message); // On affiche le message de succès
                    window.location.reload(); // On recharge la page pour voir les changements
                } else {
                    // Si l'application renvoie une erreur métier
                    throw new Error(data.message || 'Erreur inconnue renvoyée par le serveur.');
                }
            })
            .catch(error => {
                // En cas d'erreur (réseau ou autre), on affiche un message et on réactive le bouton
                console.error('Erreur lors de la résolution de la panne:', error);
                alert('Une erreur est survenue. Veuillez vérifier la console et réessayer.');
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-check-circle me-1"></i>Résoudre';
            });
        });
    });
});
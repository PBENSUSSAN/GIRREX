// Fichier : static/js/suivi_tables.js

document.addEventListener('DOMContentLoaded', function () {
    // On sélectionne tous les boutons qui servent à déplier/replier
    const toggles = document.querySelectorAll('.toggle-subtasks');

    toggles.forEach(function(toggle) {
        // Pour chaque bouton, on ajoute un écouteur d'événement au clic
        toggle.addEventListener('click', function() {
            // On vérifie quelle icône est actuellement affichée
            if (this.classList.contains('bi-plus-square-fill')) {
                // Si c'est le "+", on le remplace par le "-"
                this.classList.remove('bi-plus-square-fill');
                this.classList.add('bi-dash-square-fill');
            } else {
                // Sinon (si c'est le "-"), on le remplace par le "+"
                this.classList.remove('bi-dash-square-fill');
                this.classList.add('bi-plus-square-fill');
            }
        });
    });
});
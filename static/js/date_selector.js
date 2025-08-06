// Fichier : static/js/date_selector.js
document.addEventListener('DOMContentLoaded', function() {
    const dateSelector = document.getElementById('date-selector');
    if (dateSelector) {
        // On récupère l'URL de base depuis l'attribut data-*
        const baseUrl = dateSelector.dataset.baseUrl;

        dateSelector.addEventListener('change', function() {
            const newDate = this.value;
            if (newDate && baseUrl) {
                // On remplace le placeholder par la nouvelle date
                const finalUrl = baseUrl.replace('__DATE__', newDate);
                window.location.href = finalUrl;
            }
        });
    }
});
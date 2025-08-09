// Fichier : static/js/clocks.js

document.addEventListener('DOMContentLoaded', function() {
    const localTimeEl = document.getElementById('local-time-display');
    const zuluTimeEl = document.getElementById('zulu-time-display');

    // S'assure que les éléments existent avant de lancer l'horloge
    if (!localTimeEl || !zuluTimeEl) {
        return;
    }

    // Fonction pour ajouter un zéro devant les nombres < 10 (ex: 7 -> "07")
    function formatTimeUnit(unit) {
        return unit.toString().padStart(2, '0');
    }

    function updateClocks() {
        const now = new Date();

        // Mise à jour de l'heure locale
        const localHours = formatTimeUnit(now.getHours());
        const localMinutes = formatTimeUnit(now.getMinutes());
        const localSeconds = formatTimeUnit(now.getSeconds());
        localTimeEl.textContent = `${localHours}:${localMinutes}:${localSeconds}`;

        // Mise à jour de l'heure Zulu (UTC)
        const zuluHours = formatTimeUnit(now.getUTCHours());
        const zuluMinutes = formatTimeUnit(now.getUTCMinutes());
        const zuluSeconds = formatTimeUnit(now.getUTCSeconds());
        zuluTimeEl.textContent = `${zuluHours}:${zuluMinutes}:${zuluSeconds}`;
    }

    // Met à jour les horloges toutes les secondes (1000 millisecondes)
    setInterval(updateClocks, 1000);

    // Lance la fonction une première fois immédiatement sans attendre la première seconde
    updateClocks();
});
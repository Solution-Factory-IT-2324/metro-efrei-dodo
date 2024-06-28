function redirectToItineraire() {
    window.location.href = 'itineraire.html';
}

function redirectToACPM() {
    window.location.href = 'ACPM.html';
}

function redirectToConnexite() {
    window.location.href = 'connexite.html';
}

function redirectToPMR() {
    window.location.href = 'PMR.html';
}

function fetchMetroLineData() {
    fetch('http://127.0.0.1:25565/api/line/get-by-name/1')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 200 && data.data.length > 0) {
                const metroLine = data.data[0];
                const metroInfoDiv = document.getElementById('metroInfo');
                metroInfoDiv.innerHTML = `
                    <p>Nom de l'agence: ${metroLine.agency_name}</p>
                    <p>Nom court de la ligne: ${metroLine.route_short_name}</p>
                    <p>Nom long de la ligne: ${metroLine.route_long_name}</p>
                    <p>Couleur de la ligne: <span style="color: #${metroLine.route_color};">#${metroLine.route_color}</span></p>
                    <p>Couleur du texte: <span style="color: #${metroLine.route_text_color};">#${metroLine.route_text_color}</span></p>
                `;
            } else {
                throw new Error('No data found or status is not 200');
            }
        })
        .catch(error => {
            console.error('Il y a eu un problème avec la requête fetch:', error);
            const metroInfoDiv = document.getElementById('metroInfo');
            metroInfoDiv.innerHTML = `<p>Erreur: ${error.message}</p>`;
        });
}


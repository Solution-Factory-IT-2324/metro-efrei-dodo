document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const journeyId = urlParams.get('journey');

    if (journeyId) {
        fetch(`http://127.0.0.1:8080/api/journey/get-journey/${journeyId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 200) {
                    const mapContainer = document.getElementById('map');
                    const frame = document.createElement('iframe');
                    frame.setAttribute('src', `journey-map.html?journey=${journeyId}`);
                    frame.setAttribute('style', 'width: 100%; height: 100%; border: none;');
                    mapContainer.appendChild(frame);
                } else {
                    console.error('Error fetching journey data:', data.message);
                }
            })
            .catch(error => console.error('Error fetching journey data:', error));
    } else {
        console.error('No journey ID provided in the URL');
    }
});

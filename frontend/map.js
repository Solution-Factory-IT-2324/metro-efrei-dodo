document.addEventListener('DOMContentLoaded', () => {
    const map = L.map('map').setView([48.8566, 2.3522], 12); // Centered on Paris

    // Define different tile layers
    const baseLayers = {
    'CartoDB Positron': L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        }),
    'CartoDB Dark Matter': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        }),
    };

    // Add the default tile layer to the map
    baseLayers['CartoDB Positron'].addTo(map);
    L.control.layers(baseLayers).addTo(map);

    // Fetch line data to get colors
    fetch('http://127.0.0.1:25565/api/line/')
        .then(response => response.json())
        .then(lineData => {
            const lineColors = {};
            lineData.data.forEach(line => {
                lineColors[line.route_id] = `#${line.route_color}`;
            });

            // Fetch graph data
            fetch('http://127.0.0.1:8080/api/graph/')
                .then(response => response.json())
                .then(data => {
                    console.log('Graph data:', data);
                    const vertices = data.data.vertex;
                    const edges = data.data.edge;

                    // Add connections between stations
                    edges.forEach(edge => {
                        const fromStation = vertices[edge.from_stop_id];
                        const toStation = vertices[edge.to_stop_id];
                        // if ((fromStation && toStation) && (edge.type !== 'transfer')) {
                        if ((fromStation && toStation)) {
                            L.polyline([
                                [fromStation.stop_lat, fromStation.stop_lon],
                                [toStation.stop_lat, toStation.stop_lon]
                            ], {
                                color: lineColors[edge.line] || 'blue',
                                weight: 5,
                            }).addTo(map);
                        }
                    });

                    // Add station circle markers
                    Object.entries(vertices).forEach(([key, station]) => {
                        L.circleMarker([station.stop_lat, station.stop_lon], {
                            radius: 5,  // Adjust size of the circle
                            color: '#98aac3',
                            fillColor: '#ffffff',
                            opacity: 0.4,
                            fillOpacity: 1,
                        })
                        .bindPopup(`<b>${station.stop_name}</b><br>ID: ${key}`)  // Accessing key here
                        .addTo(map);
                    });

                })
                .catch(error => console.error('Error fetching graph data:', error));
        })
        .catch(error => console.error('Error fetching line data:', error));
});

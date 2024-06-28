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

    // Fetch line data to get colors, names, and route types
    fetch('http://127.0.0.1:8080/api/line/')
        .then(response => response.json())
        .then(lineData => {
            const lineColors = {};
            const lineNames = {};
            const lineTypes = {};
            lineData.data.forEach(line => {
                lineColors[line.route_id] = `#${line.route_color}`;
                lineNames[line.route_id] = line.route_long_name;
                lineTypes[line.route_id] = line.route_type;
            });

            // Fetch graph data
            fetch('http://127.0.0.1:8080/api/graph/')
                .then(response => response.json())
                .then(data => {
                    console.log('Graph data:', data);
                    const vertices = data.data.vertex;
                    const edges = data.data.edge;

                    // Create a mapping of station IDs to line names
                    const stationLines = {};
                    Object.entries(vertices).forEach(([key, station]) => {
                        if (!stationLines[key]) {
                            stationLines[key] = new Set();
                        }
                        // Add the line serving the station
                        if (lineNames[station.line]) {
                            stationLines[key].add(lineNames[station.line]);
                        }
                    });

                    // Function to add connections between stations
                    const addConnections = (filterFn) => {
                        edges.forEach(edge => {
                            const fromStation = vertices[edge.from_stop_id];
                            const toStation = vertices[edge.to_stop_id];
                            if ((fromStation && toStation) && (edge.type !== 'transfer')) {
                                if (filterFn(lineTypes[edge.line])) {
                                    let color = lineColors[edge.line] || 'blue';
                                    let weight = 5;
                                    let dashArray = '';

                                    // Change design based on route_type
                                    switch (lineTypes[edge.line]) {
                                        case 0:
                                            weight = 3;
                                            dashArray = '5, 10';
                                            break;
                                        case 1:
                                            weight = 3;
                                            break;
                                        case 2:
                                            weight = 5;
                                            break;
                                    }

                                    L.polyline([
                                        [fromStation.stop_lat, fromStation.stop_lon],
                                        [toStation.stop_lat, toStation.stop_lon]
                                    ], {
                                        color: color,
                                        weight: weight,
                                        dashArray: dashArray,
                                    }).addTo(map);

                                    // Update the mapping for stations connected by this edge
                                    if (lineNames[edge.line]) {
                                        stationLines[edge.from_stop_id].add(lineNames[edge.line]);
                                        stationLines[edge.to_stop_id].add(lineNames[edge.line]);
                                    }
                                }
                            }
                        });
                    };

                    // Function to clear the map
                    const clearMap = () => {
                        map.eachLayer(layer => {
                            if (layer instanceof L.Polyline || layer instanceof L.CircleMarker) {
                                map.removeLayer(layer);
                            }
                        });
                    };

                    // Add station circle markers
                    const addStations = () => {
                        const circleMarkers = [];
                        Object.entries(vertices).forEach(([key, station]) => {
                            const marker = L.circleMarker([station.stop_lat, station.stop_lon], {
                                radius: getRadius(map.getZoom()),  // Dynamic radius based on zoom level
                                color: '#98aac3',
                                fillColor: '#ffffff',
                                opacity: 0.4,
                                fillOpacity: 1,
                            })
                            .bindPopup(`
                                <b>${station.stop_name}</b><br>
                                ID: ${key}<br>
                                Lignes: ${Array.from(stationLines[key]).join(', ')}
                            `)
                            .addTo(map);
                            circleMarkers.push(marker);
                        });

                        // Function to calculate radius based on zoom level
                        function getRadius(zoom) {
                            return Math.max(3, zoom - 12);  // Example: Adjust radius calculation as needed
                        }

                        // Function to update the radius of all circle markers
                        function updateMarkerRadius() {
                            const zoom = map.getZoom();
                            circleMarkers.forEach(marker => {
                                marker.setRadius(getRadius(zoom));
                            });
                        }

                        // Update radius when zoom level changes
                        map.on('zoomend', updateMarkerRadius);
                    };

                    // Add all stations initially
                    addStations();

                    // Filter functions
                    const filterTrain = (routeType) => routeType === 2;
                    const filterTramway = (routeType) => routeType === 0;
                    const filterMetro = (routeType) => routeType === 1;

                    // Create boolean filter functions for each route type
                    let filterActiveTrain = true;
                    let filterActiveTramway = true;
                    let filterActiveMetro = true;

                    // Add event listeners to filter buttons
                    document.getElementById('filter-train').addEventListener('click', () => {
                        filterActiveTrain = !filterActiveTrain;
                        clearMap();
                        addStations();
                        filterActiveTrain ? addConnections(filterTrain) : addConnections(() => false);
                        filterActiveTramway ? addConnections(filterTramway) : addConnections(() => false);
                        filterActiveMetro ? addConnections(filterMetro) : addConnections(() => false);
                    });

                    document.getElementById('filter-tramway').addEventListener('click', () => {
                        filterActiveTramway = !filterActiveTramway;
                        clearMap();
                        addStations();
                        filterActiveTrain ? addConnections(filterTrain) : addConnections(() => false);
                        filterActiveTramway ? addConnections(filterTramway) : addConnections(() => false);
                        filterActiveMetro ? addConnections(filterMetro) : addConnections(() => false);
                    });

                    document.getElementById('filter-metro').addEventListener('click', () => {
                        filterActiveMetro = !filterActiveMetro;
                        clearMap();
                        addStations();
                        filterActiveTrain ? addConnections(filterTrain) : addConnections(() => false);
                        filterActiveTramway ? addConnections(filterTramway) : addConnections(() => false);
                        filterActiveMetro ? addConnections(filterMetro) : addConnections(() => false);
                    });

                    // Add all connections initially
                    addConnections(() => true);
                })
                .catch(error => console.error('Error fetching graph data:', error));
        })
        .catch(error => console.error('Error fetching line data:', error));
});

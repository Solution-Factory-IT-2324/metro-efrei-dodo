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

    let currentBaseLayer;
    const setBaseLayer = () => {
        const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (isDarkMode) {
            if (currentBaseLayer !== baseLayers['CartoDB Dark Matter']) {
                if (currentBaseLayer) {
                    map.removeLayer(currentBaseLayer);
                }
                baseLayers['CartoDB Dark Matter'].addTo(map);
                currentBaseLayer = baseLayers['CartoDB Dark Matter'];
            }
        } else {
            if (currentBaseLayer !== baseLayers['CartoDB Positron']) {
                if (currentBaseLayer) {
                    map.removeLayer(currentBaseLayer);
                }
                baseLayers['CartoDB Positron'].addTo(map);
                currentBaseLayer = baseLayers['CartoDB Positron'];
            }
        }
    };

    // Add the initial tile layer to the map
    setBaseLayer();

    // Add layer control to the map
    const layersControl = L.control.layers(baseLayers).addTo(map);

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
            const fetchGraphData = (algorithm) => {
                fetch(`http://127.0.0.1:8080/api/graph/tree-structure/${algorithm}`)
                    .then(response => response.json())
                    .then(graphData => {
                        const vertices = graphData.data.vertex;
                        const edges = graphData.data.edge;

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
                                    Lignes: ${Array.from(stationLines[key]).join(', ')}<br>
                                    Accessible PMR : ${station.wheelchair === 1 ? 'Oui' : 'Non'}
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

                            // Reorder markers to bring them to back
                            circleMarkers.forEach(marker => {
                                marker.bringToBack();
                            });
                        };

                        // Function to add connections between stations
                        const addConnections = () => {
                            const layers = [];
                            edges.forEach(edge => {
                                const fromCoords = [vertices[edge.from_stop_id].stop_lat, vertices[edge.from_stop_id].stop_lon];
                                const toCoords = [vertices[edge.to_stop_id].stop_lat, vertices[edge.to_stop_id].stop_lon];

                                // Color of the line
                                let color = lineColors[vertices[edge.from_stop_id].line];
                                let weight = 5;
                                let dashArray = '';

                                const polyline = L.polyline([fromCoords, toCoords], {
                                    color: color,
                                    weight: weight,
                                    dashArray: dashArray,
                                }).bindPopup(`
                                    <b>Line:</b> ${lineNames[vertices[edge.from_stop_id].line]}<br>
                                    <b>From:</b> ${vertices[edge.from_stop_id].stop_name}<br>
                                    <b>To:</b> ${vertices[edge.to_stop_id].stop_name}<br>
                                `).addTo(map);

                                layers.push({ layer: polyline, mode: 'APCM' });
                            });

                            // Apply hierarchy for superposition
                            layers.forEach(item => {
                                item.layer.bringToFront();
                            });
                        };

                        // Add all stations initially
                        addStations();

                        // Add all connections initially
                        addConnections();
                    })
                    .catch(error => console.error('Error fetching graph data:', error));
            };

            // Function to clear the map
            const clearMap = () => {
                map.eachLayer(layer => {
                    if (layer instanceof L.Polyline || layer instanceof L.CircleMarker) {
                        map.removeLayer(layer);
                    }
                });
            };

            const toggleButtonActiveState = (buttonId, isActive) => {
                const button = document.getElementById(buttonId);
                if (isActive) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
            };

            let filterActivePrim = true;
            toggleButtonActiveState('filter-prim', filterActivePrim);
            let filterActiveKruskal = false;

            // Initialize the map with Prim algorithm
            fetchGraphData('prim');

            // Add event listeners to filter buttons
            document.getElementById('filter-prim').addEventListener('click', () => {
                clearMap();
                filterActivePrim = !filterActivePrim;
                filterActiveKruskal = !filterActiveKruskal;
                toggleButtonActiveState('filter-kruskal', filterActiveKruskal);
                toggleButtonActiveState('filter-prim', filterActivePrim);
                fetchGraphData('prim');
            });

            document.getElementById('filter-kruskal').addEventListener('click', () => {
                clearMap();
                filterActivePrim = !filterActivePrim;
                filterActiveKruskal = !filterActiveKruskal;
                toggleButtonActiveState('filter-kruskal', filterActiveKruskal);
                toggleButtonActiveState('filter-prim', filterActivePrim);
                fetchGraphData('kruskal');
            });

        })
        .catch(error => console.error('Error fetching line data:', error));
});

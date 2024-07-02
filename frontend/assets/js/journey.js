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

    const fetchGraph = async () => {
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

                        // Draw only transfer
                        const drawTransfers = () => {
                            edges.forEach(edge => {
                                if (edge.type !== 'transfer') {
                                    return;
                                }
                                const fromCoords = [vertices[edge.from_stop_id].stop_lat, vertices[edge.from_stop_id].stop_lon];
                                const toCoords = [vertices[edge.to_stop_id].stop_lat, vertices[edge.to_stop_id].stop_lon];
                                const polyline = L.polyline([fromCoords, toCoords], {
                                    color: currentBaseLayer === baseLayers['CartoDB Dark Matter'] ? 'rgba(255,255,255,0.25)' : '#000000',
                                    opacity: 0.05,
                                    weight: 3,
                                }).addTo(map);
                            });
                        };

                        // Fetch traces data from the Ile-de-France Mobilités dataset
                        fetch('http://127.0.0.1:8080/assets/json/traces-du-reseau-ferre-idf.json')
                            .then(response => response.json())
                            .then(tracesData => {
                                const records = tracesData;

                                // Function to add connections between stations
                                const addConnections = (filterFn) => {
                                    const layers = [];
                                    records.forEach(record => {
                                        const fields = record;
                                        const coordinates = fields.geo_shape.geometry.coordinates;
                                        const picto = fields.picto_final ? fields.picto_final !== "picto_intermediaire/300" ? `<img src="${fields.picto_final}" alt="icon" style="width:16px; height:16px;">` : fields.mode === "TER" ? `<img src="/assets/TRAIN.png" alt="icon" style="width:16px; height:16px;">` : '' : '';

                                        let color = lineColors['IDFM:' + fields.idrefligc] || 'blue';
                                        if (color === 'blue') {
                                            color = lineColors['IDFM:' + fields.idrefligc.replace('T', 'B')]
                                        }
                                        let weight = 5;
                                        let dashArray = '';

                                        // Change design based on route_type
                                        switch (fields.mode) {
                                            case 'TRAMWAY':
                                                weight = 3;
                                                dashArray = '5, 1, 5';
                                                break;
                                            case 'METRO':
                                                weight = 3;
                                                break;
                                            case 'TRAIN':
                                                weight = 5;
                                                break;
                                            case 'RER':
                                                weight = 5;
                                                break;
                                            case 'TER':
                                                weight = 5;
                                                dashArray = '5, 15';
                                                color = '#AAAAAA';
                                                break;
                                        }

                                        if (filterFn(fields.mode)) {
                                            const latlngs = coordinates.map(coord => [coord[1], coord[0]]);
                                            const polyline = L.polyline(latlngs, {
                                                color: color,
                                                weight: weight,
                                                dashArray: dashArray,
                                                opacity: 0.15,
                                            }).bindPopup(`
                                            ${picto ? picto : ''}${picto ? ' ' : ''}<b>${fields.reseau}</b><br>
                                            ID Ligne: ${fields.idrefligc}<br>
                                            Mode: ${fields.mode === 'TRAIN' ? 'Transilien' : fields.mode}<br>
                                            `).addTo(map);

                                            layers.push({layer: polyline, mode: fields.mode});
                                        }
                                    });

                                    // Apply hierarchy for superposition
                                    layers.forEach(item => {
                                        if (item.mode === 'METRO' || item.mode === 'RER') {
                                            item.layer.bringToFront();
                                        } else if (item.mode === 'TRAMWAY' || item.mode === 'TER') {
                                            item.layer.bringToBack();
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
                                            opacity: 0.05,
                                            fillOpacity: 0.25,
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
                                        marker.bringToFront();
                                    });
                                };

                                // Function to update connections based on filter states
                                const updateConnections = () => {
                                    clearMap();
                                    addStations();
                                    if (filterActiveTrain) addConnections(mode => mode === 'TRAIN');
                                    if (filterActiveTramway) addConnections(mode => mode === 'TRAMWAY');
                                    if (filterActiveMetro) addConnections(mode => mode === 'METRO');
                                    if (filterActiveRER) addConnections(mode => mode === 'RER');
                                    if (filterActiveTER) addConnections(mode => mode === 'TER');
                                    if (filterActiveTransfer) drawTransfers();
                                };

                                // Create boolean filter functions for each route type
                                let filterActiveTrain = true;
                                let filterActiveTramway = true;
                                let filterActiveMetro = true;
                                let filterActiveRER = true;
                                let filterActiveTER = true;
                                let filterActiveTransfer = true;

                                // Add all stations initially
                                addStations();

                                // Add all connections initially
                                updateConnections();

                                // Draw transfers
                                drawTransfers();
                            })
                            .catch(error => console.error('Error fetching traces data:', error));
                    })
                    .catch(error => console.error('Error fetching graph data:', error));
            })
            .catch(error => console.error('Error fetching line data:', error));
    };

    fetchGraph();

    // Add the initial tile layer to the map
    setBaseLayer();

    // Add layer control to the map
    const layersControl = L.control.layers(baseLayers).addTo(map);

    const urlParams = new URLSearchParams(window.location.search);
    const journeyId = urlParams.get('id');

    if (journeyId) {
        fetch(`http://127.0.0.1:8080/api/journey/get-journey/${journeyId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 200) {
                    displayJourney(data.data);
                } else {
                    console.error('Error fetching journey data:', data.message);
                }
            })
            .catch(error => console.error('Error fetching journey data:', error));
    } else {
        console.error('No journey ID provided in the URL');
    }
});

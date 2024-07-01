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
                                color: currentBaseLayer === baseLayers['CartoDB Dark Matter'] ? '#ffffff' : '#000000',
                                opacity: 0.1,
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
                                        }).bindPopup(`
                                        ${picto ? picto : ''}${picto ? ' ' : ''}<b>${fields.reseau}</b><br>
                                        ID Ligne: ${fields.idrefligc}<br>
                                        Mode: ${fields.mode === 'TRAIN' ? 'Transilien' : fields.mode}<br>
                                        `).addTo(map);

                                        layers.push({ layer: polyline, mode: fields.mode });
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

                            // Function to update connections based on filter states
                            const updateConnections = () => {
                                clearMap();
                                addStations();
                                if (filterActiveTrain) addConnections(mode => mode === 'TRAIN');
                                toggleButtonActiveState('filter-train', filterActiveTrain);
                                if (filterActiveTramway) addConnections(mode => mode === 'TRAMWAY');
                                toggleButtonActiveState('filter-tramway', filterActiveTramway);
                                if (filterActiveMetro) addConnections(mode => mode === 'METRO');
                                toggleButtonActiveState('filter-metro', filterActiveMetro);
                                if (filterActiveRER) addConnections(mode => mode === 'RER');
                                toggleButtonActiveState('filter-rer', filterActiveRER);
                                if (filterActiveTER) addConnections(mode => mode === 'TER');
                                toggleButtonActiveState('filter-ter', filterActiveTER);
                                if (filterActiveTransfer) drawTransfers();
                                toggleButtonActiveState('station-connections', filterActiveTransfer);
                            };

                            // Create boolean filter functions for each route type
                            let filterActiveTrain = true;
                            let filterActiveTramway = true;
                            let filterActiveMetro = true;
                            let filterActiveRER = true;
                            let filterActiveTER = true;
                            let filterActiveTransfer = true;

                            const toggleButtonActiveState = (buttonId, isActive) => {
                                const button = document.getElementById(buttonId);
                                if (isActive) {
                                    button.classList.add('active');
                                } else {
                                    button.classList.remove('active');
                                }
                            };

                            // Add event listeners to filter buttons
                            document.getElementById('filter-train').addEventListener('click', () => {
                                filterActiveTrain = !filterActiveTrain;
                                updateConnections();
                            });

                            document.getElementById('filter-tramway').addEventListener('click', () => {
                                filterActiveTramway = !filterActiveTramway;
                                updateConnections();
                            });

                            document.getElementById('filter-metro').addEventListener('click', () => {
                                filterActiveMetro = !filterActiveMetro;
                                updateConnections();
                            });

                            document.getElementById('filter-rer').addEventListener('click', () => {
                                filterActiveRER = !filterActiveRER;
                                updateConnections();
                            });

                            document.getElementById('filter-ter').addEventListener('click', () => {
                                filterActiveTER = !filterActiveTER;
                                updateConnections();
                            });

                            document.getElementById('station-connections').addEventListener('click', () => {
                                filterActiveTransfer = !filterActiveTransfer;
                                updateConnections();
                            });

                            // Add all stations initially
                            addStations();

                            // Add all connections initially
                            updateConnections();

                            // Draw transfers
                            drawTransfers();

                            // Add listener when dark/light mode changes
                            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
                                setBaseLayer();
                                console.log(currentBaseLayer === baseLayers['CartoDB Dark Matter'])
                                updateConnections();
                            });

                            // Event listener for base layer change
                            map.on('baselayerchange', (event) => {
                                currentBaseLayer = event.layer;
                                console.log(`Base layer changed to: ${event.name}`);
                                updateConnections();
                            });

                        })
                        .catch(error => console.error('Error fetching traces data:', error));
                })
                .catch(error => console.error('Error fetching graph data:', error));
        })
        .catch(error => console.error('Error fetching line data:', error));
});

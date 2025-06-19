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
                                        const picto = fields.picto_final ? fields.picto_final !== "picto_intermediaire/300" ? `<img src="${fields.picto_final}" alt="icon" style="width:16px; height:16px;">` : fields.mode === "TER" ? `<img src="/assets/img/TRAIN.svg" alt="icon" style="width:16px; height:16px;">` : '' : '';

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
                                                opacity: 0.3,
                                            }).bindPopup(`
                                            ${picto ? picto : ''}${picto ? ' ' : ''}<b>${fields.res_com}</b><br>
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
                                            opacity: 0.2,
                                            fillOpacity: 0.5,
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

    // Fetch and merge station data
    fetch('http://127.0.0.1:8080/api/stations/')
        .then(response => response.json())
        .then(data => {
            const stations = {};
            data.data.forEach(station => {
                if (!stations[station.stop_name]) {
                    stations[station.stop_name] = {
                        stop_name: station.stop_name,
                        stop_lat: station.stop_lat,
                        stop_lon: station.stop_lon,
                        stop_id: new Set(),
                        lines: new Set(),
                    };
                }
                stations[station.stop_name].lines.add(station.route_long_name);
                stations[station.stop_name].stop_id.add(station.stop_id);
            });
            const mergedStations = Object.values(stations).map(station => ({
                stop_name: station.stop_name,
                stop_lat: station.stop_lat,
                stop_lon: station.stop_lon,
                stop_id: Array.from(station.stop_id),
                lines: Array.from(station.lines),
            }));

            // Implement autocomplete for input fields
            const startInput = document.getElementById('departure');
            const endInput = document.getElementById('arrival');
            const startSuggestionsContainer = document.getElementById('departure-suggestions');
            const endSuggestionsContainer = document.getElementById('arrival-suggestions');

            const createSuggestions = (input) => {
                const value = input.value.toLowerCase();
                const suggestions = mergedStations.filter(station =>
                    station.stop_name.toLowerCase().includes(value)
                );
                return suggestions;
            };

            const displaySuggestions = (input, suggestions, suggestionsContainer) => {
                suggestionsContainer.innerHTML = '';
                // Limit to 5 suggestions
                suggestions = suggestions.slice(0, 8);
                suggestions.forEach(suggestion => {
                    const div = document.createElement('div');
                    div.classList.add('suggestion');
                    div.innerHTML = `<strong>${suggestion.stop_name}</strong><br>
                                    ${suggestion.lines.join(', ')}`;
                    div.addEventListener('click', () => {
                        input.value = suggestion.stop_name;
                        suggestionsContainer.innerHTML = '';
                    });
                    suggestionsContainer.appendChild(div);
                });

                if (suggestions.length === 0) {
                    const div = document.createElement('div');
                    div.classList.add('suggestion');
                    div.innerHTML = 'Aucun résultat trouvé.';
                    div.style.pointerEvents = 'none';
                    suggestionsContainer.appendChild(div);
                }
            };

            startInput.addEventListener('input', () => {
                const suggestions = createSuggestions(startInput);
                displaySuggestions(startInput, suggestions, startSuggestionsContainer);
                startSuggestionsContainer.style.display = 'block';
            });

            endInput.addEventListener('input', () => {
                const suggestions = createSuggestions(endInput);
                displaySuggestions(endInput, suggestions, endSuggestionsContainer);
                endSuggestionsContainer.style.display = 'block';
            });

            const hideSuggestions = (suggestionsContainer) => {
                suggestionsContainer.style.display = 'none';
            };

            startInput.addEventListener('blur', () => {
                setTimeout(() => hideSuggestions(startSuggestionsContainer), 100);
            });

            endInput.addEventListener('blur', () => {
                setTimeout(() => hideSuggestions(endSuggestionsContainer), 100);
            });

            startInput.addEventListener('focus', () => {
                if (startInput.value !== '') {
                    const suggestions = createSuggestions(startInput);
                    displaySuggestions(startInput, suggestions, startSuggestionsContainer);
                    startSuggestionsContainer.style.display = 'block';
                }
            });

            endInput.addEventListener('focus', () => {
                if (endInput.value !== '') {
                    const suggestions = createSuggestions(endInput);
                    displaySuggestions(endInput, suggestions, endSuggestionsContainer);
                    endSuggestionsContainer.style.display = 'block';
                }
            });

            hideSuggestions(startSuggestionsContainer);
            hideSuggestions(endSuggestionsContainer);

            const whenInput = document.getElementById('when');
            const now = new Date();
            now.setHours(now.getHours() + 2);
            whenInput.value = now.toISOString().slice(0, 16);
            whenInput.readOnly = true;

            const searchButton = document.getElementById('search-button');
            searchButton.addEventListener('click', () => {
            const departure = document.getElementById('departure').value;
            const arrival = document.getElementById('arrival').value;

            if (departure && arrival) {
                // Match the stop_id of the selected stations
                const departureStation = mergedStations.find(station => station.stop_name === departure);
                const arrivalStation = mergedStations.find(station => station.stop_name === arrival);
                console.log(departureStation.stop_id[0], arrivalStation.stop_id[0]);

                fetch('http://127.0.0.1:8080/api/journey', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        start_vertex: departureStation.stop_id[0],
                        end_vertex: arrivalStation.stop_id[0]
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    const journeyId = data.data.journey_id;
                    console.log('Journey ID:', journeyId)
                    if (journeyId) {
                        window.location.href = `journey-map.html?journey=${journeyId}`;
                    }
                })
                .catch(error => {
                    console.error('Error calculating journey:', error);
                });
            } else {
                alert('Veuillez entrer une gare de départ et une gare d\'arrivée.');
            }
        });


        })
        .catch(error => console.error('Error fetching stations data:', error));
});

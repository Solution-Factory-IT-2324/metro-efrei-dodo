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

    const journeyPanel = document.getElementById('journey-panel');
    const journeyInfo = document.getElementById('journey-info');
    // const closePanel = document.getElementById('close-panel');

    const openJourneyPanel = () => {
    journeyPanel.classList.add('open');
    };

    const closeJourneyPanel = () => {
        journeyPanel.classList.remove('open');
    };

    // closePanel.addEventListener('click', closeJourneyPanel);

    const fetchGraph = () => {
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
                                    opacity: currentBaseLayer === baseLayers['CartoDB Dark Matter'] ? 0.1 : 0.01,
                                    weight: 2,
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

                                const urlParams = new URLSearchParams(window.location.search);
                                const journeyId = urlParams.get('journey');

                                // Function to update connections based on filter states
                                const updateConnections = () => {
                                    clearMap();
                                    addStations();

                                    fetch(`http://127.0.0.1:8080/api/journey/get-journey/${journeyId}`)
                                        .then(response => response.json())
                                        .then(data => {
                                            if (data.status === 200) {
                                                displayJourney(data.data);
                                            }
                                        })
                                        .catch(error => console.error('Error fetching journey data:', error));

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

                                const displayJourney = (journeyData) => {
                                    const pathCoordinates = journeyData.path.map(step => [vertices[step.stop_id].stop_lat, vertices[step.stop_id].stop_lon]);

                                    // Helper function to round coordinates
                                    const roundCoordinate = (coord, decimals = 8) => {
                                        return parseFloat(parseFloat(coord).toFixed(decimals));
                                    };

                                    // Clear previous journey info
                                    journeyInfo.innerHTML = '';

                                    // Calculate journey time in minutes
                                    const journeyStartTime = new Date(journeyData["datetime-generation"] * 1000);
                                    const journeyEndTime = new Date(journeyStartTime.getTime() + (journeyData.path[journeyData.path.length - 1].time * 1000));
                                    const journeyDuration = Math.round((journeyEndTime - journeyStartTime) / 60000); // Duration in minutes

                                    // Format time for display
                                    const formatTime = date => date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

                                    // Collect unique lines used in the journey
                                    const linesUsed = [];
                                    journeyData.path.forEach(step => {
                                        if (!linesUsed.includes(step.line)) {
                                            linesUsed.push(step.line);
                                        }
                                    });

                                    // Generate HTML for lines with pictograms
                                    const lineIconsHtml = linesUsed.map(line => {
                                        let iconSrc;
                                        switch (lineTypes[line]) {
                                            case 0:
                                                iconSrc = 'assets/img/TRAM.svg';
                                                break;
                                            case 1:
                                                iconSrc = 'assets/img/METRO.svg';
                                                break;
                                            case 2:
                                                iconSrc = 'assets/img/TRAIN.svg';
                                                break;
                                            case 3:
                                                iconSrc = 'assets/img/RER.svg';
                                                break;
                                            default:
                                                iconSrc = 'assets/img/default-icon.png';
                                        }
                                        return `<span class="metro-icon"><img src="${iconSrc}" alt="icon" class="line-icon" style="width: 16px; height: 16px" "> <span class="line-number" style="color: ${lineColors[line]}">${lineNames[line] || 'N/A'}</span></span>`;
                                    }).join('<span class="metro-icon"> > </span>');

                                    // Add summary information
                                    const journeySummary = document.createElement('div');
                                    journeySummary.id = 'journey-summary';
                                    journeySummary.innerHTML = `
                                        <div class="journey-header">
                                            <div class="journey-info">
                                                <div class="journey-title">
                                                    <p>${journeyData.path[0].stop_name}</p>
                                                    <p>${journeyData.path[journeyData.path.length - 1].stop_name}</p>
                                                </div>
                                                <div class="journey-icons">
                                                    ${lineIconsHtml}
                                                </div>
                                                <div class="journey-time">
                                                    <p>${journeyStartTime.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })} | ${formatTime(journeyStartTime)} → ${formatTime(journeyEndTime)}</p>
                                                    <p>${journeyDuration} min</p>
                                                </div>
                                            </div>
                                            <div class="journey-actions">
                                                <div class="action-button">
                                                    <img src="assets/img/PRINT.svg" alt="Imprimer en PDF" style="width: 24px; height: 24px">
                                                    <p>Imprimer</p>
                                                </div>
                                                <div class="action-button">
                                                    <img src="assets/img/SHARE.svg" alt="Partager le lien" style="width: 24px; height: 24px">
                                                    <p>Partager</p>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                    journeyInfo.appendChild(journeySummary);

                                    // Draw a line from coordinate A to coordinate B
                                    const drawLine = (fromStopId, toStopId, color, weight, dashArray, opacity) => {
                                        const fromStopLat = roundCoordinate(vertices[fromStopId].stop_lat);
                                        const fromStopLon = roundCoordinate(vertices[fromStopId].stop_lon);
                                        const toStopLat = roundCoordinate(vertices[toStopId].stop_lat);
                                        const toStopLon = roundCoordinate(vertices[toStopId].stop_lon);

                                        const coords = [
                                            [fromStopLat, fromStopLon],
                                            [toStopLat, toStopLon]
                                        ];

                                        const polyline = L.polyline(coords, {
                                            color: color,
                                            weight: weight,
                                            dashArray: dashArray,
                                            opacity: opacity,
                                        }).addTo(map);
                                    };

                                    journeyData.path.forEach((step, index) => {
                                        if (index < journeyData.path.length - 1) {
                                            const nextStep = journeyData.path[index + 1];
                                            let color = step.line ? lineColors[step.line] : 'blue';
                                            let weight = 5;
                                            let dashArray = '';

                                            if (nextStep.connection_type === 'transfer') {
                                                dashArray = '5, 5';
                                                color = currentBaseLayer === baseLayers['CartoDB Dark Matter'] ? 'rgba(255,255,255,0.25)' : '#000000';
                                                opacity = 0.75;
                                                weight = 3;
                                            } else {
                                                opacity = 1;
                                                switch (lineTypes[step.line]) {
                                                    case 0:
                                                        weight = 2;
                                                        dashArray = '5, 1, 5';
                                                        break;
                                                    case 1:
                                                        weight = 3;
                                                        break;
                                                    case 2:
                                                        weight = 5;
                                                        break;
                                                }
                                            }

                                            drawLine(step.stop_id, nextStep.stop_id, color, weight, dashArray, opacity);
                                        }

                                        let iconSrc;
                                        switch (lineTypes[step.line]) {
                                            case 0:
                                                iconSrc = 'assets/img/TRAM.svg';
                                                break;
                                            case 1:
                                                iconSrc = 'assets/img/METRO.svg';
                                                break;
                                            case 2:
                                                iconSrc = 'assets/img/TRAIN.svg';
                                                break;
                                            case 3:
                                                iconSrc = 'assets/img/RER.svg';
                                                break;
                                            default:
                                                iconSrc = 'assets/img/default-icon.png';
                                        }
                                        const stepDiv = document.createElement('div');
                                        stepDiv.classList.add('journey-step');
                                        stepDiv.innerHTML = `
                                            <div>
                                            <b>${step.stop_name}</b>${vertices[step.stop_id].wheelchair === 1 ? '<span style="margin-left: 4px"><img src="assets/img/PMR.svg" alt="Accessible PMR" style="width: 16px; height: 16px; filter: invert(51%) sepia(70%) saturate(3301%) hue-rotate(161deg) brightness(95%) contrast(101%);"></span>' : ''}<br>
                                            <span class="metro-icon"><img src="${iconSrc}" alt="icon" class="line-icon" style="width: 16px; height: 16px" "><span style="padding-left: 4px; color: ${lineColors[step.line]}">${lineNames[step.line] || 'N/A'}</span></span><br>
                                            ${parseFloat(step.time) !== 0.0 ? 'Temps : ' : ''}${parseInt(step.time / 60) ? parseInt(step.time % 60) ? parseInt(step.time / 60) + 'min ' : parseInt(step.time / 60) + 'min<br>' : ''}${parseInt(step.time % 60) ? parseInt(step.time % 60) + 's<br>' : ''}
                                            ${step.connection_type ? step.connection_type === 'start' ? '' : journeyData.path[journeyData.path.length - 1].stop_id === step.stop_id ? '' : 'Connection : ' : ''}${step.connection_type === 'transfer' ? 'Transfert' : step.connection_type === 'start' ? 'Station de départ' : journeyData.path[journeyData.path.length - 1].stop_id === step.stop_id ? 'Station de destination' : step.connection_type === 'connection' ? 'Voyage' : step.connection_type}
                                            </div>
                                        `;
                                        journeyInfo.appendChild(stepDiv);
                                    });

                                    // Adjust the map to fit the bounds with some padding
                                    const paddedBounds = L.latLngBounds(pathCoordinates).pad(0.1);
                                    map.fitBounds(paddedBounds);

                                    // Add circle markers for each stop in the journey
                                    journeyData.path.forEach(step => {
                                        L.circleMarker([vertices[step.stop_id].stop_lat, vertices[step.stop_id].stop_lon], {
                                            radius: 5,
                                            color: journeyData.path[0].stop_id === step.stop_id ? 'green' : journeyData.path[journeyData.path.length - 1].stop_id === step.stop_id ? 'red' : 'blue',
                                            fillColor: '#ffffff',
                                            opacity: 0.9,
                                            fillOpacity: 1,
                                        })
                                        .bindPopup(`
                                            <b>${step.stop_name}</b><br>
                                            ID Station : ${step.stop_id}<br>
                                            Ligne : ${lineNames[step.line] || 'N/A'}<br>
                                            Temps : ${parseInt(step.time / 60)} min ${step.time % 60} s<br>
                                            Connection : ${step.connection_type === 'transfer' ? 'Transfert' : step.connection_type === 'start' ? 'Départ' : journeyData.path[journeyData.path.length - 1].stop_id === step.stop_id ? 'Destination' : step.connection_type === 'connection' ? 'Voyage' : step.connection_type}
                                        `)
                                        .addTo(map);
                                    });

                                    openJourneyPanel();
                                };


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
    };

    fetchGraph();

    // Add the initial tile layer to the map
    setBaseLayer();

    // Add layer control to the map
    const layersControl = L.control.layers(baseLayers).addTo(map);
});
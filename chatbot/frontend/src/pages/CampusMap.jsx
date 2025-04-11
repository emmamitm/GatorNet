import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css';
import 'leaflet-routing-machine';

// Color mapping for location types
const iconColors = {
  university: '#B73239',
  building: '#F37021',
  residential: '#6C9AC3',
  parking: '#4D4D4D',
  community_centre: '#7BAFD4',
  police: '#0021A5',
  restaurant: '#D82900',
  cafe: '#D82900',
  library: '#6C3C00',
  leisure: '#33A02C',
  shop: '#E31A1C',
  highway: '#999999',
  natural: '#006837',
  default: '#FA4616',
};

// Global map instance
let map;

const CampusMap = () => {
  const [locations, setLocations] = useState([]);
  const routingControl = useRef(null); // Holds reference to active route

  useEffect(() => {
    // Prevent duplicate map initialization
    if (map || document.getElementById('map')?._leaflet_id) return;

    // Initialize the map centered on UF
    map = L.map('map').setView([29.6436, -82.3549], 15);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    // Load OSM location data from Flask API
    fetch(`${process.env.REACT_APP_API_URL}/api/map-data`)
      .then((res) => res.json())
      .then((data) => {
        if (!data.locations) return;
        const locs = data.locations;
        setLocations(locs);

        // Update total location count in the UI
        document.getElementById('location-count').textContent =
          `Showing ${locs.length} locations on campus`;

        // Add a marker for each location
        locs.forEach((location) => {
          if (!location.lat || !location.lon) return;

          const color = iconColors[location.element_type] || iconColors.default;

          // Custom colored marker
          const icon = L.divIcon({
            className: 'my-custom-pin',
            iconAnchor: [0, 24],
            popupAnchor: [0, -36],
            html: `<span style="
              background-color: ${color};
              width: 1.5rem;
              height: 1.5rem;
              display: block;
              left: -0.75rem;
              top: -0.75rem;
              position: relative;
              border-radius: 1.5rem 1.5rem 0;
              transform: rotate(45deg);
              border: 1px solid #FFF;"></span>`,
          });

          // Add marker to map
          const marker = L.marker([location.lat, location.lon], {
            icon,
            title: location.name,
          }).addTo(map);

          // Save reference for filtering
          location.marker = marker;

          // Generate popup content with tags and nav button
          let popupContent = `<div class="popup-content">
            <h3>${location.name}</h3>
            <button onclick="window.__startNav(${location.lat}, ${location.lon})">Navigate Here</button>
            <p>Type: ${location.element_type}</p>`;

          if (location.source_file) {
            popupContent += `<p>Source: ${location.source_file}</p>`;
          }

          if (location.tags) {
            popupContent += '<hr>';
            for (const [key, value] of Object.entries(location.tags)) {
              if (key !== 'name' && key !== 'official_name') {
                popupContent += `<div class="popup-tag"><strong>${key}:</strong> ${value}</div>`;
              }
            }
          }

          popupContent += '</div>';
          marker.bindPopup(popupContent);
        });

        // Build the legend
        const legend = document.getElementById('legend-items');
        legend.innerHTML = '';
        const types = new Set(locs.map(l => l.element_type));
        types.forEach(type => {
          const color = iconColors[type] || iconColors.default;
          const div = document.createElement('div');
          div.style.display = 'flex';
          div.style.alignItems = 'center';
          div.style.marginBottom = '5px';
          div.innerHTML = `
            <div style="width: 16px; height: 16px; background: ${color}; border-radius: 50%; margin-right: 8px;"></div>
            <div>${type}</div>`;
          legend.appendChild(div);
        });

        // Handle search input
        const searchInput = document.getElementById('search-input');
        const resultsDiv = document.getElementById('search-results');
        const countDiv = document.getElementById('location-count');

        searchInput.addEventListener('input', (e) => {
          const query = e.target.value.trim();
          resultsDiv.innerHTML = '';

          if (!query) {
            // Show all markers again if search is cleared
            countDiv.textContent = `Showing ${locs.length} locations on campus`;
            locs.forEach(loc => {
              if (loc.marker) loc.marker.addTo(map);
            });
            return;
          }

          // Safely compile regex
          let regex;
          try {
            regex = new RegExp(query, 'i');
          } catch {
            resultsDiv.textContent = 'Invalid regex';
            return;
          }

          // Find matches and update UI
          const matches = locs.filter(loc => regex.test(loc.name));
          countDiv.textContent = `Found ${matches.length} locations`;

          // Show/hide markers based on match
          locs.forEach(loc => {
            if (!loc.marker) return;
            if (regex.test(loc.name)) {
              loc.marker.addTo(map);
            } else {
              map.removeLayer(loc.marker);
            }
          });

          // Show result list
          matches.slice(0, 100).forEach(loc => {
            const item = document.createElement('div');
            item.textContent = loc.name;
            item.style.cursor = 'pointer';
            item.onclick = () => {
              if (!map || !loc.marker) return;
              map.setView([loc.lat, loc.lon], 18);
              loc.marker.openPopup();
            };
            resultsDiv.appendChild(item);
          });
        });

        // Navigation handler - triggered by "Navigate Here" button in popups
        window.__startNav = (destLat, destLon) => {
          if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser.');
            return;
          }

          navigator.geolocation.getCurrentPosition(
            (pos) => {
              const start = [pos.coords.latitude, pos.coords.longitude];

              // Remove existing route if present
              if (routingControl.current) {
                map.removeControl(routingControl.current);
              }

              // Add new routing control with directions
              routingControl.current = L.Routing.control({
                waypoints: [L.latLng(start), L.latLng(destLat, destLon)],
                router: L.Routing.osrmv1({
                  serviceUrl: 'https://router.project-osrm.org/route/v1',
                }),
                lineOptions: {
                  styles: [{ color: 'blue', opacity: 0.7, weight: 5 }],
                },
                routeWhileDragging: false,
                show: false
              })
              .on('routesfound', function (e) {
                const summary = e.routes[0].summary;
                const instructions = e.routes[0].instructions || [];
                const dirDiv = document.getElementById('directions');

                // Show and populate the directions box
                dirDiv.style.display = 'block';
                dirDiv.innerHTML = `
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0;">Directions</h4>
                    <button id="close-directions" style="background: none; border: none; font-size: 16px; cursor: pointer;">✕</button>
                  </div>
                  <div style="margin-top: 5px;">
                    <strong>Estimated time:</strong> ${Math.round(summary.totalTime / 60)} min
                  </div><br/>`;

                // Add step-by-step instructions
                instructions.forEach(step => {
                  dirDiv.innerHTML += `<div style="margin-bottom:4px;">• ${step.text}</div>`;
                });

                // Handle close button
                setTimeout(() => {
                  const closeBtn = document.getElementById('close-directions');
                  if (closeBtn) {
                    closeBtn.addEventListener('click', () => {
                      dirDiv.style.display = 'none';
                      if (routingControl.current) {
                        map.removeControl(routingControl.current);
                        routingControl.current = null;
                      }
                    });
                  }
                }, 0);
              })
              .addTo(map);
            },
            () => {
              alert('Unable to access your location.');
            }
          );
        };
      });
  }, []);

  return (
    <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
      {/* Map container */}
      <div id="map" style={{ height: '100%', width: '100%' }}></div>

      {/* Directions box (initially hidden) */}
      <div id="directions" style={styles.directions}></div>

      {/* Sidebar info panel */}
      <div className="info-panel" style={styles.panel}>
        <h3>UF Campus Locations</h3>
        <div id="location-count" style={styles.locationCount}></div>
        <input
          id="search-input"
          type="text"
          placeholder="Search locations..."
          style={{ width: '100%', marginBottom: 10 }}
        />
        <div id="search-results" style={{ marginTop: 10 }}></div>
        <div className="data-sources" style={styles.dataSources}>
          Data source: OpenStreetMap contributors
        </div>
      </div>

      {/* Map legend */}
      <div className="legend" style={styles.legend}>
        <h4 style={{ marginTop: 0 }}>Legend</h4>
        <div id="legend-items"></div>
      </div>
    </div>
  );
};

// Styles for the layout
const styles = {
  panel: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 300,
    background: 'white',
    padding: 10,
    borderRadius: 5,
    boxShadow: '0 0 10px rgba(0,0,0,0.2)',
    zIndex: 1000,
    maxHeight: '80%',
    overflowY: 'auto',
  },
  locationCount: {
    fontSize: 12,
    color: '#666',
    marginBottom: 10,
  },
  dataSources: {
    fontSize: 10,
    color: '#999',
    marginTop: 5,
  },
  legend: {
    position: 'absolute',
    bottom: 30,
    right: 10,
    background: 'white',
    padding: 10,
    borderRadius: 5,
    boxShadow: '0 0 10px rgba(0,0,0,0.2)',
    zIndex: 1000,
    maxHeight: 300,
    overflowY: 'auto',
  },
  directions: {
    position: 'absolute',
    bottom: 30,
    left: 10,
    background: 'white',
    padding: 10,
    borderRadius: 5,
    boxShadow: '0 0 10px rgba(0,0,0,0.2)',
    zIndex: 1000,
    maxHeight: 300,
    overflowY: 'auto',
    width: 300,
    fontSize: 13,
    color: '#333',
    lineHeight: '1.4em',
    display: 'none',
  }
};

export default CampusMap;

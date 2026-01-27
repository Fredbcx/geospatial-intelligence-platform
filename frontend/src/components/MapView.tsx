import { useState, useMemo, useEffect } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer, PathLayer } from '@deck.gl/layers';
import type { AircraftFeature, TrajectoryFeature } from '../types';
import type { Alert } from '../types/alerts';
import { useAircraftData } from '../hooks/useAircraftData';
import { useAlerts } from '../hooks/useAlerts';
import { fetchAircraftTrajectory } from '../services/api';
import ControlPanel from './ControlPanel';
import { AlertsPanel } from './AlertsPanel';
import { FloatingAlertButton } from './FloatingAlertButton';
import { ViewControlPanel } from './ViewControlPanel';
import { createAlertLayer } from './AlertLayer';
import { cellToLatLng } from 'h3-js';

const INITIAL_VIEW_STATE = {
  longitude: 12.5,
  latitude: 45.0,
  zoom: 5,
  pitch: 0,
  bearing: 0,
};

const ALTITUDE_SCALE = 1500; // 1500x for maximum visual impact

export default function MapView() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  
  const [layerVisibility, setLayerVisibility] = useState({
    aircraft: true,
    trajectories: false,
    heatmap: false,
    alerts: true,
  });

  const [layerOpacity, setLayerOpacity] = useState({
    aircraft: 0.8,
    heatmap: 0.6,
  });

  const [selectedAircraft, setSelectedAircraft] = useState<string | null>(null);
  const [trajectory, setTrajectory] = useState<TrajectoryFeature | null>(null);
  const [loadingTrajectory, setLoadingTrajectory] = useState(false);

  const [alertPanelOpen, setAlertPanelOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  const { aircraftData, heatmapData, loading, refresh } = useAircraftData({
    viewState,
    autoRefresh: true,
    refreshInterval: 30000,
  });

  const { alerts } = useAlerts(true, 30000);
  const safeAlerts = Array.isArray(alerts) ? alerts : [];

  useEffect(() => {
    console.log('🛫 Aircraft count:', aircraftData.length);
    console.log('🚨 Alerts loaded:', safeAlerts.length);
    console.log('🎮 3D Mode:', viewState.pitch > 0 ? `ENABLED (pitch=${viewState.pitch}°, scale=${ALTITUDE_SCALE}x)` : 'DISABLED');
    
    // Debug: Log aircraft altitudes
    if (aircraftData.length > 0 && viewState.pitch > 0) {
      const altitudes = aircraftData
        .map(a => a.properties.altitude)
        .filter(a => a !== null && a !== undefined)
        .sort((a, b) => (b || 0) - (a || 0));
      console.log('📊 Altitude range:', {
        max: altitudes[0],
        min: altitudes[altitudes.length - 1],
        avg: Math.round(altitudes.reduce((sum, a) => sum + (a || 0), 0) / altitudes.length)
      });
    }
  }, [aircraftData, safeAlerts, viewState.pitch]);

  useEffect(() => {
    if (selectedAircraft && layerVisibility.trajectories) {
      setLoadingTrajectory(true);
      fetchAircraftTrajectory(selectedAircraft, 1)
        .then((data) => {
          console.log('📍 Trajectory loaded:', data.properties.count, 'points');
          setTrajectory(data);
        })
        .catch((err) => {
          console.error('Error loading trajectory:', err);
          setTrajectory(null);
        })
        .finally(() => {
          setLoadingTrajectory(false);
        });
    } else {
      setTrajectory(null);
    }
  }, [selectedAircraft, layerVisibility.trajectories]);

  const handleLayerToggle = (layer: keyof typeof layerVisibility) => {
    setLayerVisibility((prev) => ({ ...prev, [layer]: !prev[layer] }));
  };

  const handleOpacityChange = (layer: 'aircraft' | 'heatmap', value: number) => {
    setLayerOpacity((prev) => ({ ...prev, [layer]: value }));
  };

  const handleAlertClick = (alert: Alert) => {
    console.log('🚨 Alert clicked:', alert.id);
    
    setViewState({
      ...viewState,
      longitude: alert.position.coordinates[0],
      latitude: alert.position.coordinates[1],
      zoom: Math.max(viewState.zoom, 8),
      transitionDuration: 1000,
    });

    setSelectedAlert(alert);

    if (alert.aircraft_icao24 && layerVisibility.trajectories) {
      setSelectedAircraft(alert.aircraft_icao24);
    }

    setTimeout(() => {
      setSelectedAlert(null);
    }, 3000);
  };

  const handleViewChange = (newViewState: { pitch: number; bearing: number }) => {
    setViewState((prev) => ({
      ...prev,
      pitch: newViewState.pitch,
      bearing: newViewState.bearing,
      transitionDuration: 500,
    }));
  };

  const handleViewReset = () => {
    setViewState({
      ...INITIAL_VIEW_STATE,
      transitionDuration: 1000,
    });
  };

  const heatmapHexagons = useMemo(() => {
    return heatmapData
      .map((cell) => {
        try {
          const [lat, lon] = cellToLatLng(cell.h3_cell);
          return {
            position: [lon, lat] as [number, number],
            count: cell.count,
            avgAltitude: cell.avg_altitude,
            avgVelocity: cell.avg_velocity,
          };
        } catch (error) {
          return null;
        }
      })
      .filter((hex): hex is NonNullable<typeof hex> => hex !== null);
  }, [heatmapData]);

  const layers = useMemo(() => {
    const result = [];

    // Aircraft layer with 3D altitude
    if (layerVisibility.aircraft && aircraftData.length > 0) {
      result.push(
        new ScatterplotLayer<AircraftFeature>({
          id: 'aircraft-layer',
          data: aircraftData,
          pickable: true,
          opacity: layerOpacity.aircraft,
          stroked: true,
          filled: true,
          radiusScale: 1000,
          radiusMinPixels: 5,
          radiusMaxPixels: 20,
          lineWidthMinPixels: 1,
          
          // 2D position (geographic)
          getPosition: (d) => d.geometry.coordinates,
          
          // 3D elevation with MAXIMUM scaling for visibility
          getElevation: (d) => {
            const altitude = d.properties.altitude || 0;
            return altitude * ALTITUDE_SCALE; // scaling
          },
          
          getRadius: (d) => {
            const altitude = d.properties.altitude || 0;
            return Math.max(100, altitude / 50);
          },
          
          getFillColor: (d) => {
            if (d.properties.icao24 === selectedAircraft) {
              return [255, 255, 0, 255]; // Yellow
            }
            
            const hasAlert = safeAlerts.some(
              alert => alert.aircraft_icao24 === d.properties.icao24 && alert.is_active
            );
            if (hasAlert) {
              return [255, 50, 50, 255]; // Red for alerts
            }
            
            if (d.properties.on_ground) {
              return [100, 100, 100, 255]; // Gray
            }
            
            // Color by altitude
            const altitude = d.properties.altitude || 0;
            if (altitude > 10000) return [255, 100, 100, 255]; // High - red
            if (altitude > 5000) return [255, 200, 100, 255];  // Medium - orange
            return [100, 200, 255, 255]; // Low - blue
          },
          
          getLineColor: (d) => {
            if (d.properties.icao24 === selectedAircraft) {
              return [255, 255, 0, 255];
            }
            return [255, 255, 255, 255];
          },
          
          onClick: (info) => {
            if (info.object) {
              const icao24 = info.object.properties.icao24;
              const altitude = info.object.properties.altitude;
              console.log('✈️ Clicked aircraft:', icao24, '| Altitude:', altitude, 'm | Scaled:', altitude * ALTITUDE_SCALE);
              setSelectedAircraft(icao24);
            }
          },
        })
      );
    }

    // Trajectory layer stays 2D (geographic path only)
    if (layerVisibility.trajectories && trajectory && trajectory.geometry.coordinates.length > 0) {
      console.log('🛤️ Rendering trajectory as 2D path (geographic only)');
      
      result.push(
        new PathLayer({
          id: 'trajectory-layer',
          data: [trajectory],
          pickable: true,
          widthScale: 2,
          widthMinPixels: 3,
          widthMaxPixels: 12,
          // Use only 2D coordinates [lon, lat]
          getPath: (d) => d.geometry.coordinates.map(coord => [coord[0], coord[1]]),
          getColor: [255, 255, 0, 220], // Bright yellow
          getWidth: 5, // Thicker for visibility
        })
      );
    }

    // Heatmap layer (stays 2D)
    if (layerVisibility.heatmap && heatmapHexagons.length > 0) {
      result.push(
        new ScatterplotLayer({
          id: 'heatmap-layer',
          data: heatmapHexagons,
          pickable: true,
          opacity: layerOpacity.heatmap,
          stroked: false,
          filled: true,
          radiusScale: 5000,
          radiusMinPixels: 20,
          radiusMaxPixels: 100,
          getPosition: (d) => d.position,
          getRadius: (d) => d.count * 50,
          getFillColor: (d) => {
            const intensity = Math.min(d.count / 50, 1);
            return [255 * intensity, 100 * (1 - intensity), 100, 150];
          },
        })
      );
    }

    // Alert layer
    if (layerVisibility.alerts && safeAlerts.length > 0) {
      result.push(
        createAlertLayer({
          alerts: safeAlerts.filter(a => a.is_active),
          visible: true,
          onAlertClick: handleAlertClick,
        })
      );
    }

    return result;
  }, [
    aircraftData, 
    heatmapHexagons, 
    trajectory, 
    safeAlerts,
    layerVisibility, 
    layerOpacity, 
    selectedAircraft,
    selectedAlert
  ]);

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        minHeight: '100vh',
      }}
    >
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: newViewState }) => {
          setViewState(newViewState);
        }}
        controller={true}
        layers={layers}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background: '#1a1a2e',
        }}
        parameters={{
          clearColor: [0.1, 0.1, 0.18, 1],
        }}
        getTooltip={({ object, layer }) => {
          if (layer?.id === 'aircraft-layer' && object) {
            const props = object.properties;
            const hasAlert = safeAlerts.some(
              alert => alert.aircraft_icao24 === props.icao24 && alert.is_active
            );
            return {
              html: `
                <div style="padding: 8px; background: rgba(0,0,0,0.9); color: white; border-radius: 4px;">
                  <strong>${props.callsign || props.icao24}</strong>
                  ${hasAlert ? '<span style="color: #ff3333;"> ⚠️ ALERT</span>' : ''}<br/>
                  Country: ${props.origin_country}<br/>
                  <strong style="color: #00ff00;">Altitude: ${props.altitude ? `${Math.round(props.altitude)}m` : 'N/A'}</strong><br/>
                  Speed: ${props.velocity ? `${Math.round(props.velocity * 3.6)} km/h` : 'N/A'}<br/>
                  <em style="color: #ffa500;">Click to show trajectory</em>
                </div>
              `,
              style: { fontSize: '0.8em' },
            };
          }
          
          if (layer?.id === 'trajectory-layer' && object) {
            const props = object.properties;
            return {
              html: `
                <div style="padding: 8px; background: rgba(0,0,0,0.9); color: yellow; border-radius: 4px;">
                  <strong>Geographic Path (2D)</strong><br/>
                  Aircraft: ${props.callsign || props.icao24}<br/>
                  Points: ${props.count}<br/>
                  <em style="font-size: 0.85em;">Shows where aircraft flew<br/>(elevation shown by aircraft marker)</em>
                </div>
              `,
              style: { fontSize: '0.8em' },
            };
          }
          
          if (layer?.id === 'heatmap-layer' && object) {
            return {
              html: `
                <div style="padding: 8px; background: rgba(0,0,0,0.9); color: white; border-radius: 4px;">
                  <strong>Density Cell</strong><br/>
                  Aircraft count: ${object.count}<br/>
                  Avg altitude: ${object.avgAltitude ? `${Math.round(object.avgAltitude)}m` : 'N/A'}<br/>
                  Avg speed: ${object.avgVelocity ? `${Math.round(object.avgVelocity * 3.6)} km/h` : 'N/A'}
                </div>
              `,
              style: { fontSize: '0.8em' },
            };
          }

          if (layer?.id === 'alerts-layer' && object) {
            const alert = object as Alert;
            const severityColors: Record<string, string> = {
              HIGH: '#ff3333',
              MEDIUM: '#ffaa00',
              LOW: '#33ff33',
            };
            return {
              html: `
                <div style="padding: 10px; background: rgba(0,0,0,0.95); color: white; border-radius: 4px; border-left: 4px solid ${severityColors[alert.severity]};">
                  <strong style="color: ${severityColors[alert.severity]};">${alert.severity} ALERT</strong><br/>
                  <em>${alert.alert_type.replace(/_/g, ' ')}</em><br/><br/>
                  <strong>${alert.aircraft_callsign || alert.aircraft_icao24}</strong><br/>
                  ${alert.reason}<br/><br/>
                  ${alert.is_acknowledged ? '<span style="color: #33ff33;">✓ Acknowledged</span>' : '<span style="color: #ffaa00;">⚠ Unacknowledged</span>'}<br/>
                  <em style="color: #aaa; font-size: 0.85em;">Click to center map</em>
                </div>
              `,
              style: { fontSize: '0.85em' },
            };
          }
          
          return null;
        }}
      />

      {/* Left control panel */}
      <ControlPanel
        layers={layerVisibility}
        onLayerToggle={handleLayerToggle}
        opacity={layerOpacity}
        onOpacityChange={handleOpacityChange}
        onRefresh={refresh}
        stats={{
          count: aircraftData.length,
          loading,
        }}
      />

      {/* View Control Panel (top-right) */}
      <ViewControlPanel
        viewState={{ pitch: viewState.pitch, bearing: viewState.bearing }}
        onChange={handleViewChange}
        onReset={handleViewReset}
      />

      {/* Floating Alert Button */}
      <FloatingAlertButton onClick={() => setAlertPanelOpen(true)} />

      {/* Alert Panel Sidebar */}
      <AlertsPanel
        open={alertPanelOpen}
        onClose={() => setAlertPanelOpen(false)}
        onAlertClick={handleAlertClick}
      />

      {/* Loading indicator */}
      {loading && (
        <div
          style={{
            position: 'absolute',
            top: 16,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '8px 16px',
            borderRadius: 4,
            fontSize: '0.9em',
          }}
        >
          Loading...
        </div>
      )}

      {/* Trajectory loading */}
      {loadingTrajectory && (
        <div
          style={{
            position: 'absolute',
            top: 50,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(255,165,0,0.9)',
            color: 'white',
            padding: '8px 16px',
            borderRadius: 4,
            fontSize: '0.9em',
          }}
        >
          Loading trajectory...
        </div>
      )}

      {/* Selected aircraft info */}
      {selectedAircraft && (
        <div
          style={{
            position: 'absolute',
            top: 16,
            left: 16,
            background: 'rgba(255,165,0,0.9)',
            color: 'white',
            padding: '12px 16px',
            borderRadius: 4,
            fontSize: '0.9em',
            cursor: 'pointer',
          }}
          onClick={() => setSelectedAircraft(null)}
        >
          <strong>Selected: {selectedAircraft}</strong><br/>
          {trajectory && `${trajectory.properties.count} points`}<br/>
          <em style={{ fontSize: '0.8em' }}>Click to deselect</em>
        </div>
      )}

      {/* Selected alert indicator */}
      {selectedAlert && (
        <div
          style={{
            position: 'absolute',
            top: selectedAircraft ? 100 : 16,
            left: 16,
            background: 'rgba(255,50,50,0.95)',
            color: 'white',
            padding: '12px 16px',
            borderRadius: 4,
            fontSize: '0.9em',
            boxShadow: '0 0 20px rgba(255,50,50,0.5)',
            animation: 'pulse 1.5s ease-in-out infinite',
          }}
        >
          <strong>⚠️ ALERT: {selectedAlert.severity}</strong><br/>
          {selectedAlert.aircraft_callsign || selectedAlert.aircraft_icao24}<br/>
          <em style={{ fontSize: '0.8em' }}>{selectedAlert.reason}</em>
        </div>
      )}

      {/* Stats footer */}
      <div
        style={{
          position: 'absolute',
          bottom: 10,
          left: 10,
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: 4,
          fontSize: '0.85em',
        }}
      >
        ✈️ {aircraftData.length} aircraft | 🚨 {safeAlerts.filter(a => a.is_active).length} alerts 
        {viewState.pitch > 0 && (
          <span style={{ color: '#6366f1', fontWeight: 'bold' }}>
            {' '}| 🎮 3D MODE (pitch {viewState.pitch}°, {ALTITUDE_SCALE}x scale)
          </span>
        )}
        {' '}| 🎨 {layers.length} layers
      </div>

      {/* Pulsing animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.8;
            transform: scale(1.02);
          }
        }
      `}</style>
    </div>
  );
}
import { useState, useMemo, useEffect } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer, PathLayer } from '@deck.gl/layers';
import type { AircraftFeature, TrajectoryFeature } from '../types';
import { useAircraftData } from '../hooks/useAircraftData';
import { fetchAircraftTrajectory } from '../services/api';
import ControlPanel from './ControlPanel';
import { cellToLatLng } from 'h3-js';

const INITIAL_VIEW_STATE = {
  longitude: 12.5,
  latitude: 45.0,
  zoom: 5,
  pitch: 0,
  bearing: 0,
};

export default function MapView() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  
  const [layerVisibility, setLayerVisibility] = useState({
    aircraft: true,
    trajectories: false,
    heatmap: false,
  });

  const [layerOpacity, setLayerOpacity] = useState({
    aircraft: 0.8,
    heatmap: 0.6,
  });

  // Selected aircraft for trajectory
  const [selectedAircraft, setSelectedAircraft] = useState<string | null>(null);
  const [trajectory, setTrajectory] = useState<TrajectoryFeature | null>(null);
  const [loadingTrajectory, setLoadingTrajectory] = useState(false);

  const { aircraftData, heatmapData, loading, refresh } = useAircraftData({
    viewState,
    autoRefresh: true,
    refreshInterval: 30000,
  });

  useEffect(() => {
    console.log('🛫 Aircraft count:', aircraftData.length);
  }, [aircraftData]);

  // Load trajectory when aircraft selected
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

    // Aircraft layer
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
          getPosition: (d) => d.geometry.coordinates,
          getRadius: (d) => {
            const altitude = d.properties.altitude || 0;
            return Math.max(100, altitude / 50);
          },
          getFillColor: (d) => {
            // Highlight selected aircraft
            if (d.properties.icao24 === selectedAircraft) {
              return [255, 255, 0, 255]; // Yellow
            }
            
            if (d.properties.on_ground) {
              return [100, 100, 100, 255];
            }
            const altitude = d.properties.altitude || 0;
            if (altitude > 10000) return [255, 100, 100, 255];
            if (altitude > 5000) return [255, 200, 100, 255];
            return [100, 200, 255, 255];
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
              console.log('Clicked aircraft:', icao24);
              setSelectedAircraft(icao24);
            }
          },
        })
      );
    }

    // Trajectory layer
    if (layerVisibility.trajectories && trajectory && trajectory.geometry.coordinates.length > 0) {
      result.push(
        new PathLayer({
          id: 'trajectory-layer',
          data: [trajectory],
          pickable: true,
          widthScale: 2,
          widthMinPixels: 2,
          widthMaxPixels: 10,
          getPath: (d) => d.geometry.coordinates,
          getColor: [255, 255, 0, 200], // Yellow with transparency
          getWidth: 3,
        })
      );
    }

    // Heatmap layer
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

    return result;
  }, [aircraftData, heatmapHexagons, trajectory, layerVisibility, layerOpacity, selectedAircraft]);

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
            return {
              html: `
                <div style="padding: 8px; background: rgba(0,0,0,0.9); color: white; border-radius: 4px;">
                  <strong>${props.callsign || props.icao24}</strong><br/>
                  Country: ${props.origin_country}<br/>
                  Altitude: ${props.altitude ? `${Math.round(props.altitude)}m` : 'N/A'}<br/>
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
                  <strong>Trajectory</strong><br/>
                  Aircraft: ${props.callsign || props.icao24}<br/>
                  Points: ${props.count}
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
          return null;
        }}
      />

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
        ✈️ {aircraftData.length} aircraft | 🎨 {layers.length} layers
      </div>
    </div>
  );
}
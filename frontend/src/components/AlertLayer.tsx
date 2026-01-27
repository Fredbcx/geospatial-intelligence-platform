import { IconLayer } from '@deck.gl/layers';
import type { Alert } from '../types/alerts';
import { getSeverityColor } from '../hooks/useAlerts';

export interface AlertLayerProps {
  alerts: Alert[];
  visible: boolean;
  onAlertClick?: (alert: Alert) => void;
}

// Icon mapping - we'll use simple circle with different colors
const ICON_MAPPING = {
  marker: {
    x: 0,
    y: 0,
    width: 128,
    height: 128,
    anchorY: 128,
    mask: false,
  },
};

export const createAlertLayer = ({
  alerts,
  visible,
  onAlertClick,
}: AlertLayerProps): IconLayer<Alert> => {
  return new IconLayer<Alert>({
    id: 'alerts-layer',
    data: alerts,
    visible,
    pickable: true,
    getPosition: (d) => [
      d.position.coordinates[0], // longitude
      d.position.coordinates[1], // latitude
    ],
    getIcon: () => 'marker',
    getSize: 40,
    getColor: (d) => {
      const baseColor = getSeverityColor(d.severity);
      // Add pulsing effect for unacknowledged alerts by varying alpha
      const alpha = d.is_acknowledged ? 200 : 255;
      return [...baseColor, alpha] as [number, number, number, number];
    },
    iconAtlas: createIconAtlas(),
    iconMapping: ICON_MAPPING,
    sizeScale: 1,
    sizeMinPixels: 20,
    sizeMaxPixels: 60,
    onClick: (info) => {
      if (info.object && onAlertClick) {
        onAlertClick(info.object);
      }
    },
    // Add animation for unacknowledged alerts
    updateTriggers: {
      getColor: [alerts.map(a => a.is_acknowledged).join(',')],
    },
  });
};

// Create a simple icon atlas with a warning symbol
const createIconAtlas = (): string => {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  
  if (ctx) {
    // Draw warning triangle
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    
    // Triangle shape
    ctx.moveTo(64, 20); // top
    ctx.lineTo(100, 100); // bottom right
    ctx.lineTo(28, 100); // bottom left
    ctx.closePath();
    ctx.fill();
    
    // Exclamation mark
    ctx.fillStyle = '#000000';
    
    // Line of exclamation
    ctx.fillRect(58, 40, 12, 35);
    
    // Dot of exclamation
    ctx.beginPath();
    ctx.arc(64, 88, 6, 0, 2 * Math.PI);
    ctx.fill();
  }
  
  return canvas.toDataURL();
};

// Helper to create pulsing animation effect
export const createPulsingEffect = (timestamp: number, acknowledged: boolean): number => {
  if (acknowledged) return 1.0;
  
  // Pulse between 0.7 and 1.0 every 2 seconds
  const pulseSpeed = 2000;
  const normalized = (timestamp % pulseSpeed) / pulseSpeed;
  const sinWave = Math.sin(normalized * Math.PI * 2);
  return 0.7 + (sinWave + 1) * 0.15; // Maps [-1, 1] to [0.7, 1.0]
};
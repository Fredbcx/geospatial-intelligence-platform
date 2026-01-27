import { useState, useMemo } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Divider,
  Chip,
  Button,
  FormControl,
  Select,
  MenuItem,
  Alert as MuiAlert,
  CircularProgress,
} from '@mui/material';
import {
  Close as CloseIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useAlerts, getAlertTypeLabel, formatAlertTime } from '../hooks/useAlerts';
import type { Alert, AlertSeverity, AlertType } from '../types/alerts';

interface AlertsPanelProps {
  open: boolean;
  onClose: () => void;
  onAlertClick?: (alert: Alert) => void;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({ open, onClose, onAlertClick }) => {
  const { alerts, stats, isLoading, error, acknowledgeAlert, resolveAlert, filters, setFilters } = useAlerts();

  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  // Filter alerts based on selections
  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      if (selectedSeverity !== 'all' && alert.severity !== selectedSeverity) {
        return false;
      }
      if (selectedType !== 'all' && alert.type !== selectedType) {
        return false;
      }
      return true;
    });
  }, [alerts, selectedSeverity, selectedType]);

  const handleAcknowledge = async (alertId: number) => {
    try {
      await acknowledgeAlert(alertId);
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolve = async (alertId: number) => {
    try {
      await resolveAlert(alertId);
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const getSeverityIcon = (severity: AlertSeverity) => {
    switch (severity) {
      case 'HIGH':
        return <WarningIcon sx={{ color: '#ef4444' }} />;
      case 'MEDIUM':
        return <InfoIcon sx={{ color: '#f59e0b' }} />;
      case 'LOW':
        return <CheckCircleIcon sx={{ color: '#10b981' }} />;
      default:
        return <InfoIcon sx={{ color: '#6b7280' }} />;
    }
  };

  const getSeverityColor = (severity: AlertSeverity): string => {
    switch (severity) {
      case 'HIGH':
        return '#ef4444'; // Red
      case 'MEDIUM':
        return '#f59e0b'; // Orange/Yellow
      case 'LOW':
        return '#10b981'; // Green
      default:
        return '#6b7280'; // Gray
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: { xs: '100%', sm: 400 },
          bgcolor: '#1e1e2e', // Dark background
          color: '#e5e5e5', // Light text
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          bgcolor: '#252535',
          borderBottom: '1px solid #3a3a4a',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon sx={{ color: '#ef4444' }} />
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#ffffff' }}>
            Active Alerts
          </Typography>
        </Box>
        <IconButton onClick={onClose} sx={{ color: '#e5e5e5' }}>
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Stats Summary */}
      {stats && (
        <Box
          sx={{
            p: 2,
            display: 'flex',
            justifyContent: 'space-around',
            bgcolor: '#252535',
            borderBottom: '1px solid #3a3a4a',
          }}
        >
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" sx={{ color: '#ef4444', fontWeight: 700 }}>
              {stats.high}
            </Typography>
            <Typography variant="caption" sx={{ color: '#d1d1d1', fontWeight: 500 }}>
              High
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" sx={{ color: '#f59e0b', fontWeight: 700 }}>
              {stats.medium}
            </Typography>
            <Typography variant="caption" sx={{ color: '#d1d1d1', fontWeight: 500 }}>
              Medium
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" sx={{ color: '#10b981', fontWeight: 700 }}>
              {stats.low}
            </Typography>
            <Typography variant="caption" sx={{ color: '#d1d1d1', fontWeight: 500 }}>
              Low
            </Typography>
          </Box>
        </Box>
      )}

      {/* Filters */}
      <Box sx={{ p: 2, bgcolor: '#1e1e2e', borderBottom: '1px solid #3a3a4a' }}>
        <Typography variant="subtitle2" sx={{ mb: 1, color: '#ffffff', fontWeight: 600 }}>
          Filters
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <FormControl size="small" sx={{ flex: 1 }}>
            <Select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              sx={{
                bgcolor: '#252535',
                color: '#e5e5e5',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#3a3a4a',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#4a4a5a',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#6366f1',
                },
                '& .MuiSvgIcon-root': {
                  color: '#e5e5e5',
                },
              }}
            >
              <MenuItem value="all">All Severities</MenuItem>
              <MenuItem value="HIGH">High</MenuItem>
              <MenuItem value="MEDIUM">Medium</MenuItem>
              <MenuItem value="LOW">Low</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ flex: 1 }}>
            <Select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              sx={{
                bgcolor: '#252535',
                color: '#e5e5e5',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#3a3a4a',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#4a4a5a',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#6366f1',
                },
                '& .MuiSvgIcon-root': {
                  color: '#e5e5e5',
                },
              }}
            >
              <MenuItem value="all">All Types</MenuItem>
              <MenuItem value="SPEED_ANOMALY">Speed Anomaly</MenuItem>
              <MenuItem value="ALTITUDE_ANOMALY">Altitude Anomaly</MenuItem>
              <MenuItem value="TRAJECTORY_DEVIATION">Trajectory Deviation</MenuItem>
              <MenuItem value="GEOFENCE_VIOLATION">Geofence Violation</MenuItem>
              <MenuItem value="UNUSUAL_PATTERN">Unusual Pattern</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress sx={{ color: '#6366f1' }} />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Box sx={{ p: 2 }}>
          <MuiAlert severity="error" sx={{ bgcolor: '#7f1d1d', color: '#fecaca' }}>
            {error}
          </MuiAlert>
        </Box>
      )}

      {/* Alerts List */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          bgcolor: '#1e1e2e',
        }}
      >
        {filteredAlerts.length === 0 && !isLoading && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircleIcon sx={{ fontSize: 48, color: '#10b981', mb: 2 }} />
            <Typography variant="body1" sx={{ color: '#d1d1d1' }}>
              No active alerts
            </Typography>
          </Box>
        )}

        {filteredAlerts.map((alert) => (
          <Box
            key={alert.id}
            onClick={() => onAlertClick?.(alert)}
            sx={{
              mb: 2,
              p: 2,
              borderRadius: 2,
              bgcolor: '#252535',
              border: `2px solid ${getSeverityColor(alert.severity)}`,
              cursor: 'pointer',
              transition: 'all 0.2s',
              '&:hover': {
                bgcolor: '#2a2a3a',
                transform: 'translateX(-4px)',
                boxShadow: `0 4px 12px ${getSeverityColor(alert.severity)}40`,
              },
            }}
          >
            {/* Alert Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {getSeverityIcon(alert.severity)}
              <Chip
                label={alert.severity}
                size="small"
                sx={{
                  bgcolor: getSeverityColor(alert.severity),
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '0.7rem',
                }}
              />
              <Typography variant="caption" sx={{ ml: 'auto', color: '#a1a1a1', fontWeight: 500 }}>
                {formatAlertTime(alert.detected_at)}
              </Typography>
            </Box>

            {/* Alert Type */}
            <Typography variant="subtitle2" sx={{ color: '#ffffff', fontWeight: 600, mb: 0.5 }}>
              {getAlertTypeLabel(alert.type)}
            </Typography>

            {/* Aircraft Info */}
            <Typography variant="body2" sx={{ color: '#e5e5e5', fontWeight: 600, mb: 1 }}>
              {alert.aircraft_callsign || alert.aircraft_icao24}
            </Typography>

            {/* Reason */}
            <Typography variant="body2" sx={{ color: '#d1d1d1', mb: 2, lineHeight: 1.5 }}>
              {alert.reason}
            </Typography>

            {/* Status Badge */}
            {alert.is_acknowledged && (
              <Chip
                icon={<CheckCircleIcon />}
                label="Acknowledged"
                size="small"
                sx={{
                  mb: 1,
                  bgcolor: '#065f46',
                  color: '#d1fae5',
                  '& .MuiChip-icon': {
                    color: '#d1fae5',
                  },
                }}
              />
            )}

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
              {!alert.is_acknowledged && (
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<CheckCircleIcon />}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAcknowledge(alert.id);
                  }}
                  sx={{
                    flex: 1,
                    borderColor: '#3b82f6',
                    color: '#3b82f6',
                    '&:hover': {
                      borderColor: '#2563eb',
                      bgcolor: '#1e3a8a20',
                    },
                  }}
                >
                  Acknowledge
                </Button>
              )}
              <Button
                size="small"
                variant="contained"
                onClick={(e) => {
                  e.stopPropagation();
                  handleResolve(alert.id);
                }}
                sx={{
                  flex: 1,
                  bgcolor: '#16a34a',
                  color: '#ffffff',
                  '&:hover': {
                    bgcolor: '#15803d',
                  },
                }}
              >
                Resolve
              </Button>
            </Box>
          </Box>
        ))}
      </Box>

      {/* Footer */}
      <Box
        sx={{
          p: 2,
          bgcolor: '#252535',
          borderTop: '1px solid #3a3a4a',
          textAlign: 'center',
        }}
      >
        <Typography variant="caption" sx={{ color: '#a1a1a1', fontWeight: 500 }}>
          Showing {filteredAlerts.length} of {alerts.length} alerts
        </Typography>
      </Box>
    </Drawer>
  );
};
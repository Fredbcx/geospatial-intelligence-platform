import React from 'react';
import { Fab, Badge, Tooltip, Box } from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';
import { useAlerts } from '../hooks/useAlerts';

interface FloatingAlertButtonProps {
  onClick: () => void;
}

export const FloatingAlertButton: React.FC<FloatingAlertButtonProps> = ({ onClick }) => {
  const { stats, alerts } = useAlerts();

  const safeAlerts = Array.isArray(alerts) ? alerts : [];
  
  console.log('FloatingAlertButton - alerts:', safeAlerts.length, 'stats:', stats);

  // Count unacknowledged alerts
  const unacknowledgedCount = safeAlerts.filter(
    a => !a.is_acknowledged && a.is_active
  ).length;
  
  const highSeverityCount = safeAlerts.filter(
    a => a.severity === 'HIGH' && a.is_active
  ).length;

  // Determine button color based on severity
  const getButtonColor = () => {
    if (highSeverityCount > 0) return 'error';
    if (stats && stats.by_severity.MEDIUM > 0) return 'warning';
    if (stats && stats.by_severity.LOW > 0) return 'info';
    return 'default';
  };

  // Calculate badge count
  const badgeCount = stats?.active_count || safeAlerts.filter(a => a.is_active).length || 0;

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 20,
        right: 20,
        zIndex: 1000,
      }}
    >
      <Tooltip title="View Active Alerts" placement="left">
        <Badge
          badgeContent={badgeCount}
          color="error"
          overlap="circular"
          max={99}
          sx={{
            '& .MuiBadge-badge': {
              fontSize: '0.9rem',
              fontWeight: 'bold',
              minWidth: 24,
              height: 24,
              animation: unacknowledgedCount > 0 ? 'pulse 2s ease-in-out infinite' : 'none',
              '@keyframes pulse': {
                '0%': {
                  transform: 'scale(1)',
                  opacity: 1,
                },
                '50%': {
                  transform: 'scale(1.1)',
                  opacity: 0.8,
                },
                '100%': {
                  transform: 'scale(1)',
                  opacity: 1,
                },
              },
            },
          }}
        >
          <Fab
            color={getButtonColor()}
            onClick={onClick}
            size="large"
            sx={{
              boxShadow: 3,
              '&:hover': {
                boxShadow: 6,
                transform: 'scale(1.05)',
              },
              transition: 'all 0.2s ease-in-out',
            }}
          >
            <WarningIcon sx={{ fontSize: 32 }} />
          </Fab>
        </Badge>
      </Tooltip>
    </Box>
  );
};
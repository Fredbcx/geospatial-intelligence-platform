import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Slider,
  Button,
  IconButton,
  Tooltip,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import {
  ThreeDRotation as ThreeDIcon,
  ViewInAr as TwoDIcon,
  RotateLeft as RotateLeftIcon,
  RotateRight as RotateRightIcon,
  Refresh as ResetIcon,
  KeyboardArrowDown as PitchDownIcon,
  KeyboardArrowUp as PitchUpIcon,
} from '@mui/icons-material';

export interface ViewState {
  pitch: number;
  bearing: number;
}

interface ViewControlPanelProps {
  viewState: ViewState;
  onChange: (viewState: ViewState) => void;
  onReset: () => void;
}

const STORAGE_KEY = 'geoint-view-preferences';

export const ViewControlPanel: React.FC<ViewControlPanelProps> = ({
  viewState,
  onChange,
  onReset,
}) => {
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  const [expanded, setExpanded] = useState(true);

  // Load saved preferences on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const prefs = JSON.parse(saved);
        onChange(prefs);
        setViewMode(prefs.pitch > 0 ? '3d' : '2d');
      }
    } catch (err) {
      console.error('Failed to load view preferences:', err);
    }
  }, []);

  // Save preferences when they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(viewState));
    } catch (err) {
      console.error('Failed to save view preferences:', err);
    }
  }, [viewState]);

  const handleModeChange = (
    event: React.MouseEvent<HTMLElement>,
    newMode: '2d' | '3d' | null
  ) => {
    if (newMode === null) return;
    
    setViewMode(newMode);
    
    if (newMode === '2d') {
      // Switch to 2D: pitch = 0, keep bearing
      onChange({ ...viewState, pitch: 0 });
    } else {
      // Switch to 3D: pitch = 45, keep bearing
      onChange({ ...viewState, pitch: 45 });
    }
  };

  const handlePitchChange = (event: Event, value: number | number[]) => {
    const newPitch = value as number;
    onChange({ ...viewState, pitch: newPitch });
    setViewMode(newPitch > 0 ? '3d' : '2d');
  };

  const handleBearingChange = (event: Event, value: number | number[]) => {
    onChange({ ...viewState, bearing: value as number });
  };

  const handleRotateLeft = () => {
    const newBearing = (viewState.bearing - 45 + 360) % 360;
    onChange({ ...viewState, bearing: newBearing });
  };

  const handleRotateRight = () => {
    const newBearing = (viewState.bearing + 45) % 360;
    onChange({ ...viewState, bearing: newBearing });
  };

  const handleReset = () => {
    setViewMode('2d');
    onReset();
  };

  return (
    <Paper
      elevation={3}
      sx={{
        position: 'absolute',
        top: 16,
        right: 80, // Next to alerts button
        width: expanded ? 280 : 60,
        bgcolor: 'rgba(30, 30, 46, 0.95)',
        backdropFilter: 'blur(10px)',
        color: '#e5e5e5',
        p: expanded ? 2 : 1,
        transition: 'all 0.3s ease',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        '&:hover': {
          border: '1px solid rgba(99, 102, 241, 0.5)',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: expanded ? 2 : 0,
        }}
      >
        {expanded && (
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#fff' }}>
            View Controls
          </Typography>
        )}
        <Tooltip title={expanded ? 'Collapse' : 'Expand'}>
          <IconButton
            size="small"
            onClick={() => setExpanded(!expanded)}
            sx={{ color: '#e5e5e5' }}
          >
            {expanded ? <TwoDIcon /> : <ThreeDIcon />}
          </IconButton>
        </Tooltip>
      </Box>

      {expanded && (
        <>
          {/* 2D/3D Toggle */}
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={handleModeChange}
            fullWidth
            size="small"
            sx={{
              mb: 2,
              '& .MuiToggleButton-root': {
                color: '#e5e5e5',
                borderColor: 'rgba(99, 102, 241, 0.3)',
                '&.Mui-selected': {
                  bgcolor: 'rgba(99, 102, 241, 0.3)',
                  color: '#6366f1',
                  '&:hover': {
                    bgcolor: 'rgba(99, 102, 241, 0.4)',
                  },
                },
                '&:hover': {
                  bgcolor: 'rgba(99, 102, 241, 0.1)',
                },
              },
            }}
          >
            <ToggleButton value="2d">
              <TwoDIcon sx={{ mr: 1, fontSize: 18 }} />
              2D
            </ToggleButton>
            <ToggleButton value="3d">
              <ThreeDIcon sx={{ mr: 1, fontSize: 18 }} />
              3D
            </ToggleButton>
          </ToggleButtonGroup>

          <Divider sx={{ mb: 2, borderColor: 'rgba(99, 102, 241, 0.2)' }} />

          {/* Pitch Control */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" sx={{ color: '#d1d1d1', fontWeight: 500 }}>
                Pitch (Tilt)
              </Typography>
              <Typography variant="caption" sx={{ color: '#6366f1', fontWeight: 600 }}>
                {viewState.pitch}°
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Tooltip title="Decrease tilt">
                <IconButton
                  size="small"
                  onClick={() => handlePitchChange({} as Event, Math.max(0, viewState.pitch - 5))}
                  sx={{ color: '#e5e5e5' }}
                >
                  <PitchDownIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Slider
                value={viewState.pitch}
                onChange={handlePitchChange}
                min={0}
                max={60}
                step={1}
                sx={{
                  flex: 1,
                  color: '#6366f1',
                  '& .MuiSlider-thumb': {
                    bgcolor: '#6366f1',
                    '&:hover, &.Mui-focusVisible': {
                      boxShadow: '0 0 0 8px rgba(99, 102, 241, 0.16)',
                    },
                  },
                  '& .MuiSlider-track': {
                    bgcolor: '#6366f1',
                  },
                  '& .MuiSlider-rail': {
                    bgcolor: 'rgba(99, 102, 241, 0.3)',
                  },
                }}
              />
              <Tooltip title="Increase tilt">
                <IconButton
                  size="small"
                  onClick={() => handlePitchChange({} as Event, Math.min(60, viewState.pitch + 5))}
                  sx={{ color: '#e5e5e5' }}
                >
                  <PitchUpIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {/* Bearing Control */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" sx={{ color: '#d1d1d1', fontWeight: 500 }}>
                Bearing (Rotation)
              </Typography>
              <Typography variant="caption" sx={{ color: '#f59e0b', fontWeight: 600 }}>
                {viewState.bearing}°
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Tooltip title="Rotate left 45°">
                <IconButton
                  size="small"
                  onClick={handleRotateLeft}
                  sx={{ color: '#e5e5e5' }}
                >
                  <RotateLeftIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Slider
                value={viewState.bearing}
                onChange={handleBearingChange}
                min={0}
                max={360}
                step={1}
                sx={{
                  flex: 1,
                  color: '#f59e0b',
                  '& .MuiSlider-thumb': {
                    bgcolor: '#f59e0b',
                    '&:hover, &.Mui-focusVisible': {
                      boxShadow: '0 0 0 8px rgba(245, 158, 11, 0.16)',
                    },
                  },
                  '& .MuiSlider-track': {
                    bgcolor: '#f59e0b',
                  },
                  '& .MuiSlider-rail': {
                    bgcolor: 'rgba(245, 158, 11, 0.3)',
                  },
                }}
              />
              <Tooltip title="Rotate right 45°">
                <IconButton
                  size="small"
                  onClick={handleRotateRight}
                  sx={{ color: '#e5e5e5' }}
                >
                  <RotateRightIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          <Divider sx={{ mb: 2, borderColor: 'rgba(99, 102, 241, 0.2)' }} />

          {/* Reset Button */}
          <Button
            fullWidth
            size="small"
            startIcon={<ResetIcon />}
            onClick={handleReset}
            sx={{
              color: '#e5e5e5',
              borderColor: 'rgba(99, 102, 241, 0.3)',
              '&:hover': {
                borderColor: 'rgba(99, 102, 241, 0.5)',
                bgcolor: 'rgba(99, 102, 241, 0.1)',
              },
            }}
            variant="outlined"
          >
            Reset View
          </Button>

          {/* Info Text */}
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              mt: 2,
              color: '#a1a1a1',
              textAlign: 'center',
              fontSize: '0.7rem',
            }}
          >
            Use mouse/trackpad to pan & zoom
          </Typography>
        </>
      )}
    </Paper>
  );
};
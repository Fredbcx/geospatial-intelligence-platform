import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Switch,
  FormControlLabel,
  Slider,
  Divider,
  IconButton,
  Button, // ✅ Aggiungi Button
  Collapse,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  Refresh,
} from '@mui/icons-material';

interface ControlPanelProps {
  layers: {
    aircraft: boolean;
    trajectories: boolean;
    heatmap: boolean;
  };
  onLayerToggle: (layer: keyof ControlPanelProps['layers']) => void;
  opacity: {
    aircraft: number;
    heatmap: number;
  };
  onOpacityChange: (layer: 'aircraft' | 'heatmap', value: number) => void;
  onRefresh: () => void;
  stats?: {
    count: number;
    loading: boolean;
  };
}

export default function ControlPanel({
  layers,
  onLayerToggle,
  opacity,
  onOpacityChange,
  onRefresh,
  stats,
}: ControlPanelProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Paper
      elevation={3}
      sx={{
        position: 'absolute',
        top: 16,
        right: 16,
        width: collapsed ? 48 : 280,
        maxHeight: 'calc(100vh - 32px)',
        overflow: 'auto',
        transition: 'width 0.3s ease',
        bgcolor: 'rgba(0, 0, 0, 0.85)',
        color: 'white',
      }}
    >
      <Box sx={{ p: 2 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          {!collapsed && (
            <Typography variant="h6" component="h2">
              Controls
            </Typography>
          )}
          <IconButton
            size="small"
            onClick={() => setCollapsed(!collapsed)}
            sx={{ color: 'white' }}
          >
            {collapsed ? <ChevronLeft /> : <ChevronRight />}
          </IconButton>
        </Box>

        <Collapse in={!collapsed}>
          {/* Stats */}
          {stats && (
            <>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Aircraft Visible
                </Typography>
                <Typography variant="h4">
                  {stats.loading ? '...' : stats.count.toLocaleString()}
                </Typography>
              </Box>
              <Divider sx={{ my: 2, bgcolor: 'rgba(255,255,255,0.1)' }} />
            </>
          )}

          {/* Refresh Button - FIX: Usa Button invece di IconButton con fullWidth */}
          <Box sx={{ mb: 2 }}>
            <Button
              fullWidth
              onClick={onRefresh}
              disabled={stats?.loading}
              startIcon={<Refresh />}
              sx={{
                color: 'white',
                border: '1px solid rgba(255,255,255,0.2)',
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.1)',
                },
              }}
            >
              Refresh Data
            </Button>
          </Box>

          <Divider sx={{ my: 2, bgcolor: 'rgba(255,255,255,0.1)' }} />

          {/* Layer Toggles */}
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Layers
          </Typography>

          <FormControlLabel
            control={
              <Switch
                checked={layers.aircraft}
                onChange={() => onLayerToggle('aircraft')}
                color="primary"
              />
            }
            label="Aircraft Points"
          />

          {layers.aircraft && (
            <Box sx={{ px: 2, mb: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Opacity
              </Typography>
              <Slider
                value={opacity.aircraft}
                onChange={(_, value) => onOpacityChange('aircraft', value as number)}
                min={0}
                max={1}
                step={0.1}
                valueLabelDisplay="auto"
                size="small"
              />
            </Box>
          )}

          <FormControlLabel
            control={
              <Switch
                checked={layers.trajectories}
                onChange={() => onLayerToggle('trajectories')}
                color="primary"
              />
            }
            label="Trajectories"
          />

          <FormControlLabel
            control={
              <Switch
                checked={layers.heatmap}
                onChange={() => onLayerToggle('heatmap')}
                color="primary"
              />
            }
            label="Density Heatmap"
          />

          {layers.heatmap && (
            <Box sx={{ px: 2, mb: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Opacity
              </Typography>
              <Slider
                value={opacity.heatmap}
                onChange={(_, value) => onOpacityChange('heatmap', value as number)}
                min={0}
                max={1}
                step={0.1}
                valueLabelDisplay="auto"
                size="small"
              />
            </Box>
          )}

          <Divider sx={{ my: 2, bgcolor: 'rgba(255,255,255,0.1)' }} />

          {/* Legend */}
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Altitude Legend
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  bgcolor: 'rgb(255,100,100)',
                  border: '1px solid white',
                }}
              />
              <Typography variant="caption">&gt; 10,000m</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  bgcolor: 'rgb(255,200,100)',
                  border: '1px solid white',
                }}
              />
              <Typography variant="caption">5,000-10,000m</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  bgcolor: 'rgb(100,200,255)',
                  border: '1px solid white',
                }}
              />
              <Typography variant="caption">&lt; 5,000m</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  bgcolor: 'rgb(100,100,100)',
                  border: '1px solid white',
                }}
              />
              <Typography variant="caption">On ground</Typography>
            </Box>
          </Box>
        </Collapse>
      </Box>
    </Paper>
  );
}
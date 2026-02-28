import React, { useState } from 'react';
import { Box, Typography, Collapse, Paper, Chip } from '@mui/material';
import { ExpandMore, ExpandLess, ElectricalServices, CheckCircle, ErrorOutline, Schedule } from '@mui/icons-material';
import type { WorkflowTrace } from '../../types';
import { COLORS } from '../../../styles/colors';

interface WorkflowTraceProps {
  trace: WorkflowTrace;
  defaultExpanded?: boolean;
}

export default function WorkflowTracePanel({ trace, defaultExpanded = false }: WorkflowTraceProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const formatDuration = (ms?: number): string => {
    if (!ms) return '—';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <Paper
      sx={{
        mt: 2,
        mb: 1,
        background: 'linear-gradient(135deg, #f9f5ff 0%, #f5faff 100%)',
        border: `1px solid ${COLORS.dividerOnLight}`,
        borderRadius: '12px',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Box
        onClick={() => setExpanded(!expanded)}
        sx={{
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          backgroundColor: 'rgba(59, 130, 246, 0.08)',
          borderBottom: expanded ? `1px solid ${COLORS.dividerOnLight}` : 'none',
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: 'rgba(59, 130, 246, 0.12)',
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ElectricalServices sx={{ color: '#3b82f6' }} />
          <Typography sx={{ fontWeight: 600, color: '#3b82f6', fontSize: '0.95rem' }}>
            ⚙️ Detalles del Procesamiento
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={`${trace.total_steps} pasos`}
            size="small"
            icon={trace.validation_passed ? <CheckCircle sx={{ fontSize: '1rem' }} /> : <ErrorOutline sx={{ fontSize: '1rem' }} />}
            sx={{
              backgroundColor: trace.validation_passed ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: trace.validation_passed ? '#10b981' : '#ef4444',
              fontWeight: 500,
            }}
          />
          {expanded ? <ExpandLess /> : <ExpandMore />}
        </Box>
      </Box>

      {/* Expanded Content */}
      <Collapse in={expanded} timeout="auto">
        <Box sx={{ px: 2, py: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Summary */}
          <Box sx={{ pb: 1.5, borderBottom: `1px solid ${COLORS.dividerOnLight}` }}>
            <Typography sx={{ fontWeight: 600, fontSize: '0.9rem', color: COLORS.textOnLightPrimary, mb: 1 }}>
              Resumen de Ejecución
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 1.5 }}>
              <Box>
                <Typography sx={{ fontSize: '0.75rem', color: '#999', textTransform: 'uppercase' }}>
                  Tiempo Total
                </Typography>
                <Typography sx={{ fontSize: '1.1rem', fontWeight: 700, color: '#3b82f6' }}>
                  {formatDuration(trace.execution_time_ms)}
                </Typography>
              </Box>
              <Box>
                <Typography sx={{ fontSize: '0.75rem', color: '#999', textTransform: 'uppercase' }}>
                  Herramientas Usadas
                </Typography>
                <Typography sx={{ fontSize: '1.1rem', fontWeight: 700, color: '#3b82f6' }}>
                  {trace.tools_used.length}
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Validation Details */}
          {trace.validation_details && (
            <Box sx={{ p: 1.5, backgroundColor: trace.validation_passed ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)', borderLeft: `4px solid ${trace.validation_passed ? '#10b981' : '#ef4444'}`, borderRadius: '6px' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                {trace.validation_passed ? (
                  <CheckCircle sx={{ color: '#10b981', fontSize: '1.2rem' }} />
                ) : (
                  <ErrorOutline sx={{ color: '#ef4444', fontSize: '1.2rem' }} />
                )}
                <Typography sx={{ fontWeight: 600, fontSize: '0.95rem', color: COLORS.textOnLightPrimary }}>
                  {trace.validation_passed ? '✅ Validación Pasada' : '❌ Validación Fallida'}
                </Typography>
              </Box>
              {trace.validation_details.reason && (
                <Typography sx={{ fontSize: '0.85rem', color: COLORS.textOnLightSecondary }}>
                  {trace.validation_details.reason}
                </Typography>
              )}
            </Box>
          )}

          {/* Tools List */}
          <Box>
            <Typography sx={{ fontWeight: 600, fontSize: '0.9rem', color: COLORS.textOnLightPrimary, mb: 1 }}>
              Herramientas Ejecutadas
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
              {trace.tool_traces.map((tool, idx) => (
                <Box key={idx} sx={{ p: 1, backgroundColor: '#f9f9f9', border: `1px solid ${COLORS.dividerOnLight}`, borderRadius: '6px', display: 'flex', alignItems: 'center', gap: 1 }}>
                  {tool.status === 'success' && <CheckCircle sx={{ color: '#10b981', fontSize: '1rem' }} />}
                  {tool.status === 'failure' && <ErrorOutline sx={{ color: '#ef4444', fontSize: '1rem' }} />}
                  {tool.status === 'skipped' && <Schedule sx={{ color: '#f59e0b', fontSize: '1rem' }} />}
                  <Typography sx={{ fontSize: '0.9rem', fontWeight: 500, flex: 1 }}>
                    {tool.tool_name}
                  </Typography>
                  {tool.duration_ms && <Chip label={`${tool.duration_ms}ms`} size="small" sx={{ fontSize: '0.7rem' }} />}
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
}

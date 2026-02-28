import React, { useState } from 'react';
import { Box, Typography, Collapse, Paper, Chip } from '@mui/material';
import { ExpandMore, ExpandLess, AutoStories } from '@mui/icons-material';
import type { Citation } from '../../types';
import { COLORS } from '../../../styles/colors';
import { sourceToGithubUrl, sourceToDisplayName } from '../../utils/sourceLinks';

interface CitationsPanelProps {
  citations: Citation[];
  defaultExpanded?: boolean;
}

export default function CitationsPanel({ citations, defaultExpanded = true }: CitationsPanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <Paper
      sx={{
        mt: 2,
        mb: 1,
        background: 'linear-gradient(135deg, #f0f4ff 0%, #fff8f0 100%)',
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
          backgroundColor: 'rgba(100, 80, 200, 0.08)',
          borderBottom: expanded ? `1px solid ${COLORS.dividerOnLight}` : 'none',
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: 'rgba(100, 80, 200, 0.12)',
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AutoStories sx={{ color: '#6450c8' }} />
          <Typography sx={{ fontWeight: 600, color: '#6450c8', fontSize: '0.95rem' }}>
            📜 Fuentes Legales ({citations.length})
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Chip
            label={`${citations.length} cita${citations.length !== 1 ? 's' : ''}`}
            size="small"
            sx={{ backgroundColor: 'rgba(100, 80, 200, 0.15)', color: '#6450c8', fontWeight: 500 }}
          />
          {expanded ? <ExpandLess /> : <ExpandMore />}
        </Box>
      </Box>

      {/* Expanded Content */}
      <Collapse in={expanded} timeout="auto">
        <Box sx={{ px: 2, py: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {citations.map((citation, idx) => (
            <Box
              key={idx}
              sx={{
                p: 1.5,
                backgroundColor: '#ffffff',
                border: `1px solid rgba(100, 80, 200, 0.2)`,
                borderRadius: '8px',
              }}
            >
              <Typography sx={{ fontWeight: 700, color: '#6450c8', fontSize: '0.95rem', mb: 0.75 }}>
                📋{' '}
                <a
                  href={sourceToGithubUrl(citation.source)}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: '#6450c8',
                    textDecoration: 'underline',
                    textUnderlineOffset: '3px',
                    wordBreak: 'break-word',
                  }}
                >
                  {sourceToDisplayName(citation.source)}
                </a>
              </Typography>
              {citation.page && (
                <Chip label={`Pág. ${citation.page}`} size="small" sx={{ mb: 1, backgroundColor: 'rgba(100, 80, 200, 0.1)', color: '#6450c8' }} />
              )}
              <Box sx={{ p: 1, backgroundColor: 'rgba(100, 80, 200, 0.05)', borderLeft: '3px solid #6450c8', borderRadius: '4px', fontSize: '0.85rem', color: COLORS.textOnLightPrimary, fontStyle: 'italic' }}>
                "{citation.snippet}"
              </Box>
            </Box>
          ))}
        </Box>
      </Collapse>
    </Paper>
  );
}

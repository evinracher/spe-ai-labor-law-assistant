import React, { useState } from 'react';
import { Box, Typography, Collapse, Chip } from '@mui/material';
import { ExpandMore, ExpandLess } from '@mui/icons-material';
import type { Citation } from '../../types';
import { COLORS } from '../../../styles/colors';
import { sourceToGithubUrl, sourceToDisplayName } from '../../utils/sourceLinks';

interface CitationsPanelProps {
  citations: Citation[];
  defaultExpanded?: boolean;
}

export default function CitationsPanel({ citations, defaultExpanded = false }: CitationsPanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        mt: 1.5,
        borderTop: `1px solid ${COLORS.dividerOnLight}`,
        pt: 1,
      }}
    >
      {/* Toggle button */}
      <Box
        onClick={() => setExpanded(!expanded)}
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.5,
          cursor: 'pointer',
          color: COLORS.gold,
          fontSize: '0.8rem',
          fontWeight: 600,
          userSelect: 'none',
          transition: 'opacity 0.15s ease',
          '&:hover': { opacity: 0.75 },
        }}
      >
        {expanded ? <ExpandLess sx={{ fontSize: '1rem' }} /> : <ExpandMore sx={{ fontSize: '1rem' }} />}
        {expanded
          ? `Ocultar fuentes (${citations.length})`
          : `Ver fuentes legales (${citations.length})`}
      </Box>

      {/* Expanded citations */}
      <Collapse in={expanded} timeout="auto">
        <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
          {citations.map((citation, idx) => (
            <Box
              key={idx}
              sx={{
                p: 1.25,
                backgroundColor: 'rgba(212,175,55,0.06)',
                border: `1px solid rgba(212,175,55,0.25)`,
                borderRadius: '8px',
              }}
            >
              <Typography sx={{ fontWeight: 700, color: COLORS.gold, fontSize: '0.85rem', mb: 0.5 }}>
                <a
                  href={sourceToGithubUrl(citation.source)}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: COLORS.gold,
                    textDecoration: 'underline',
                    textUnderlineOffset: '3px',
                    wordBreak: 'break-word',
                  }}
                >
                  {sourceToDisplayName(citation.source)}
                </a>
              </Typography>
              {citation.page && (
                <Chip
                  label={`Pág. ${citation.page}`}
                  size="small"
                  sx={{ mb: 0.75, backgroundColor: 'rgba(212,175,55,0.15)', color: COLORS.gold, fontWeight: 500, fontSize: '0.75rem', height: '20px' }}
                />
              )}
              <Box
                sx={{
                  px: 1,
                  py: 0.5,
                  backgroundColor: 'rgba(212,175,55,0.08)',
                  borderLeft: `2px solid ${COLORS.gold}`,
                  borderRadius: '0 4px 4px 0',
                  fontSize: '0.82rem',
                  color: COLORS.textOnLightSecondary,
                  fontStyle: 'italic',
                  lineHeight: 1.5,
                }}
              >
                "{citation.snippet}"
              </Box>
            </Box>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
}

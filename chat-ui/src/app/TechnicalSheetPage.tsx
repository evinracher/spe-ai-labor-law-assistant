import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { theme } from '../styles/muiTheme';
import TechnicalSheet from './components/ui/technical-sheet';

/**
 * Page for viewing and downloading the technical sheet
 * Can be used as a standalone page or accessed from the header modal
 */
export default function TechnicalSheetPage() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <TechnicalSheet />
    </ThemeProvider>
  );
}

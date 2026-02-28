import {
  AppBar,
  Toolbar,
  Box,
  Typography,
  IconButton,
  Tooltip,
  Dialog,
  DialogContent,
  DialogTitle,
  Button,
} from "@mui/material";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import GavelIcon from "@mui/icons-material/Gavel";
import DescriptionIcon from "@mui/icons-material/Description";
import { COLORS } from "../../../styles/colors";
import { useState } from "react";
import TechnicalSheet from "./technical-sheet";

interface HeaderProps {
  hasMessages: boolean;
  onClearChat: () => void;
}

export default function Header({ hasMessages, onClearChat }: HeaderProps) {
  const [openTechnicalSheet, setOpenTechnicalSheet] = useState(false);

  return (
    <>
      <AppBar position="fixed" elevation={0}>
      <Toolbar
        sx={{
          minHeight: { xs: 56, sm: 64 },
          px: { xs: 2, sm: 3 },
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Left: Logo + Title */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.25 }}>
          <Box
            sx={{
              width: 34,
              height: 34,
              borderRadius: "8px",
              backgroundColor: "rgba(212,175,55,0.12)",
              border: `1px solid rgba(212,175,55,0.3)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <GavelIcon sx={{ color: COLORS.gold, fontSize: 18 }} />
          </Box>
          <Box>
            <Typography
              sx={{
                fontSize: { xs: "1rem", sm: "1.1rem" },
                fontWeight: 600,
                color: COLORS.textOnDarkPrimary,
                lineHeight: 1.2,
                letterSpacing: "-0.01em",
              }}
            >
              Asistente de Derecho Laboral
            </Typography>
            <Typography
              sx={{
                fontSize: "0.7rem",
                color: COLORS.gold,
                opacity: 0.85,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                fontWeight: 500,
                lineHeight: 1,
              }}
            >
              Colombia · Derecho Laboral
            </Typography>
          </Box>
        </Box>

        {/* Right: Actions */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <Tooltip title="Ver ficha técnica" placement="bottom">
            <IconButton
              onClick={() => setOpenTechnicalSheet(true)}
              size="small"
              sx={{
                color: COLORS.textOnDarkSecondary,
                "&:hover": {
                  color: COLORS.gold,
                  backgroundColor: "rgba(212,175,55,0.08)",
                },
              }}
            >
              <DescriptionIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {hasMessages && (
            <Tooltip title="Limpiar chat" placement="bottom">
              <IconButton
                onClick={onClearChat}
                size="small"
                sx={{
                  color: COLORS.textOnDarkSecondary,
                  "&:hover": {
                    color: COLORS.gold,
                    backgroundColor: "rgba(212,175,55,0.08)",
                  },
                }}
              >
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Toolbar>
    </AppBar>

    {/* Technical Sheet Dialog */}
    <Dialog 
      open={openTechnicalSheet} 
      onClose={() => setOpenTechnicalSheet(false)}
      maxWidth="lg"
      fullWidth
      sx={{
        '& .MuiDialog-paper': {
          maxHeight: '90vh',
        }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        Ficha Técnica
        <Button 
          onClick={() => setOpenTechnicalSheet(false)}
          sx={{ color: COLORS.textOnLightSecondary }}
        >
          ✕
        </Button>
      </DialogTitle>
      <DialogContent sx={{ p: 0, overflow: 'hidden' }}>
        <TechnicalSheet />
      </DialogContent>
    </Dialog>
    </>
  );
}

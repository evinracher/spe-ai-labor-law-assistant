import { Box, Typography, Stack, Chip } from "@mui/material";
import GavelIcon from "@mui/icons-material/Gavel";
import { COLORS } from "../../../styles/colors";

// ─── SUGGESTION CHIPS ────────────────────────────────────────────────────────
const SUGGESTIONS = [
  "Contrato a término fijo: reglas básicas",
  "Despido con justa causa: causales",
  "Liquidación de prestaciones: paso a paso",
];

interface EmptyStateProps {
  onSuggestion: (s: string) => void;
}

export default function EmptyState({ onSuggestion }: EmptyStateProps) {
  return (
    <Box
      sx={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        py: 6,
        px: 2,
        textAlign: "center",
      }}
    >
      <Box
        sx={{
          width: 56,
          height: 56,
          borderRadius: "50%",
          backgroundColor: "rgba(212,175,55,0.12)",
          border: `1.5px solid rgba(212,175,55,0.3)`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          mb: 2.5,
        }}
      >
        <GavelIcon sx={{ color: COLORS.gold, fontSize: 26 }} />
      </Box>

      <Typography
        sx={{
          fontSize: "1.05rem",
          fontWeight: 600,
          color: COLORS.textOnLightPrimary,
          mb: 0.75,
        }}
      >
        Haz una pregunta sobre derecho laboral colombiano.
      </Typography>
      <Typography
        sx={{
          fontSize: "0.875rem",
          color: COLORS.textOnLightSecondary,
          mb: 3.5,
          maxWidth: 400,
        }}
      >
        Ejemplo: ¿Cómo se calcula la liquidación?
      </Typography>

      <Stack direction="row" spacing={1} flexWrap="wrap" justifyContent="center" gap={1}>
        {SUGGESTIONS.map((s) => (
          <Chip
            key={s}
            label={s}
            onClick={() => onSuggestion(s)}
            size="small"
            sx={{
              backgroundColor: "rgba(212,175,55,0.1)",
              color: COLORS.textOnLightPrimary,
              border: `1px solid rgba(212,175,55,0.35)`,
              fontSize: "0.8rem",
              fontWeight: 500,
              cursor: "pointer",
              "&:hover": {
                backgroundColor: "rgba(212,175,55,0.2)",
                borderColor: COLORS.gold,
              },
            }}
          />
        ))}
      </Stack>
    </Box>
  );
}

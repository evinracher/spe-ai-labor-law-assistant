import { Box, Typography } from "@mui/material";
import { COLORS } from "../../../styles/colors";
import type { Message } from "../../types";
import CitationsPanel from "./citations-panel";

// ─── FORMAT TIME ─────────────────────────────────────────────────────────────
function formatTime(isoString: string): string {
  const d = new Date(isoString);
  return d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit", hour12: false });
}

// ─── RENDER MESSAGE TEXT (supports **bold**) ─────────────────────────────────
function MessageText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => {
        const parts = line.split(/(\*\*[^*]+\*\*)/g);
        return (
          <span key={i}>
            {parts.map((part, j) =>
              part.startsWith("**") && part.endsWith("**") ? (
                <strong key={j}>{part.slice(2, -2)}</strong>
              ) : (
                <span key={j}>{part}</span>
              )
            )}
            {i < lines.length - 1 && <br />}
          </span>
        );
      })}
    </>
  );
}

// ─── TYPING INDICATOR ────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, py: 0.25 }}>
      {[0, 1, 2].map((i) => (
        <Box
          key={i}
          sx={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            backgroundColor: COLORS.textOnLightSecondary,
            animation: "typingBounce 1.2s ease-in-out infinite",
            animationDelay: `${i * 0.2}s`,
            "@keyframes typingBounce": {
              "0%, 80%, 100%": { transform: "scale(0.7)", opacity: 0.4 },
              "40%": { transform: "scale(1)", opacity: 1 },
            },
          }}
        />
      ))}
    </Box>
  );
}

// ─── MESSAGE BUBBLE ──────────────────────────────────────────────────────────
export default function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  const isTyping = msg.role === "typing";
  const isError = msg.role === "error";

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        mb: 1.5,
        width: "100%",
      }}
    >
      <Box
        sx={{
          maxWidth: isUser ? "72%" : "80%",
          backgroundColor: isUser
            ? COLORS.userBubble
            : isError
            ? "#FFF0F0"
            : COLORS.whiteBubble,
          color: isError ? "#B00020" : COLORS.textOnLightPrimary,
          border: isUser
            ? `1px solid rgba(180,150,30,0.25)`
            : isError
            ? "1px solid rgba(176,0,32,0.2)"
            : `1px solid ${COLORS.dividerOnLight}`,
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          px: 2,
          py: 1.25,
          boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
          fontSize: "0.9375rem",
          lineHeight: 1.65,
          wordBreak: "break-word",
        }}
      >
        {isTyping ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Typography
              sx={{
                fontSize: "0.875rem",
                color: COLORS.textOnLightSecondary,
                fontStyle: "italic",
              }}
            >
              El asistente está respondiendo
            </Typography>
            <TypingDots />
          </Box>
        ) : (
          <MessageText text={msg.text} />
        )}
      </Box>

      {/* Citations Panel - Shows legal sources */}
      {!isTyping && !isUser && msg.citations && msg.citations.length > 0 && (
        <Box sx={{ maxWidth: isUser ? "72%" : "80%", width: "100%", mt: 0.75 }}>
          <CitationsPanel citations={msg.citations} defaultExpanded={true} />
        </Box>
      )}

      {!isTyping && (
        <Typography
          variant="caption"
          sx={{
            mt: 0.4,
            mx: 0.5,
            fontSize: "0.75rem",
            color: COLORS.textOnLightSecondary,
            opacity: 0.75,
          }}
        >
          {formatTime(msg.ts)}
        </Typography>
      )}
    </Box>
  );
}

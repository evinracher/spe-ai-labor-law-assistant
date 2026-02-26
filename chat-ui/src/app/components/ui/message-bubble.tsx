import { useState } from "react";
import { Box, Typography } from "@mui/material";
import { COLORS } from "../../../styles/colors";
import type { Message, Citation } from "../../types";

const CITATIONS_PREVIEW = 3;

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

// ─── SINGLE CITATION CARD ────────────────────────────────────────────────────
function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const label = citation.page === null
    ? citation.source
    : `${citation.source} · p. ${citation.page}`;

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1,
        backgroundColor: "rgba(212,175,55,0.08)",
        border: "1px solid rgba(212,175,55,0.25)",
        borderRadius: "8px",
        px: 1.25,
        py: 0.85,
      }}
    >
      {/* Index badge */}
      <Box
        sx={{
          flexShrink: 0,
          width: 18,
          height: 18,
          borderRadius: "50%",
          backgroundColor: COLORS.gold,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          mt: "1px",
        }}
      >
        <Typography
          sx={{ fontSize: "0.6rem", fontWeight: 700, color: COLORS.darkBg, lineHeight: 1 }}
        >
          {index + 1}
        </Typography>
      </Box>

      <Box sx={{ minWidth: 0 }}>
        {/* Source label */}
        <Typography
          sx={{
            fontSize: "0.72rem",
            fontWeight: 700,
            color: COLORS.gold,
            letterSpacing: "0.01em",
            mb: 0.3,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </Typography>
        {/* Snippet */}
        <Typography
          sx={{
            fontSize: "0.78rem",
            color: COLORS.textOnLightSecondary,
            lineHeight: 1.5,
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          "{citation.snippet}"
        </Typography>
      </Box>
    </Box>
  );
}

// ─── CITATION LIST ────────────────────────────────────────────────────────────
function CitationList({ citations }: { citations: Citation[] }) {
  const [expanded, setExpanded] = useState(false);

  if (citations.length === 0) return null;

  const shown = expanded ? citations : citations.slice(0, CITATIONS_PREVIEW);
  const hasMore = citations.length > CITATIONS_PREVIEW;

  return (
    <Box
      sx={{
        borderTop: "1px solid rgba(212,175,55,0.2)",
        mt: 1.5,
        pt: 1.25,
      }}
    >
      {/* Header */}
      <Typography
        sx={{
          fontSize: "0.7rem",
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.07em",
          color: COLORS.gold,
          mb: 0.85,
          opacity: 0.9,
        }}
      >
        Fuentes consultadas ({citations.length})
      </Typography>

      {/* Cards */}
      <Box sx={{ display: "flex", flexDirection: "column", gap: 0.75 }}>
        {shown.map((c, i) => (
          <CitationCard key={c.chunk_id ?? `${c.source}-${i}`} citation={c} index={i} />
        ))}
      </Box>

      {/* Show more / less toggle */}
      {hasMore && (
        <Typography
          component="button"
          onClick={() => setExpanded((v) => !v)}
          sx={{
            mt: 0.85,
            background: "none",
            border: "none",
            padding: 0,
            cursor: "pointer",
            fontSize: "0.76rem",
            fontWeight: 600,
            color: COLORS.gold,
            textDecoration: "underline",
            textUnderlineOffset: "2px",
            "&:hover": { color: COLORS.goldHover },
          }}
        >
          {expanded
            ? "Mostrar menos"
            : `Mostrar ${citations.length - CITATIONS_PREVIEW} más…`}
        </Typography>
      )}
    </Box>
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
  const hasCitations = !isUser && !isTyping && !isError && (msg.citations?.length ?? 0) > 0;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        mb: 1.5,
      }}
    >
      <Box
        sx={{
          maxWidth: isUser ? "72%" : "78%",
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
          <>
            <MessageText text={msg.text} />
            {hasCitations && <CitationList citations={msg.citations ?? []} />}
          </>
        )}
      </Box>

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

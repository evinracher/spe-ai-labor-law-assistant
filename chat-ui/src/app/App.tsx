import React, { useState, useRef, useEffect, useCallback } from "react";
import { sendMessageRequest } from "../services/chatService";
import {
  createTheme,
  ThemeProvider,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Paper,
  Stack,
  TextField,
  Chip,
  Snackbar,
  Alert,
  CircularProgress,
  Tooltip,
} from "@mui/material";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import SendIcon from "@mui/icons-material/Send";
import GavelIcon from "@mui/icons-material/Gavel";

// ─── PALETTE ────────────────────────────────────────────────────────────────
const COLORS = {
  darkBg: "#0B0B0F",
  darkSurface: "#111118",
  gold: "#D4AF37",
  goldHover: "#B88A1E",
  chatPanel: "#F5F6F8",
  whiteBubble: "#FFFFFF",
  userBubble: "#F1E4B5",
  textOnDarkPrimary: "#EDEDED",
  textOnDarkSecondary: "#B3B3B3",
  textOnLightPrimary: "#111111",
  textOnLightSecondary: "#444444",
  dividerOnDark: "rgba(255,255,255,0.08)",
  dividerOnLight: "rgba(17,17,17,0.08)",
};

// ─── MUI THEME ───────────────────────────────────────────────────────────────
const theme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: COLORS.darkBg,
      paper: COLORS.darkSurface,
    },
    primary: {
      main: COLORS.gold,
      contrastText: "#111111",
    },
    text: {
      primary: COLORS.textOnDarkPrimary,
      secondary: COLORS.textOnDarkSecondary,
    },
    divider: COLORS.dividerOnDark,
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 15,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        "html, body, #root": {
          height: "100%",
          margin: 0,
          padding: 0,
          backgroundColor: COLORS.darkBg,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: COLORS.darkBg,
          backgroundImage: "none",
          borderBottom: `1px solid ${COLORS.dividerOnDark}`,
          boxShadow: "none",
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            backgroundColor: "rgba(255,255,255,0.05)",
            color: COLORS.textOnDarkPrimary,
            borderRadius: 12,
            "& fieldset": {
              borderColor: "rgba(255,255,255,0.15)",
            },
            "&:hover fieldset": {
              borderColor: "rgba(212,175,55,0.5)",
            },
            "&.Mui-focused fieldset": {
              borderColor: COLORS.gold,
              borderWidth: 1.5,
            },
          },
          "& .MuiInputBase-input::placeholder": {
            color: COLORS.textOnDarkSecondary,
            opacity: 1,
          },
        },
      },
    },
  },
});

// ─── TYPES ───────────────────────────────────────────────────────────────────
interface Message {
  id: string;
  role: "user" | "assistant" | "typing" | "error";
  text: string;
  ts: string;
}

// ─── SUGGESTION CHIPS ────────────────────────────────────────────────────────
const SUGGESTIONS = [
  "Contrato a término fijo: reglas básicas",
  "Despido con justa causa: causales",
  "Liquidación de prestaciones: paso a paso",
];

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
function MessageBubble({ msg }: { msg: Message }) {
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
          <MessageText text={msg.text} />
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

// ─── EMPTY STATE ─────────────────────────────────────────────────────────────
function EmptyState({ onSuggestion }: { onSuggestion: (s: string) => void }) {
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

// ─── MAIN APP ────────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "success" | "error";
  }>({ open: false, message: "", severity: "success" });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const typingIdRef = useRef<string | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const genId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

  const handleSend = useCallback(async () => {
    const text = inputText.trim();
    if (!text || isLoading) return;

    setInputText("");
    setIsLoading(true);

    // Add user message
    const userMsg: Message = {
      id: genId(),
      role: "user",
      text,
      ts: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // Add typing indicator
    const typingId = genId();
    typingIdRef.current = typingId;
    const typingMsg: Message = {
      id: typingId,
      role: "typing",
      text: "",
      ts: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, typingMsg]);

    try {
      const answer = await sendMessageRequest(text);
      const assistantMsg: Message = {
        id: genId(),
        role: "assistant",
        text: answer,
        ts: new Date().toISOString(),
      };
      // Replace typing indicator with actual response
      setMessages((prev) =>
        prev.map((m) => (m.id === typingIdRef.current ? assistantMsg : m))
      );
    } catch {
      // Replace typing with error bubble
      const errorMsg: Message = {
        id: genId(),
        role: "error",
        text: "Ocurrió un error al procesar su consulta. Por favor, inténtelo de nuevo.",
        ts: new Date().toISOString(),
      };
      setMessages((prev) =>
        prev.map((m) => (m.id === typingIdRef.current ? errorMsg : m))
      );
      setSnackbar({
        open: true,
        message: "No se pudo obtener respuesta. Intenta de nuevo.",
        severity: "error",
      });
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [inputText, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setInputText("");
    setSnackbar({ open: true, message: "Chat limpiado.", severity: "success" });
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const handleSuggestion = (s: string) => {
    setInputText(s);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const hasMessages = messages.length > 0;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      <Box
        sx={{
          height: "100vh",
          display: "flex",
          flexDirection: "column",
          backgroundColor: COLORS.darkBg,
          overflow: "hidden",
        }}
      >
        {/* ── HEADER ── */}
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
              {hasMessages && (
                <Tooltip title="Limpiar chat" placement="bottom">
                  <IconButton
                    onClick={handleClearChat}
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

        {/* ── MAIN BODY ── */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            mt: { xs: "56px", sm: "64px" },
            mb: 0,
            overflow: "hidden",
            px: { xs: 0, sm: 2, md: 3 },
            py: { xs: 1.5, sm: 2 },
          }}
        >
          {/* ── CHAT PANEL ── */}
          <Paper
            elevation={0}
            sx={{
              width: "100%",
              maxWidth: { xs: "100%", md: 1000 },
              flex: 1,
              display: "flex",
              flexDirection: "column",
              backgroundColor: COLORS.chatPanel,
              borderRadius: { xs: 0, sm: "18px" },
              border: { xs: "none", sm: `1px solid rgba(0,0,0,0.08)` },
              boxShadow: { xs: "none", sm: "0 4px 32px rgba(0,0,0,0.22)" },
              overflow: "hidden",
            }}
          >
            {/* Messages Scroll Area */}
            <Box
              sx={{
                flex: 1,
                overflowY: "auto",
                px: { xs: 2, sm: 3 },
                py: { xs: 2, sm: 2.5 },
                display: "flex",
                flexDirection: "column",
                scrollbarWidth: "thin",
                scrollbarColor: `rgba(0,0,0,0.15) transparent`,
                "&::-webkit-scrollbar": { width: 5 },
                "&::-webkit-scrollbar-track": { background: "transparent" },
                "&::-webkit-scrollbar-thumb": {
                  background: "rgba(0,0,0,0.15)",
                  borderRadius: 3,
                },
              }}
            >
              {!hasMessages ? (
                <EmptyState onSuggestion={handleSuggestion} />
              ) : (
                messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)
              )}
              <div ref={messagesEndRef} />
            </Box>

            {/* ── COMPOSER ── */}
            <Box
              sx={{
                borderTop: `1px solid ${COLORS.dividerOnLight}`,
                backgroundColor: COLORS.darkSurface,
                px: { xs: 1.5, sm: 2 },
                py: { xs: 1.25, sm: 1.5 },
                display: "flex",
                alignItems: "flex-end",
                gap: 1.25,
              }}
            >
              <TextField
                inputRef={inputRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Escribe tu pregunta…"
                multiline
                minRows={1}
                maxRows={4}
                disabled={isLoading}
                fullWidth
                variant="outlined"
                size="small"
                sx={{
                  "& .MuiOutlinedInput-root": {
                    py: 1,
                    px: 1.75,
                    fontSize: "0.9375rem",
                    borderRadius: "12px",
                    backgroundColor: isLoading
                      ? "rgba(255,255,255,0.03)"
                      : "rgba(255,255,255,0.05)",
                  },
                }}
              />

              {/* Send Button */}
              <Box
                component="button"
                onClick={handleSend}
                disabled={!inputText.trim() || isLoading}
                sx={{
                  width: 42,
                  height: 42,
                  minWidth: 42,
                  flexShrink: 0,
                  borderRadius: "12px",
                  backgroundColor:
                    !inputText.trim() || isLoading
                      ? "rgba(255,255,255,0.08)"
                      : COLORS.gold,
                  border: "none",
                  cursor:
                    !inputText.trim() || isLoading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "background-color 0.18s ease, transform 0.1s ease",
                  outline: "none",
                  "&:hover:not(:disabled)": {
                    backgroundColor: COLORS.goldHover,
                    transform: "scale(1.04)",
                  },
                  "&:active:not(:disabled)": {
                    transform: "scale(0.97)",
                  },
                }}
              >
                {isLoading ? (
                  <CircularProgress
                    size={18}
                    thickness={4}
                    sx={{ color: COLORS.textOnDarkSecondary }}
                  />
                ) : (
                  <SendIcon
                    sx={{
                      fontSize: 18,
                      color:
                        !inputText.trim()
                          ? COLORS.textOnDarkSecondary
                          : COLORS.darkBg,
                    }}
                  />
                )}
              </Box>
            </Box>
          </Paper>
        </Box>

        {/* ── SNACKBAR ── */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={3500}
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
          anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        >
          <Alert
            onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
            severity={snackbar.severity}
            variant="filled"
            sx={{
              borderRadius: "10px",
              fontSize: "0.875rem",
              backgroundColor:
                snackbar.severity === "error" ? "#B00020" : COLORS.darkSurface,
              color: "#FFFFFF",
              border:
                snackbar.severity === "success"
                  ? `1px solid ${COLORS.dividerOnDark}`
                  : "none",
              "& .MuiAlert-icon": {
                color:
                  snackbar.severity === "error" ? "#FFB3B3" : COLORS.gold,
              },
            }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
}

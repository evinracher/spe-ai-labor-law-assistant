import React, { useState, useRef, useEffect, useCallback } from "react";
import { sendMessageRequest } from "../services/chatService";
import {
  ThemeProvider,
  CssBaseline,
  Box,
  Paper,
  TextField,
  CircularProgress,
} from "@mui/material";
import { COLORS } from "../styles/colors";
import { theme } from "../styles/muiTheme";
import SendIcon from "@mui/icons-material/Send";
import Header from "./components/ui/header";
import AppSnackbar from "./components/ui/app-snackbar";
import MessageBubble from "./components/ui/message-bubble";
import EmptyState from "./components/ui/empty-state";
import type { Message } from "./types";

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
        <Header hasMessages={hasMessages} onClearChat={handleClearChat} />
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
        <AppSnackbar
          open={snackbar.open}
          message={snackbar.message}
          severity={snackbar.severity}
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        />
      </Box>
    </ThemeProvider>
  );
}

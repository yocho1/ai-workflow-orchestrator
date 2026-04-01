import React from "react";
import ReactDOM from "react-dom/client";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";

import App from "./App";
import "./styles.css";

const THEME_MODE_KEY = "workflow_theme_mode";

const getInitialMode = (): "light" | "dark" => {
  const stored = window.localStorage.getItem(THEME_MODE_KEY);
  return stored === "dark" ? "dark" : "light";
};

const getAppTheme = (mode: "light" | "dark") =>
  createTheme({
    palette: {
      mode,
      primary: {
        main: "#0f766e",
        dark: "#115e59",
        light: "#14b8a6",
      },
      secondary: {
        main: "#d97706",
        light: "#f59e0b",
        dark: "#b45309",
      },
      text: {
        primary: mode === "light" ? "#0f172a" : "#e2e8f0",
        secondary: mode === "light" ? "#475569" : "#94a3b8",
      },
      background: {
        default: mode === "light" ? "#f7f4ed" : "#0b1220",
        paper: mode === "light" ? "#ffffff" : "#111c2e",
      },
      divider: mode === "light" ? "rgba(15, 23, 42, 0.12)" : "rgba(148, 163, 184, 0.22)",
    },
    shape: {
      borderRadius: 16,
    },
    typography: {
      fontFamily: "'Manrope', 'Helvetica Neue', sans-serif",
      h1: { fontFamily: "'Space Grotesk', 'Manrope', sans-serif", fontWeight: 700, letterSpacing: -0.8 },
      h2: { fontFamily: "'Space Grotesk', 'Manrope', sans-serif", fontWeight: 700, letterSpacing: -0.6 },
      h3: { fontFamily: "'Space Grotesk', 'Manrope', sans-serif", fontWeight: 700, letterSpacing: -0.4 },
      h4: { fontFamily: "'Space Grotesk', 'Manrope', sans-serif", fontWeight: 700, letterSpacing: -0.3 },
      h5: { fontFamily: "'Space Grotesk', 'Manrope', sans-serif", fontWeight: 700, letterSpacing: -0.2 },
      h6: { fontFamily: "'Space Grotesk', 'Manrope', sans-serif", fontWeight: 700, letterSpacing: -0.1 },
      button: { textTransform: "none", fontWeight: 700 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            background:
              mode === "light"
                ? "radial-gradient(circle at 8% 5%, rgba(20, 184, 166, 0.18), transparent 38%), radial-gradient(circle at 92% 85%, rgba(217, 119, 6, 0.16), transparent 34%), linear-gradient(145deg, #f8f5ef 0%, #eff6f6 42%, #f7f2e8 100%)"
                : "radial-gradient(circle at 8% 5%, rgba(20, 184, 166, 0.15), transparent 34%), radial-gradient(circle at 92% 85%, rgba(217, 119, 6, 0.12), transparent 30%), linear-gradient(140deg, #0b1220 0%, #111827 48%, #1f2937 100%)",
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 16,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            border: mode === "light" ? "1px solid rgba(15, 23, 42, 0.08)" : "1px solid rgba(148, 163, 184, 0.2)",
            boxShadow: mode === "light" ? "0 16px 35px rgba(15, 23, 42, 0.08)" : "0 14px 30px rgba(2, 6, 23, 0.45)",
            backgroundImage:
              mode === "light"
                ? "linear-gradient(180deg, rgba(255,255,255,0.94) 0%, rgba(255,255,255,0.9) 100%)"
                : "linear-gradient(180deg, rgba(17,28,46,0.95) 0%, rgba(17,28,46,0.92) 100%)",
            backdropFilter: "blur(8px)",
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            paddingInline: 16,
          },
          containedPrimary: {
            backgroundImage: "linear-gradient(120deg, #0f766e 0%, #14b8a6 100%)",
            boxShadow: "0 10px 20px rgba(15, 118, 110, 0.25)",
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 999,
            fontWeight: 700,
          },
        },
      },
      MuiTextField: {
        defaultProps: {
          size: "small",
        },
      },
      MuiTableCell: {
        styleOverrides: {
          head: {
            fontWeight: 700,
            color: mode === "light" ? "#334155" : "#cbd5e1",
            backgroundColor: mode === "light" ? "rgba(148, 163, 184, 0.12)" : "rgba(51, 65, 85, 0.28)",
          },
        },
      },
    },
  });

function RootApp(): JSX.Element {
  const [mode, setMode] = React.useState<"light" | "dark">(getInitialMode);
  const theme = React.useMemo(() => getAppTheme(mode), [mode]);

  const handleToggleTheme = React.useCallback(() => {
    setMode((prev) => {
      const next = prev === "light" ? "dark" : "light";
      window.localStorage.setItem(THEME_MODE_KEY, next);
      return next;
    });
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App colorMode={mode} onToggleColorMode={handleToggleTheme} />
    </ThemeProvider>
  );
}

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element not found");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <RootApp />
  </React.StrictMode>,
);

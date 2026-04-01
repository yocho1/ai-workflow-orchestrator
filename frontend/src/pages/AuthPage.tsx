import { FormEvent, useState } from "react";
import { Alert, Box, Button, Card, CardContent, Stack, Tab, Tabs, TextField, Typography } from "@mui/material";

type AuthPageProps = {
  onLogin: (email: string, password: string) => Promise<void>;
  onRegister: (email: string, fullName: string, password: string) => Promise<void>;
};

export const AuthPage = ({ onLogin, onRegister }: AuthPageProps): JSX.Element => {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  let submitLabel = "Create Account";
  if (mode === "login") {
    submitLabel = "Login";
  }
  if (loading) {
    submitLabel = "Please wait...";
  }

  const onSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim() || (mode === "register" && !fullName.trim())) {
      setError("Please fill in all required fields.");
      return;
    }

    setLoading(true);
    try {
      if (mode === "login") {
        await onLogin(email.trim(), password);
      } else {
        await onRegister(email.trim(), fullName.trim(), password);
      }
    } catch {
      setError(mode === "login" ? "Login failed." : "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", px: { xs: 1.5, sm: 2.5 } }}>
      <Card sx={{ width: "100%", maxWidth: 980, borderRadius: 5, overflow: "hidden" }}>
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1.05fr 1fr" } }}>
          <Box
            sx={{
              p: { xs: 3, sm: 4 },
              background: "linear-gradient(145deg, rgba(15,118,110,0.98) 0%, rgba(21,128,61,0.94) 48%, rgba(217,119,6,0.92) 100%)",
              color: "#f8fafc",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              gap: 2.5,
            }}
          >
            <Stack spacing={1.5}>
              <Typography variant="h3" sx={{ fontWeight: 800, lineHeight: 1.15 }}>
                Workflow OS
              </Typography>
              <Typography variant="body1" sx={{ color: "rgba(241, 245, 249, 0.92)", maxWidth: 420 }}>
                Coordinate uploads, extraction, and AI operations in one modern control center.
              </Typography>
            </Stack>
            <Typography variant="caption" sx={{ color: "rgba(241,245,249,0.85)" }}>
              Secure access for your team workspace
            </Typography>
          </Box>

          <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
            <Stack spacing={2.5}>
              <Typography variant="h4" sx={{ fontWeight: 800 }}>
                {mode === "login" ? "Welcome back" : "Create your account"}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to access your documents and AI workflows.
              </Typography>

              <Tabs value={mode} onChange={(_, value) => setMode(value)}>
                <Tab label="Login" value="login" />
                <Tab label="Register" value="register" />
              </Tabs>

              {error && <Alert severity="error">{error}</Alert>}

              <Box component="form" onSubmit={onSubmit}>
                <Stack spacing={2}>
                  <TextField
                    label="Email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                    fullWidth
                  />
                  {mode === "register" && (
                    <TextField
                      label="Full Name"
                      value={fullName}
                      onChange={(event) => setFullName(event.target.value)}
                      required
                      fullWidth
                    />
                  )}
                  <TextField
                    label="Password"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                    fullWidth
                    helperText="Minimum 8 characters"
                  />
                  <Button type="submit" variant="contained" disabled={loading}>
                    {submitLabel}
                  </Button>
                </Stack>
              </Box>
            </Stack>
          </CardContent>
        </Box>
      </Card>
    </Box>
  );
};

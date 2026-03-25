import { useEffect } from "react";
import { Box, Drawer } from "@mui/material";

import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { AuthPage } from "./pages/AuthPage";
import { DashboardPage } from "./pages/DashboardPage";
import { login, me, register } from "./services/auth";
import { useAuthStore } from "./state/authStore";
import { useUIStore } from "./state/uiStore";

const drawerWidth = 260;

function App(): JSX.Element {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const { token, user, isAuthReady, setAuth, setUser, markAuthReady, logout } = useAuthStore();

  useEffect(() => {
    const bootstrap = async (): Promise<void> => {
      if (!token) {
        markAuthReady();
        return;
      }

      try {
        const currentUser = await me();
        setUser(currentUser);
      } catch {
        logout();
      } finally {
        markAuthReady();
      }
    };

    void bootstrap();
  }, [token]);

  const handleLogin = async (email: string, password: string): Promise<void> => {
    const authData = await login(email, password);
    setAuth(authData.token.access_token, authData.user);
  };

  const handleRegister = async (email: string, fullName: string, password: string): Promise<void> => {
    const authData = await register(email, fullName, password);
    setAuth(authData.token.access_token, authData.user);
  };

  if (!isAuthReady) {
    return <Box sx={{ minHeight: "100vh" }} />;
  }

  if (!token || !user) {
    return <AuthPage onLogin={handleLogin} onRegister={handleRegister} />;
  }

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Drawer
        variant="persistent"
        open={sidebarOpen}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
          },
        }}
      >
        <Sidebar />
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          transition: "margin 0.2s ease",
          marginLeft: sidebarOpen ? 0 : `-${drawerWidth}px`,
        }}
      >
        <Header
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          userName={user.full_name}
          onLogout={logout}
        />
        <Box sx={{ p: { xs: 2, sm: 3 } }}>
          <DashboardPage />
        </Box>
      </Box>
    </Box>
  );
}

export default App;

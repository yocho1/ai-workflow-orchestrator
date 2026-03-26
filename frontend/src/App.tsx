import { useEffect } from "react";
import { Box, Drawer } from "@mui/material";

import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { AIAssistantPage } from "./pages/AIAssistantPage";
import { AuthPage } from "./pages/AuthPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { UploadsPage } from "./pages/UploadsPage";
import { login, me, register } from "./services/auth";
import { useAuthStore } from "./state/authStore";
import { useUIStore } from "./state/uiStore";

const drawerWidth = 260;

function App(): JSX.Element {
  const { sidebarOpen, activeSection, setSidebarOpen, setActiveSection } = useUIStore();
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

  const sectionTitleMap = {
    dashboard: "Executive Dashboard",
    documents: "Documents",
    uploads: "Uploads",
    ai: "AI Assistant",
  };

  let pageContent = <DashboardPage />;
  if (activeSection === "documents") {
    pageContent = <DocumentsPage />;
  }
  if (activeSection === "uploads") {
    pageContent = <UploadsPage />;
  }
  if (activeSection === "ai") {
    pageContent = <AIAssistantPage />;
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
        <Sidebar activeSection={activeSection} onSelectSection={setActiveSection} />
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
          sectionTitle={sectionTitleMap[activeSection]}
          onLogout={logout}
        />
        <Box sx={{ p: { xs: 2, sm: 3 } }}>
          {pageContent}
        </Box>
      </Box>
    </Box>
  );
}

export default App;

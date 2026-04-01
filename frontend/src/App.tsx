import { useEffect } from "react";
import { Box, Drawer, useMediaQuery, useTheme } from "@mui/material";

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

type AppProps = {
  colorMode: "light" | "dark";
  onToggleColorMode: () => void;
};

function App({ colorMode, onToggleColorMode }: AppProps): JSX.Element {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
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
    <Box sx={{ display: "flex", minHeight: "100vh", position: "relative" }}>
      <Drawer
        variant={isMobile ? "temporary" : "persistent"}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            border: "none",
            background:
              "linear-gradient(180deg, rgba(15, 23, 42, 0.96) 0%, rgba(15, 118, 110, 0.95) 65%, rgba(21, 94, 117, 0.96) 100%)",
          },
        }}
      >
        <Sidebar
          activeSection={activeSection}
          onSelectSection={(section) => {
            setActiveSection(section);
            if (isMobile) {
              setSidebarOpen(false);
            }
          }}
        />
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          position: "relative",
          transition: "margin 0.22s ease",
          marginLeft: !isMobile && !sidebarOpen ? `-${drawerWidth}px` : 0,
        }}
      >
        <Header
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          userName={user.full_name}
          sectionTitle={sectionTitleMap[activeSection]}
          onLogout={logout}
          colorMode={colorMode}
          onToggleColorMode={onToggleColorMode}
        />
        <Box
          sx={{
            p: { xs: 1.5, sm: 2.5, md: 3 },
          }}
        >
          {pageContent}
        </Box>
      </Box>
    </Box>
  );
}

export default App;

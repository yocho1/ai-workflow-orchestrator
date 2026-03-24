import { Box, Drawer } from "@mui/material";

import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { DashboardPage } from "./pages/DashboardPage";
import { useUIStore } from "./state/uiStore";

const drawerWidth = 260;

function App(): JSX.Element {
  const { sidebarOpen, setSidebarOpen } = useUIStore();

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
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        <Box sx={{ p: { xs: 2, sm: 3 } }}>
          <DashboardPage />
        </Box>
      </Box>
    </Box>
  );
}

export default App;

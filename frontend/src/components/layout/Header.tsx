import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import MenuRoundedIcon from "@mui/icons-material/MenuRounded";
import DarkModeRoundedIcon from "@mui/icons-material/DarkModeRounded";
import LightModeRoundedIcon from "@mui/icons-material/LightModeRounded";
import { AppBar, Avatar, Box, IconButton, Toolbar, Typography } from "@mui/material";

type HeaderProps = {
  onToggleSidebar: () => void;
  userName: string;
  sectionTitle: string;
  onLogout: () => void;
  colorMode: "light" | "dark";
  onToggleColorMode: () => void;
};

export const Header = ({
  onToggleSidebar,
  userName,
  sectionTitle,
  onLogout,
  colorMode,
  onToggleColorMode,
}: HeaderProps): JSX.Element => {
  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        background: "linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.78) 100%)",
        backdropFilter: "blur(14px)",
        color: "text.primary",
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Toolbar sx={{ minHeight: 72, px: { xs: 2, sm: 3 } }}>
        <IconButton
          edge="start"
          onClick={onToggleSidebar}
          sx={{ mr: 1.5, border: "1px solid", borderColor: "divider", bgcolor: "background.paper" }}
        >
          <MenuRoundedIcon fontSize="small" />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
            {sectionTitle}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            AI Workflow Orchestrator
          </Typography>
        </Box>
        <IconButton
          onClick={onToggleColorMode}
          sx={{
            mr: 1,
            border: "1px solid",
            borderColor: "divider",
            bgcolor: "rgba(248, 250, 252, 0.9)",
          }}
          aria-label="Toggle color mode"
        >
          {colorMode === "light" ? <DarkModeRoundedIcon fontSize="small" /> : <LightModeRoundedIcon fontSize="small" />}
        </IconButton>
        <IconButton
          onClick={onLogout}
          sx={{
            mr: 1,
            border: "1px solid",
            borderColor: "divider",
            bgcolor: "rgba(248, 250, 252, 0.9)",
          }}
          aria-label="Logout"
        >
          <LogoutRoundedIcon fontSize="small" />
        </IconButton>
        <Avatar
          sx={{
            width: 36,
            height: 36,
            bgcolor: "secondary.main",
            color: "#fff",
            fontWeight: 800,
            border: "2px solid rgba(255, 255, 255, 0.9)",
          }}
        >
          {userName.slice(0, 1).toUpperCase()}
        </Avatar>
      </Toolbar>
    </AppBar>
  );
};

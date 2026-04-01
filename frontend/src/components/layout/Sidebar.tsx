import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import DescriptionRoundedIcon from "@mui/icons-material/DescriptionRounded";
import UploadFileRoundedIcon from "@mui/icons-material/UploadFileRounded";
import { SvgIconComponent } from "@mui/icons-material";
import { Box, List, ListItemButton, ListItemIcon, ListItemText, Stack, Toolbar, Typography } from "@mui/material";

import { AppSection } from "../../state/uiStore";

type NavItem = {
  key: AppSection;
  label: string;
  icon: SvgIconComponent;
};

const navItems: NavItem[] = [
  { key: "dashboard", label: "Dashboard", icon: DashboardRoundedIcon },
  { key: "documents", label: "Documents", icon: DescriptionRoundedIcon },
  { key: "uploads", label: "Uploads", icon: UploadFileRoundedIcon },
  { key: "ai", label: "AI Assistant", icon: AutoAwesomeRoundedIcon },
];

type SidebarProps = {
  activeSection: AppSection;
  onSelectSection: (section: AppSection) => void;
};

export const Sidebar = ({ activeSection, onSelectSection }: SidebarProps): JSX.Element => {
  return (
    <Box sx={{ width: 260, color: "#e2e8f0", height: "100%" }}>
      <Toolbar sx={{ px: 2.5, pt: 2, pb: 1.25 }}>
        <Stack spacing={0.4}>
          <Typography variant="h6" sx={{ fontWeight: 800, color: "#f8fafc", lineHeight: 1.1 }}>
            Workflow OS
          </Typography>
          <Typography variant="caption" sx={{ color: "rgba(241, 245, 249, 0.8)" }}>
            Intelligent operations cockpit
          </Typography>
          <Typography variant="caption" sx={{ color: "rgba(204, 251, 241, 0.9)", fontWeight: 700 }}>
            Live Workspace
          </Typography>
        </Stack>
      </Toolbar>
      <List sx={{ px: 1.25, pt: 1 }}>
        {navItems.map((item) => (
          <ListItemButton
            key={item.key}
            selected={activeSection === item.key}
            onClick={() => onSelectSection(item.key)}
            sx={{
              borderRadius: 2.5,
              mb: 0.75,
              color: "rgba(226, 232, 240, 0.92)",
              "&.Mui-selected": {
                bgcolor: "rgba(248, 250, 252, 0.2)",
                color: "#ffffff",
                boxShadow: "inset 0 0 0 1px rgba(255, 255, 255, 0.2)",
              },
              "&.Mui-selected:hover": {
                bgcolor: "rgba(248, 250, 252, 0.26)",
              },
              "&:hover": {
                bgcolor: "rgba(248, 250, 252, 0.12)",
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>
              <item.icon fontSize="small" sx={{ color: "inherit" }} />
            </ListItemIcon>
            <ListItemText
              primary={item.label}
              slotProps={{
                primary: {
                  sx: {
                    fontWeight: activeSection === item.key ? 700 : 600,
                    fontSize: "0.96rem",
                  },
                },
              }}
            />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
};

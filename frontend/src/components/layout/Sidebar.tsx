import { Box, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography } from "@mui/material";

import { AppSection } from "../../state/uiStore";

type NavItem = {
  key: AppSection;
  label: string;
  marker: string;
};

const navItems: NavItem[] = [
  { key: "dashboard", label: "Dashboard", marker: "DB" },
  { key: "documents", label: "Documents", marker: "DOC" },
  { key: "uploads", label: "Uploads", marker: "UP" },
  { key: "ai", label: "AI Assistant", marker: "AI" },
];

type SidebarProps = {
  activeSection: AppSection;
  onSelectSection: (section: AppSection) => void;
};

export const Sidebar = ({ activeSection, onSelectSection }: SidebarProps): JSX.Element => {
  return (
    <Box sx={{ width: 260, borderRight: "1px solid", borderColor: "divider", height: "100%" }}>
      <Toolbar sx={{ px: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, color: "primary.main" }}>
          Workflow OS
        </Typography>
      </Toolbar>
      <List sx={{ px: 1 }}>
        {navItems.map((item) => (
          <ListItemButton
            key={item.key}
            selected={activeSection === item.key}
            onClick={() => onSelectSection(item.key)}
            sx={{ borderRadius: 2, mb: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                {item.marker}
              </Typography>
            </ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
};

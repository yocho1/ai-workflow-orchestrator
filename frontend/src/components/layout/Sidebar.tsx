import { Box, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography } from "@mui/material";

const navItems = [
  { label: "Dashboard", marker: "DB" },
  { label: "Documents", marker: "DOC" },
  { label: "Uploads", marker: "UP" },
  { label: "AI Assistant", marker: "AI" },
];

export const Sidebar = (): JSX.Element => {
  return (
    <Box sx={{ width: 260, borderRight: "1px solid", borderColor: "divider", height: "100%" }}>
      <Toolbar sx={{ px: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, color: "primary.main" }}>
          Workflow OS
        </Typography>
      </Toolbar>
      <List sx={{ px: 1 }}>
        {navItems.map((item) => (
          <ListItemButton key={item.label} sx={{ borderRadius: 2, mb: 0.5 }}>
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

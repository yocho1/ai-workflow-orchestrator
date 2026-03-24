import { AppBar, Avatar, Box, IconButton, Toolbar, Typography } from "@mui/material";

type HeaderProps = {
  onToggleSidebar: () => void;
};

export const Header = ({ onToggleSidebar }: HeaderProps): JSX.Element => {
  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        backgroundColor: "background.paper",
        color: "text.primary",
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Toolbar sx={{ minHeight: 72, px: { xs: 2, sm: 3 } }}>
        <IconButton edge="start" onClick={onToggleSidebar} sx={{ mr: 2 }}>
          <Typography variant="button">Menu</Typography>
        </IconButton>
        <Typography variant="h6" sx={{ fontWeight: 600, flexGrow: 1 }}>
          Business Workflow Automation
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <IconButton>
            <Typography variant="button">Alerts</Typography>
          </IconButton>
          <Avatar sx={{ width: 34, height: 34, bgcolor: "primary.main" }}>A</Avatar>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

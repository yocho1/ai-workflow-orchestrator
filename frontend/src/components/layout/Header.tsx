import { AppBar, Avatar, Box, IconButton, Toolbar, Typography } from "@mui/material";

type HeaderProps = {
  onToggleSidebar: () => void;
  userName: string;
  sectionTitle: string;
  onLogout: () => void;
};

export const Header = ({ onToggleSidebar, userName, sectionTitle, onLogout }: HeaderProps): JSX.Element => {
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
          {sectionTitle}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <IconButton onClick={onLogout}>
            <Typography variant="button">Logout</Typography>
          </IconButton>
          <Avatar sx={{ width: 34, height: 34, bgcolor: "primary.main" }}>
            {userName.slice(0, 1).toUpperCase()}
          </Avatar>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

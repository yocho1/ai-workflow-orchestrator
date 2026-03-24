import { Card, CardContent, Grid, Stack, Typography } from "@mui/material";

import { usePageTitle } from "../hooks/usePageTitle";

const cards = [
  { label: "Pending Documents", value: "28" },
  { label: "Processed Today", value: "164" },
  { label: "Failed Pipelines", value: "2" },
  { label: "AI Queries (24h)", value: "51" },
];

export const DashboardPage = (): JSX.Element => {
  usePageTitle("Dashboard");

  return (
    <Stack spacing={3}>
      <Typography variant="h4" sx={{ fontWeight: 700 }}>
        Operations Dashboard
      </Typography>
      <Grid container spacing={2.5}>
        {cards.map((card) => (
          <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={card.label}>
            <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
              <CardContent>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {card.label}
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {card.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
};

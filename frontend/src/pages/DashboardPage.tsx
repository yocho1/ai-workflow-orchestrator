import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Card,
  CardContent,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { usePageTitle } from "../hooks/usePageTitle";
import { listDocuments } from "../services/documents";
import { DocumentRecord } from "../types/api";

export const DashboardPage = (): JSX.Element => {
  usePageTitle("Dashboard");

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch {
      setError("Failed to load documents from backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadDocuments();
  }, []);

  const stats = useMemo(() => {
    const total = documents.length;
    const classified = documents.filter((doc) => doc.processing_status === "classified").length;
    const pending = documents.filter((doc) => doc.processing_status !== "classified").length;
    const invoices = documents.filter((doc) => doc.document_type === "invoice").length;
    return [
      { label: "Total Documents", value: total },
      { label: "Classified", value: classified },
      { label: "Pending", value: pending },
      { label: "Invoices", value: invoices },
    ];
  }, [documents]);

  const recentDocuments = documents.slice(0, 6);

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error">{error}</Alert>}

      <Grid container spacing={2.5}>
        {stats.map((card) => (
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

      <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
            Recent Activity
          </Typography>
          {loading && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              Loading recent documents...
            </Typography>
          )}
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Filename</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Type</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recentDocuments.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.id}</TableCell>
                  <TableCell>{doc.filename}</TableCell>
                  <TableCell>{doc.processing_status}</TableCell>
                  <TableCell>{doc.document_type ?? "-"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Stack>
  );
};

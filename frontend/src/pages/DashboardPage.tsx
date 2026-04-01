import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  MenuItem,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";

import { usePageTitle } from "../hooks/usePageTitle";
import { listDocuments } from "../services/documents";
import { DocumentRecord } from "../types/api";
import { StatusBadge } from "../components/StatusBadge";

export const DashboardPage = (): JSX.Element => {
  usePageTitle("Dashboard");

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

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
  const filteredRecentDocuments = recentDocuments.filter((doc) => {
    if (statusFilter !== "all" && doc.processing_status !== statusFilter) {
      return false;
    }
    if (!searchTerm.trim()) {
      return true;
    }
    return `${doc.filename} ${doc.document_type ?? ""} ${doc.processing_status}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
  });

  const lastUpdated = documents.length > 0 ? new Date(documents[0].updated_at).toLocaleString() : "No activity yet";

  return (
    <Stack spacing={3.25}>
      {error && <Alert severity="error">{error}</Alert>}

      <Card
        elevation={0}
        sx={{
          borderRadius: 4,
          overflow: "hidden",
          background:
            "linear-gradient(115deg, rgba(15,118,110,0.95) 0%, rgba(21,128,61,0.88) 42%, rgba(217,119,6,0.88) 100%)",
          color: "#f8fafc",
        }}
      >
        <CardContent sx={{ p: { xs: 2.5, sm: 3.25 } }}>
          <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={2}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.7 }}>
                Operations Pulse
              </Typography>
              <Typography variant="body1" sx={{ color: "rgba(241, 245, 249, 0.9)", maxWidth: 560 }}>
                Track document throughput, classification progress, and workflow quality in one place.
              </Typography>
            </Box>
            <Stack spacing={1} alignItems={{ xs: "flex-start", md: "flex-end" }}>
              <Chip
                label={loading ? "Syncing" : "Live Data"}
                sx={{ bgcolor: "rgba(255, 255, 255, 0.2)", color: "#fff", border: "1px solid rgba(255,255,255,0.32)" }}
              />
              <Typography variant="caption" sx={{ color: "rgba(241,245,249,0.82)" }}>
                Last update: {lastUpdated}
              </Typography>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Grid container spacing={2.5}>
        {stats.map((card) => (
          <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={card.label}>
            <Card elevation={0} sx={{ borderRadius: 3.5 }}>
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

      <Card elevation={0} sx={{ borderRadius: 3.5 }}>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} justifyContent="space-between" sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              Recent Activity
            </Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
              <TextField
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search documents"
                slotProps={{
                  input: {
                    startAdornment: <SearchRoundedIcon fontSize="small" style={{ marginRight: 8, opacity: 0.7 }} />,
                  },
                }}
                sx={{ minWidth: 220 }}
              />
              <TextField
                select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                sx={{ minWidth: 160 }}
              >
                <MenuItem value="all">All statuses</MenuItem>
                <MenuItem value="uploaded">Uploaded</MenuItem>
                <MenuItem value="processing">Processing</MenuItem>
                <MenuItem value="classified">Classified</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
              </TextField>
            </Stack>
          </Stack>
          {loading && (
            <Stack spacing={1} sx={{ mb: 1.5 }}>
              <Skeleton variant="rounded" height={38} />
              <Skeleton variant="rounded" height={38} />
              <Skeleton variant="rounded" height={38} />
            </Stack>
          )}
          <Table size="small" sx={{ "& td, & th": { borderColor: "rgba(148, 163, 184, 0.22)" } }}>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Filename</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Updated</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredRecentDocuments.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.id}</TableCell>
                  <TableCell>{doc.filename}</TableCell>
                  <TableCell>
                    <StatusBadge status={doc.processing_status} />
                  </TableCell>
                  <TableCell>{doc.document_type ?? "-"}</TableCell>
                  <TableCell>{new Date(doc.updated_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
              {!loading && filteredRecentDocuments.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Stack alignItems="center" spacing={1.2} sx={{ py: 3 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        No activity found
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Clear filters or upload documents to populate this view.
                      </Typography>
                      <Button size="small" variant="outlined" onClick={() => {
                        setSearchTerm("");
                        setStatusFilter("all");
                      }}>
                        Reset view
                      </Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Stack>
  );
};

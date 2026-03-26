import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { usePageTitle } from "../hooks/usePageTitle";
import { classifyDocument } from "../services/ai";
import { listDocuments } from "../services/documents";
import { DocumentRecord } from "../types/api";

export const DocumentsPage = (): JSX.Element => {
  usePageTitle("Documents");

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [classifyingId, setClassifyingId] = useState<number | null>(null);

  const load = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      setDocuments(await listDocuments());
    } catch {
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleClassify = async (documentId: number): Promise<void> => {
    setClassifyingId(documentId);
    setError(null);
    try {
      await classifyDocument(documentId);
      await load();
    } catch {
      setError("Failed to classify this document.");
    } finally {
      setClassifyingId(null);
    }
  };

  return (
    <Stack spacing={2.5}>
      {error && <Alert severity="error">{error}</Alert>}

      <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Document Registry
            </Typography>
            <Button variant="text" onClick={() => void load()}>
              Refresh
            </Button>
          </Stack>

          {loading ? (
            <Stack direction="row" spacing={1} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2">Loading...</Typography>
            </Stack>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Filename</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell align="right">Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id} hover>
                    <TableCell>{doc.id}</TableCell>
                    <TableCell>{doc.filename}</TableCell>
                    <TableCell>
                      <Chip size="small" label={doc.processing_status} />
                    </TableCell>
                    <TableCell>{doc.document_type ?? "-"}</TableCell>
                    <TableCell align="right">
                      <Button
                        size="small"
                        variant="outlined"
                        disabled={classifyingId === doc.id}
                        onClick={() => void handleClassify(doc.id)}
                      >
                        {classifyingId === doc.id ? "Classifying..." : "Classify"}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Stack>
  );
};

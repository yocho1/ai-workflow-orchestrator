import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Grid,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import { usePageTitle } from "../hooks/usePageTitle";
import { askDocument, classifyDocument } from "../services/ai";
import { createDocument, listDocuments } from "../services/documents";
import { AskDocumentResult, DocumentRecord } from "../types/api";

type FormState = {
  filename: string;
  extracted_text: string;
};

const initialForm: FormState = {
  filename: "",
  extracted_text: "",
};

export const DashboardPage = (): JSX.Element => {
  usePageTitle("Dashboard");

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [createLoading, setCreateLoading] = useState<boolean>(false);
  const [form, setForm] = useState<FormState>(initialForm);

  const [classifyLoadingId, setClassifyLoadingId] = useState<number | null>(null);

  const [askDocumentId, setAskDocumentId] = useState<string>("");
  const [question, setQuestion] = useState<string>("");
  const [askLoading, setAskLoading] = useState<boolean>(false);
  const [askResult, setAskResult] = useState<AskDocumentResult | null>(null);

  const loadDocuments = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDocuments();
      setDocuments(data);
      if (data.length > 0 && askDocumentId === "") {
        setAskDocumentId(String(data[0].id));
      }
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

  const onSubmitCreate = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    if (!form.filename.trim() || !form.extracted_text.trim()) {
      setError("Filename and extracted text are required.");
      return;
    }

    setCreateLoading(true);
    setError(null);
    try {
      await createDocument({
        filename: form.filename.trim(),
        extracted_text: form.extracted_text.trim(),
      });
      setForm(initialForm);
      await loadDocuments();
    } catch {
      setError("Failed to create document.");
    } finally {
      setCreateLoading(false);
    }
  };

  const onClassify = async (documentId: number): Promise<void> => {
    setClassifyLoadingId(documentId);
    setError(null);
    try {
      await classifyDocument(documentId);
      await loadDocuments();
    } catch {
      setError("Classification failed. Check backend or OpenRouter settings.");
    } finally {
      setClassifyLoadingId(null);
    }
  };

  const onAsk = async (): Promise<void> => {
    if (!askDocumentId || !question.trim()) {
      setError("Select a document and provide a question.");
      return;
    }

    setAskLoading(true);
    setError(null);
    try {
      const result = await askDocument(Number(askDocumentId), question.trim());
      setAskResult(result);
    } catch {
      setError("Question answering failed.");
    } finally {
      setAskLoading(false);
    }
  };

  return (
    <Stack spacing={3}>
      <Typography variant="h4" sx={{ fontWeight: 700 }}>
        Operations Dashboard
      </Typography>

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

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
                Create Document
              </Typography>
              <Box component="form" onSubmit={onSubmitCreate}>
                <Stack spacing={2}>
                  <TextField
                    label="Filename"
                    value={form.filename}
                    onChange={(event) => setForm((prev) => ({ ...prev, filename: event.target.value }))}
                    placeholder="invoice-2026-03.txt"
                    fullWidth
                    required
                  />
                  <TextField
                    label="Extracted Text"
                    value={form.extracted_text}
                    onChange={(event) => setForm((prev) => ({ ...prev, extracted_text: event.target.value }))}
                    minRows={5}
                    multiline
                    fullWidth
                    required
                  />
                  <Button type="submit" variant="contained" disabled={createLoading}>
                    {createLoading ? "Creating..." : "Create Document"}
                  </Button>
                </Stack>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 7 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Documents
                </Typography>
                <Button variant="text" onClick={() => void loadDocuments()}>
                  Refresh
                </Button>
              </Stack>

              {loading ? (
                <Stack direction="row" spacing={1} alignItems="center">
                  <CircularProgress size={18} />
                  <Typography variant="body2">Loading documents...</Typography>
                </Stack>
              ) : (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>Filename</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {documents.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell>{doc.id}</TableCell>
                        <TableCell>{doc.filename}</TableCell>
                        <TableCell>{doc.processing_status}</TableCell>
                        <TableCell>{doc.document_type ?? "-"}</TableCell>
                        <TableCell align="right">
                          <Button
                            size="small"
                            variant="outlined"
                            disabled={classifyLoadingId === doc.id}
                            onClick={() => void onClassify(doc.id)}
                          >
                            {classifyLoadingId === doc.id ? "Classifying..." : "Classify"}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
            Ask Document (RAG)
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField
                select
                label="Document"
                value={askDocumentId}
                onChange={(event) => setAskDocumentId(event.target.value)}
                fullWidth
              >
                {documents.map((doc) => (
                  <MenuItem key={doc.id} value={String(doc.id)}>
                    #{doc.id} - {doc.filename}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12, md: 8 }}>
              <TextField
                label="Question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="What is the total amount due?"
                fullWidth
              />
            </Grid>
          </Grid>

          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Button variant="contained" onClick={() => void onAsk()} disabled={askLoading}>
              {askLoading ? "Asking..." : "Ask"}
            </Button>
          </Stack>

          {askResult && (
            <Stack spacing={1.5} sx={{ mt: 2.5 }}>
              <Divider />
              <Typography variant="body2" color="text.secondary">
                Answer
              </Typography>
              <Typography variant="body1">{askResult.answer}</Typography>
              <Typography variant="caption" color="text.secondary">
                Confidence: {askResult.confidence ?? "n/a"} | Context Chunks: {askResult.context_chunks_used}
              </Typography>
            </Stack>
          )}
        </CardContent>
      </Card>
    </Stack>
  );
};

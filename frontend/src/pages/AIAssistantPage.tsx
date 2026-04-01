import { useEffect, useState } from "react";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  LinearProgress,
  MenuItem,
  Paper,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";

import { usePageTitle } from "../hooks/usePageTitle";
import { askDocument, classifyDocument } from "../services/ai";
import { listDocuments } from "../services/documents";
import { getHttpErrorMessage } from "../services/http";
import { AskDocumentResult, DocumentRecord } from "../types/api";

const formatConfidence = (confidence: number | null): string => {
  if (confidence === null || Number.isNaN(confidence)) {
    return "Not available";
  }
  if (confidence >= 0.85) {
    return "High";
  }
  if (confidence >= 0.65) {
    return "Medium";
  }
  return "Low";
};

export const AIAssistantPage = (): JSX.Element => {
  usePageTitle("AI Assistant");

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState<boolean>(true);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string; answer?: AskDocumentResult }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [classifying, setClassifying] = useState(false);

  useEffect(() => {
    const load = async (): Promise<void> => {
      setLoadingDocuments(true);
      try {
        const data = await listDocuments();
        setDocuments(data);
        if (data.length > 0) {
          setSelectedDocumentId(String(data[0].id));
        }
      } catch (error) {
        setError(getHttpErrorMessage(error, "Failed to load documents."));
      } finally {
        setLoadingDocuments(false);
      }
    };

    void load();
  }, []);

  const onAsk = async (): Promise<void> => {
    if (!selectedDocumentId || !question.trim()) {
      setError("Select a document and enter a question.");
      return;
    }

    setAsking(true);
    setError(null);
    const userMessage = question.trim();
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setQuestion("");
    try {
      const result = await askDocument(Number(selectedDocumentId), userMessage);
      setMessages((prev) => [...prev, { role: "assistant", content: result.answer, answer: result }]);
    } catch (error) {
      setError(getHttpErrorMessage(error, "AI question failed."));
    } finally {
      setAsking(false);
    }
  };

  const onClassify = async (): Promise<void> => {
    if (!selectedDocumentId) {
      setError("Select a document first.");
      return;
    }

    setClassifying(true);
    setError(null);
    try {
      await classifyDocument(Number(selectedDocumentId));
    } catch (error) {
      setError(getHttpErrorMessage(error, "Classification failed."));
    } finally {
      setClassifying(false);
    }
  };

  return (
    <Stack spacing={2.5}>
      {error && <Alert severity="error">{error}</Alert>}

      <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
            AI Workspace
          </Typography>

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}>
              {loadingDocuments ? (
                <Skeleton variant="rounded" height={40} />
              ) : (
                <TextField
                  select
                  label="Document"
                  value={selectedDocumentId}
                  onChange={(event) => setSelectedDocumentId(event.target.value)}
                  fullWidth
                >
                  {documents.map((doc) => (
                    <MenuItem key={doc.id} value={String(doc.id)}>
                      #{doc.id} - {doc.filename}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            </Grid>
            <Grid size={{ xs: 12, md: 8 }}>
              <TextField
                label="Question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="What is the total amount due?"
                fullWidth
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void onAsk();
                  }
                }}
              />
            </Grid>
          </Grid>

          <Stack direction="row" spacing={1.5} sx={{ mt: 2 }}>
            <Button variant="contained" onClick={() => void onAsk()} disabled={asking}>
              {asking ? "Asking..." : "Ask AI"}
            </Button>
            <Button variant="outlined" onClick={() => void onClassify()} disabled={classifying}>
              {classifying ? "Classifying..." : "Classify Selected"}
            </Button>
          </Stack>

          <Divider sx={{ my: 2.5 }} />

          <Stack spacing={1.5} sx={{ maxHeight: 420, overflowY: "auto", pr: 0.5 }}>
            {messages.length === 0 ? (
              <Paper variant="outlined" sx={{ p: 2.5 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 0.5 }}>
                  Start a conversation
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Ask questions about a selected document and the assistant will answer with confidence details.
                </Typography>
              </Paper>
            ) : (
              messages.map((message, index) => (
                <Stack
                  key={`${message.role}-${index}`}
                  direction="row"
                  spacing={1.2}
                  justifyContent={message.role === "user" ? "flex-end" : "flex-start"}
                >
                  {message.role === "assistant" && (
                    <Avatar sx={{ bgcolor: "primary.main", width: 32, height: 32 }}>
                      <AutoAwesomeRoundedIcon fontSize="small" />
                    </Avatar>
                  )}
                  <Paper
                    sx={{
                      p: 1.5,
                      maxWidth: "78%",
                      bgcolor: message.role === "user" ? "primary.main" : "background.paper",
                      color: message.role === "user" ? "#fff" : "text.primary",
                      borderRadius: 2.5,
                    }}
                  >
                    <Typography variant="body2">{message.content}</Typography>
                    {message.answer && (
                      <Box sx={{ mt: 1.2 }}>
                        <Typography variant="caption" color={message.role === "user" ? "rgba(255,255,255,0.8)" : "text.secondary"}>
                          Confidence: {formatConfidence(message.answer.confidence)}
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={Math.max(0, Math.min(100, (message.answer.confidence ?? 0) * 100))}
                          sx={{ mt: 0.75, height: 6, borderRadius: 999 }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.75 }}>
                          Sources: {Array.from({ length: Math.max(1, message.answer.context_chunks_used) })
                            .map((_, i) => `Doc #${message.answer?.document_id} chunk ${i + 1}`)
                            .join(" • ")}
                        </Typography>
                      </Box>
                    )}
                  </Paper>
                  {message.role === "user" && (
                    <Avatar sx={{ bgcolor: "secondary.main", width: 32, height: 32 }}>
                      <PersonRoundedIcon fontSize="small" />
                    </Avatar>
                  )}
                </Stack>
              ))
            )}

            {asking && (
              <Stack direction="row" spacing={1.2} alignItems="center">
                <Avatar sx={{ bgcolor: "primary.main", width: 32, height: 32 }}>
                  <AutoAwesomeRoundedIcon fontSize="small" />
                </Avatar>
                <Paper sx={{ p: 1.5, borderRadius: 2.5 }}>
                  <Stack direction="row" spacing={0.75}>
                    <Skeleton variant="circular" width={8} height={8} />
                    <Skeleton variant="circular" width={8} height={8} />
                    <Skeleton variant="circular" width={8} height={8} />
                  </Stack>
                </Paper>
              </Stack>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
};

import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

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
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskDocumentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [classifying, setClassifying] = useState(false);

  useEffect(() => {
    const load = async (): Promise<void> => {
      try {
        const data = await listDocuments();
        setDocuments(data);
        if (data.length > 0) {
          setSelectedDocumentId(String(data[0].id));
        }
      } catch (error) {
        setError(getHttpErrorMessage(error, "Failed to load documents."));
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
    try {
      setAnswer(await askDocument(Number(selectedDocumentId), question.trim()));
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

          <Stack direction="row" spacing={1.5} sx={{ mt: 2 }}>
            <Button variant="contained" onClick={() => void onAsk()} disabled={asking}>
              {asking ? "Asking..." : "Ask AI"}
            </Button>
            <Button variant="outlined" onClick={() => void onClassify()} disabled={classifying}>
              {classifying ? "Classifying..." : "Classify Selected"}
            </Button>
          </Stack>

          {answer && (
            <Stack spacing={1.5} sx={{ mt: 2.5 }}>
              <Divider />
              <Typography variant="body2" color="text.secondary">
                Answer
              </Typography>
              <Typography variant="body1">{answer.answer}</Typography>
              <Typography variant="caption" color="text.secondary">
                Confidence: {formatConfidence(answer.confidence)}
              </Typography>
            </Stack>
          )}
        </CardContent>
      </Card>
    </Stack>
  );
};

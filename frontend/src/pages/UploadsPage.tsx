import { ChangeEvent, useState } from "react";
import { Alert, Button, Card, CardContent, Stack, Typography } from "@mui/material";

import { usePageTitle } from "../hooks/usePageTitle";
import { uploadDocument } from "../services/documents";

export const UploadsPage = (): JSX.Element => {
  usePageTitle("Uploads");

  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const selected = event.target.files?.[0];
    if (!selected) {
      return;
    }

    setFile(selected);
    setError(null);
    setMessage(`Selected file: ${selected.name}`);
  };

  const handleUpload = async (): Promise<void> => {
    if (!file) {
      setError("Select a file first.");
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const created = await uploadDocument(file);
      setMessage(`Uploaded successfully: ${created.filename}`);
      setFile(null);
    } catch {
      setError("Upload failed. Supported formats: .txt, .md, .csv, .json, .pdf.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack spacing={2.5}>
      {error && <Alert severity="error">{error}</Alert>}
      {message && <Alert severity="success">{message}</Alert>}

      <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Upload and Ingest
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Upload .txt, .md, .csv, .json, or .pdf. Extraction is handled securely on the backend.
            </Typography>

            <Button component="label" variant="outlined">
              <span>Choose File</span>
              <input hidden type="file" accept=".txt,.md,.csv,.json,.pdf,text/plain,application/pdf" onChange={handleFile} />
            </Button>

            <Button variant="contained" disabled={loading || !file} onClick={() => void handleUpload()}>
              {loading ? "Uploading..." : "Upload Document"}
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
};

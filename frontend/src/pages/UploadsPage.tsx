import { ChangeEvent, DragEvent, useState } from "react";
import { Alert, Box, Button, Card, CardContent, CircularProgress, Stack, Typography } from "@mui/material";
import CloudUploadRoundedIcon from "@mui/icons-material/CloudUploadRounded";

import { usePageTitle } from "../hooks/usePageTitle";
import { uploadDocument } from "../services/documents";

export const UploadsPage = (): JSX.Element => {
  usePageTitle("Uploads");

  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
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

  const handleDrag = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    event.stopPropagation();
    if (event.type === "dragenter" || event.type === "dragover") {
      setDragActive(true);
      return;
    }
    setDragActive(false);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
    const dropped = event.dataTransfer.files?.[0];
    if (!dropped) {
      return;
    }
    setFile(dropped);
    setError(null);
    setMessage(`Selected file: ${dropped.name}`);
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

            <Box
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              sx={{
                border: "2px dashed",
                borderColor: dragActive ? "primary.main" : "divider",
                borderRadius: 3,
                p: 3,
                textAlign: "center",
                bgcolor: dragActive ? "rgba(20, 184, 166, 0.08)" : "transparent",
                transition: "all 0.2s ease",
              }}
            >
              <Stack spacing={1} alignItems="center">
                <CloudUploadRoundedIcon color="primary" />
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  Drag and drop your file here
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  or choose a file manually
                </Typography>
                <Button component="label" variant="outlined">
                  <span>Choose File</span>
                  <input hidden type="file" accept=".txt,.md,.csv,.json,.pdf,text/plain,application/pdf" onChange={handleFile} />
                </Button>
              </Stack>
            </Box>

            {file && (
              <Typography variant="body2" color="text.secondary">
                Ready to upload: {file.name}
              </Typography>
            )}

            <Button variant="contained" disabled={loading || !file} onClick={() => void handleUpload()}>
              {loading ? (
                <Stack direction="row" spacing={1} alignItems="center">
                  <CircularProgress size={16} color="inherit" />
                  <span>Uploading...</span>
                </Stack>
              ) : (
                "Upload Document"
              )}
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
};

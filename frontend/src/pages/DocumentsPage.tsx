import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  LinearProgress,
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

import { StatusBadge } from "../components/StatusBadge";
import { usePageTitle } from "../hooks/usePageTitle";
import { classifyDocument } from "../services/ai";
import { listDocuments } from "../services/documents";
import { getJobStatus } from "../services/jobs";
import {
  batchExtractMetadata,
  extractMetadata,
  exportMetadataCsv,
  exportMetadataPdf,
  getMetadata,
  listMetadataReviewQueue,
  MetadataExportFilters,
  updateMetadata,
} from "../services/metadata";
import { DocumentRecord, JobStatusResponse, MetadataReviewQueueItem } from "../types/api";
import { getHttpErrorMessage } from "../services/http";

const EXPORT_FILTERS_STORAGE_KEY = "documents_export_filters_v1";

type StoredExportFilters = {
  documentType: string;
  needsReview: string;
  updatedFrom: string;
  updatedTo: string;
};

const defaultStoredExportFilters: StoredExportFilters = {
  documentType: "",
  needsReview: "all",
  updatedFrom: "",
  updatedTo: "",
};

const loadStoredExportFilters = (): StoredExportFilters => {
  try {
    const raw = window.localStorage.getItem(EXPORT_FILTERS_STORAGE_KEY);
    if (!raw) {
      return defaultStoredExportFilters;
    }

    const parsed = JSON.parse(raw) as Partial<StoredExportFilters>;
    return {
      documentType: typeof parsed.documentType === "string" ? parsed.documentType : "",
      needsReview:
        parsed.needsReview === "true" || parsed.needsReview === "false" || parsed.needsReview === "all"
          ? parsed.needsReview
          : "all",
      updatedFrom: typeof parsed.updatedFrom === "string" ? parsed.updatedFrom : "",
      updatedTo: typeof parsed.updatedTo === "string" ? parsed.updatedTo : "",
    };
  } catch {
    return defaultStoredExportFilters;
  }
};

const typeDisplayMap: Record<string, string> = {
  invoice: "🧾 Invoice",
  receipt: "🧾 Receipt",
  contract: "⚖️ Contract",
  agreement: "⚖️ Agreement",
  purchase_order: "🛒 Purchase Order",
  email: "✉️ Email",
  report: "📄 Report",
  dataset: "📊 Dataset",
  certificate: "🎓 Certificate",
  other: "📦 Other",
};

const formatDocumentType = (documentType: string | null): string => {
  if (!documentType) {
    return "-";
  }
  return typeDisplayMap[documentType] ?? "📦 Other";
};

export const DocumentsPage = (): JSX.Element => {
  usePageTitle("Documents");

  const storedExportFilters = loadStoredExportFilters();

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [classifyingId, setClassifyingId] = useState<number | null>(null);
  const [extractingId, setExtractingId] = useState<number | null>(null);
  const [reviewQueue, setReviewQueue] = useState<MetadataReviewQueueItem[]>([]);
  const [reviewQueueError, setReviewQueueError] = useState<string | null>(null);
  const [batchJob, setBatchJob] = useState<JobStatusResponse | null>(null);
  const [batchRunning, setBatchRunning] = useState<boolean>(false);

  const [reviewOpen, setReviewOpen] = useState<boolean>(false);
  const [reviewLoading, setReviewLoading] = useState<boolean>(false);
  const [reviewSaving, setReviewSaving] = useState<boolean>(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewDocumentId, setReviewDocumentId] = useState<number | null>(null);
  const [reviewDocumentType, setReviewDocumentType] = useState<string>("other");
  const [reviewConfidence, setReviewConfidence] = useState<string>("0");
  const [reviewExtractedJson, setReviewExtractedJson] = useState<string>("{}");
  const [exportDocumentType, setExportDocumentType] = useState<string>(storedExportFilters.documentType);
  const [exportNeedsReview, setExportNeedsReview] = useState<string>(storedExportFilters.needsReview);
  const [exportUpdatedFrom, setExportUpdatedFrom] = useState<string>(storedExportFilters.updatedFrom);
  const [exportUpdatedTo, setExportUpdatedTo] = useState<string>(storedExportFilters.updatedTo);

  useEffect(() => {
    const payload: StoredExportFilters = {
      documentType: exportDocumentType,
      needsReview: exportNeedsReview,
      updatedFrom: exportUpdatedFrom,
      updatedTo: exportUpdatedTo,
    };
    window.localStorage.setItem(EXPORT_FILTERS_STORAGE_KEY, JSON.stringify(payload));
  }, [exportDocumentType, exportNeedsReview, exportUpdatedFrom, exportUpdatedTo]);

  const buildExportFilters = (): MetadataExportFilters => {
    const filters: MetadataExportFilters = {};

    if (exportDocumentType) {
      filters.document_type = exportDocumentType;
    }
    if (exportNeedsReview !== "all") {
      filters.needs_review = exportNeedsReview === "true";
    }
    if (exportUpdatedFrom) {
      filters.updated_from = exportUpdatedFrom;
    }
    if (exportUpdatedTo) {
      filters.updated_to = exportUpdatedTo;
    }

    return filters;
  };

  const hasInvalidDateRange = (): boolean => {
    if (!exportUpdatedFrom || !exportUpdatedTo) {
      return false;
    }
    return exportUpdatedFrom > exportUpdatedTo;
  };

  const invalidDateRange = hasInvalidDateRange();

  const resetExportFilters = (): void => {
    setExportDocumentType("");
    setExportNeedsReview("all");
    setExportUpdatedFrom("");
    setExportUpdatedTo("");
    setError(null);
  };

  const load = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    setReviewQueueError(null);
    try {
      const [docsResult, queueResult] = await Promise.allSettled([
        listDocuments(),
        listMetadataReviewQueue(),
      ]);

      if (docsResult.status === "fulfilled") {
        setDocuments(docsResult.value);
      } else {
        setDocuments([]);
        setError(getHttpErrorMessage(docsResult.reason, "Failed to load documents."));
      }

      if (queueResult.status === "fulfilled") {
        setReviewQueue(queueResult.value);
      } else {
        setReviewQueue([]);
        setReviewQueueError(
          getHttpErrorMessage(queueResult.reason, "Failed to load review queue."),
        );
      }
    } catch {
      setDocuments([]);
      setReviewQueue([]);
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

  const handleExtractMetadata = async (documentId: number): Promise<void> => {
    setExtractingId(documentId);
    setError(null);
    try {
      await extractMetadata(documentId);
      await load();
    } catch (err: unknown) {
      setError(getHttpErrorMessage(err, "Failed to extract metadata."));
    } finally {
      setExtractingId(null);
    }
  };

  const sleep = (ms: number): Promise<void> =>
    new Promise((resolve) => {
      setTimeout(resolve, ms);
    });

  const handleBatchExtract = async (): Promise<void> => {
    if (documents.length === 0) {
      return;
    }

    setBatchRunning(true);
    setError(null);
    try {
      const start = await batchExtractMetadata(documents.map((doc) => doc.id));

      for (let attempt = 0; attempt < 120; attempt += 1) {
        const job = await getJobStatus(start.job_id);
        setBatchJob(job);

        if (job.status === "completed") {
          await load();
          break;
        }

        if (job.status === "failed") {
          await load();
          setError(`Batch extraction failed: ${job.error ?? "Some documents could not be processed."}`);
          break;
        }

        await sleep(500);
      }
    } catch (err: unknown) {
      setError(getHttpErrorMessage(err, "Failed to start batch extraction."));
    } finally {
      setBatchRunning(false);
    }
  };

  const handleExportCsv = async (): Promise<void> => {
    if (invalidDateRange) {
      setError("Export filter error: 'Updated from' must be before or equal to 'Updated to'.");
      return;
    }

    setError(null);
    try {
      const blob = await exportMetadataCsv(buildExportFilters());
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `metadata_export_${new Date().toISOString().replace(/[:.]/g, "-")}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(getHttpErrorMessage(err, "Failed to export CSV."));
    }
  };

  const handleExportPdf = async (): Promise<void> => {
    if (invalidDateRange) {
      setError("Export filter error: 'Updated from' must be before or equal to 'Updated to'.");
      return;
    }

    setError(null);
    try {
      const blob = await exportMetadataPdf(buildExportFilters());
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `metadata_export_${new Date().toISOString().replace(/[:.]/g, "-")}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(getHttpErrorMessage(err, "Failed to export PDF."));
    }
  };

  const openReviewDialog = async (documentId: number): Promise<void> => {
    setReviewOpen(true);
    setReviewLoading(true);
    setReviewError(null);
    setReviewDocumentId(documentId);
    try {
      const metadata = await getMetadata(documentId);
      setReviewDocumentType(metadata.document_type ?? "other");
      setReviewConfidence(String(metadata.confidence_score ?? 0));
      setReviewExtractedJson(JSON.stringify(metadata.extracted_data ?? {}, null, 2));
    } catch (err: unknown) {
      setReviewError(getHttpErrorMessage(err, "Could not load metadata. Extract metadata first."));
      setReviewDocumentType("other");
      setReviewConfidence("0");
      setReviewExtractedJson("{}");
    } finally {
      setReviewLoading(false);
    }
  };

  const closeReviewDialog = (): void => {
    setReviewOpen(false);
    setReviewError(null);
    setReviewDocumentId(null);
  };

  const handleSaveReview = async (): Promise<void> => {
    if (!reviewDocumentId) {
      return;
    }

    let parsedExtractedData: Record<string, unknown>;
    try {
      const parsed = JSON.parse(reviewExtractedJson) as unknown;
      if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
        setReviewError("Extracted data must be a JSON object.");
        return;
      }
      parsedExtractedData = parsed as Record<string, unknown>;
    } catch {
      setReviewError("Invalid JSON in extracted data.");
      return;
    }

    const confidenceValue = Number(reviewConfidence);
    if (Number.isNaN(confidenceValue) || confidenceValue < 0 || confidenceValue > 1) {
      setReviewError("Confidence score must be between 0 and 1.");
      return;
    }

    setReviewSaving(true);
    setReviewError(null);
    try {
      await updateMetadata(reviewDocumentId, {
        document_type: reviewDocumentType,
        confidence_score: confidenceValue,
        extracted_data: parsedExtractedData,
      });
      await load();
      closeReviewDialog();
    } catch (err: unknown) {
      setReviewError(getHttpErrorMessage(err, "Failed to save metadata updates."));
    } finally {
      setReviewSaving(false);
    }
  };

  return (
    <Stack spacing={2.5}>
      {error && <Alert severity="error">{error}</Alert>}

      <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1.5 }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Review Queue
            </Typography>
            <Chip
              size="small"
              color={reviewQueue.length > 0 ? "warning" : "default"}
              label={`${reviewQueue.length} pending`}
            />
          </Stack>
          {reviewQueueError && (
            <Alert severity="warning" sx={{ mb: 1.5 }}>
              {reviewQueueError}
            </Alert>
          )}
          {reviewQueue.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No low-confidence metadata currently needs review.
            </Typography>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Document</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell align="right">Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reviewQueue.map((item) => (
                  <TableRow key={item.document_id} hover>
                    <TableCell>{item.filename}</TableCell>
                    <TableCell>{formatDocumentType(item.document_type)}</TableCell>
                    <TableCell>{(item.confidence_score * 100).toFixed(0)}%</TableCell>
                    <TableCell>{item.review_reason ?? "Manual review required"}</TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined" onClick={() => void openReviewDialog(item.document_id)}>
                        Review Now
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Document Registry
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button
                variant="contained"
                disabled={batchRunning || loading || documents.length === 0}
                onClick={() => void handleBatchExtract()}
              >
                {batchRunning ? "Batch Running..." : "Extract All"}
              </Button>
              <Button
                variant="outlined"
                disabled={loading}
                onClick={() => void handleExportCsv()}
              >
                Export CSV
              </Button>
              <Button
                variant="outlined"
                disabled={loading}
                onClick={() => void handleExportPdf()}
              >
                Export PDF
              </Button>
              <Button variant="text" onClick={() => void load()}>
                Refresh
              </Button>
            </Stack>
          </Stack>

          <Stack
            direction={{ xs: "column", md: "row" }}
            spacing={1}
            sx={{ mb: 2 }}
            alignItems={{ xs: "stretch", md: "center" }}
          >
            <TextField
              select
              size="small"
              label="Filter Type"
              value={exportDocumentType}
              onChange={(e) => setExportDocumentType(e.target.value)}
              sx={{ minWidth: 170 }}
            >
              <MenuItem value="">All types</MenuItem>
              <MenuItem value="invoice">invoice</MenuItem>
              <MenuItem value="contract">contract</MenuItem>
              <MenuItem value="receipt">receipt</MenuItem>
              <MenuItem value="report">report</MenuItem>
              <MenuItem value="other">other</MenuItem>
            </TextField>
            <TextField
              select
              size="small"
              label="Review"
              value={exportNeedsReview}
              onChange={(e) => setExportNeedsReview(e.target.value)}
              sx={{ minWidth: 140 }}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="true">Needs review</MenuItem>
              <MenuItem value="false">No review</MenuItem>
            </TextField>
            <TextField
              size="small"
              label="Updated from"
              type="date"
              value={exportUpdatedFrom}
              onChange={(e) => setExportUpdatedFrom(e.target.value)}
              InputLabelProps={{ shrink: true }}
              error={invalidDateRange}
              helperText={invalidDateRange ? "Must be earlier than or equal to 'Updated to'." : " "}
            />
            <TextField
              size="small"
              label="Updated to"
              type="date"
              value={exportUpdatedTo}
              onChange={(e) => setExportUpdatedTo(e.target.value)}
              InputLabelProps={{ shrink: true }}
              error={invalidDateRange}
              helperText={invalidDateRange ? "Must be later than or equal to 'Updated from'." : " "}
            />
            <Button variant="text" onClick={resetExportFilters}>
              Reset Filters
            </Button>
          </Stack>

          {batchJob && (
            <Box sx={{ mb: 2 }}>
              <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Batch job {batchJob.job_id}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {batchJob.processed_documents}/{batchJob.total_documents}
                </Typography>
              </Stack>
              <LinearProgress variant="determinate" value={batchJob.progress_percent} />
            </Box>
          )}

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
                      <StatusBadge status={doc.processing_status} />
                    </TableCell>
                    <TableCell>{formatDocumentType(doc.document_type)}</TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={1} justifyContent="flex-end">
                        <Button
                          size="small"
                          variant="outlined"
                          disabled={classifyingId === doc.id}
                          onClick={() => void handleClassify(doc.id)}
                        >
                          {classifyingId === doc.id ? "Classifying..." : "Classify"}
                        </Button>
                        <Button
                          size="small"
                          variant="contained"
                          disabled={extractingId === doc.id}
                          onClick={() => void handleExtractMetadata(doc.id)}
                        >
                          {extractingId === doc.id ? "Extracting..." : "Extract"}
                        </Button>
                        <Button
                          size="small"
                          variant="text"
                          onClick={() => void openReviewDialog(doc.id)}
                        >
                          Review
                        </Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={reviewOpen} onClose={closeReviewDialog} maxWidth="md" fullWidth>
        <DialogTitle>Review Metadata</DialogTitle>
        <DialogContent>
          {reviewLoading ? (
            <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 1 }}>
              <CircularProgress size={18} />
              <Typography variant="body2">Loading metadata...</Typography>
            </Stack>
          ) : (
            <Stack spacing={2} sx={{ pt: 1 }}>
              {reviewError && <Alert severity="error">{reviewError}</Alert>}

              <Box display="grid" gridTemplateColumns={{ xs: "1fr", sm: "1fr 1fr" }} gap={2}>
                <TextField
                  select
                  label="Document Type"
                  value={reviewDocumentType}
                  onChange={(e) => setReviewDocumentType(e.target.value)}
                >
                  <MenuItem value="invoice">invoice</MenuItem>
                  <MenuItem value="contract">contract</MenuItem>
                  <MenuItem value="receipt">receipt</MenuItem>
                  <MenuItem value="report">report</MenuItem>
                  <MenuItem value="other">other</MenuItem>
                </TextField>
                <TextField
                  label="Confidence (0-1)"
                  value={reviewConfidence}
                  onChange={(e) => setReviewConfidence(e.target.value)}
                  inputProps={{ step: "0.01" }}
                />
              </Box>

              <Divider />

              <TextField
                label="Extracted Data (JSON)"
                value={reviewExtractedJson}
                onChange={(e) => setReviewExtractedJson(e.target.value)}
                multiline
                minRows={12}
                fullWidth
              />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeReviewDialog} disabled={reviewSaving}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={() => void handleSaveReview()}
            disabled={reviewLoading || reviewSaving || reviewDocumentId === null}
          >
            {reviewSaving ? "Saving..." : "Save Review"}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";

interface Metadata {
  id: number;
  document_id: number;
  document_type: string;
  confidence_score: number;
  extracted_data: Record<string, unknown>;
  extraction_model: string;
  extraction_error: string | null;
  created_at: string;
  updated_at: string;
}

interface MetadataDisplayProps {
  metadata: Metadata | null;
  loading?: boolean;
  error?: string | null;
}

/**
 * MetadataDisplay Component
 * 
 * Displays extracted document metadata with:
 * - Document type badge with confidence score
 * - Extracted fields organized by type
 * - Error state if extraction failed
 * - Loading state while extracting
 */
export function MetadataDisplay({
  metadata,
  loading = false,
  error = null,
}: MetadataDisplayProps) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 2 }}>
            <CircularProgress size={18} />
            <Typography variant="body2">Extracting metadata...</Typography>
          </Stack>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  if (!metadata) {
    return (
      <Card>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
            Extracted Metadata
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No metadata has been extracted yet.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (metadata.extraction_error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{metadata.extraction_error}</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
            Extracted Metadata
          </Typography>
          <Chip
            size="small"
            label={
              <>
            {metadata.document_type.toUpperCase()}
                {" "}
                (
              {(metadata.confidence_score * 100).toFixed(0)}%
                )
              </>
            }
            variant="outlined"
          />
        </Stack>

        {Object.entries(metadata.extracted_data).length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No fields extracted.
          </Typography>
        ) : (
          <Stack spacing={2}>
            {Object.entries(metadata.extracted_data).map(([key, value]) => (
              <Box key={key} sx={{ borderLeft: "4px solid", borderColor: "primary.light", pl: 1.5 }}>
                <Typography variant="body2" sx={{ fontWeight: 700, textTransform: "capitalize" }}>
                  {key.replace(/_/g, ' ')}
                </Typography>
                <MetadataFieldValue value={value} />
              </Box>
            ))}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Renders a metadata field value based on its type
 */
function MetadataFieldValue({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: "italic" }}>
        Not found
      </Typography>
    );
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return (
        <Typography variant="body2" color="text.secondary">
          Empty list
        </Typography>
      );
    }

    if (typeof value[0] === 'object' && value[0] !== null) {
      return (
        <Stack spacing={1} sx={{ mt: 1 }}>
          {value.map((item, idx) => (
            <Box key={idx} sx={{ p: 1, borderRadius: 1, bgcolor: "grey.100" }}>
              <Typography variant="body2">
              {typeof item === 'object' ? JSON.stringify(item) : String(item)}
              </Typography>
            </Box>
          ))}
        </Stack>
      );
    }

    return (
      <Stack spacing={0.5} sx={{ mt: 0.5 }}>
        {value.map((item, idx) => (
          <Typography key={idx} variant="body2" color="text.secondary">
            - {String(item)}
          </Typography>
        ))}
      </Stack>
    );
  }

  if (typeof value === 'object' && value !== null) {
    return (
      <Box
        component="pre"
        sx={{
          mt: 1,
          p: 1,
          borderRadius: 1,
          bgcolor: "grey.100",
          overflowX: "auto",
          fontSize: 12,
        }}
      >
        {JSON.stringify(value, null, 2)}
      </Box>
    );
  }

  if (typeof value === 'boolean') {
    return <Chip size="small" color={value ? "success" : "default"} label={value ? "Yes" : "No"} />;
  }

  return (
    <Typography variant="body2" color="text.secondary">
      {String(value)}
    </Typography>
  );
}

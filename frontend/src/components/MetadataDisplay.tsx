import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';

interface Metadata {
  id: number;
  document_id: number;
  document_type: string;
  confidence_score: number;
  extracted_data: Record<string, any>;
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
        <CardHeader>
          <CardTitle>Extracted Metadata</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Extracting metadata...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-900">Metadata Extraction Failed</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-800">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!metadata) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Extracted Metadata</CardTitle>
          <CardDescription>No metadata has been extracted yet</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Extract metadata to see structured data from your document.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (metadata.extraction_error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-900">Extraction Failed</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-800">{metadata.extraction_error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Extracted Metadata</CardTitle>
          <Badge variant="outline" className="whitespace-nowrap">
            {metadata.document_type.toUpperCase()}
            <span className="ml-2 text-xs">
              {(metadata.confidence_score * 100).toFixed(0)}%
            </span>
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {Object.entries(metadata.extracted_data).length === 0 ? (
          <p className="text-sm text-muted-foreground">No fields extracted</p>
        ) : (
          <div className="space-y-4">
            {Object.entries(metadata.extracted_data).map(([key, value]) => (
              <div key={key} className="border-l-4 border-blue-200 pl-4">
                <p className="text-sm font-semibold text-gray-700 capitalize">
                  {key.replace(/_/g, ' ')}
                </p>
                <MetadataFieldValue value={value} />
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Renders a metadata field value based on its type
 */
function MetadataFieldValue({ value }: { value: any }) {
  if (value === null || value === undefined) {
    return <p className="text-sm text-muted-foreground italic">Not found</p>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <p className="text-sm text-muted-foreground">Empty list</p>;
    }

    // Check if array contains objects
    if (typeof value[0] === 'object' && value[0] !== null) {
      return (
        <ul className="mt-2 space-y-2">
          {value.map((item, idx) => (
            <li key={idx} className="rounded border border-gray-200 bg-gray-50 p-2 text-sm">
              {typeof item === 'object' ? JSON.stringify(item) : String(item)}
            </li>
          ))}
        </ul>
      );
    }

    // Simple array of values
    return (
      <ul className="mt-1 list-inside space-y-1">
        {value.map((item, idx) => (
          <li key={idx} className="text-sm text-gray-600">
            • {String(item)}
          </li>
        ))}
      </ul>
    );
  }

  if (typeof value === 'object' && value !== null) {
    return (
      <pre className="mt-2 overflow-x-auto rounded bg-gray-100 p-2 text-xs">
        {JSON.stringify(value, null, 2)}
      </pre>
    );
  }

  if (typeof value === 'boolean') {
    return (
      <Badge variant={value ? 'default' : 'secondary'}>
        {value ? 'Yes' : 'No'}
      </Badge>
    );
  }

  return <p className="text-sm text-gray-600">{String(value)}</p>;
}

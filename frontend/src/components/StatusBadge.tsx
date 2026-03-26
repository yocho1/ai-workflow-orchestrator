import { Chip, ChipProps } from "@mui/material";

interface StatusBadgeProps extends Omit<ChipProps, "label" | "color"> {
  status: string | null;
}

const statusConfig: Record<string, { label: string; color: ChipProps["color"] }> = {
  uploaded: {
    label: "📤 Uploaded",
    color: "default",
  },
  processing: {
    label: "⏳ Processing",
    color: "info",
  },
  classified: {
    label: "✅ Classified",
    color: "success",
  },
  completed: {
    label: "🎉 Completed",
    color: "success",
  },
  failed: {
    label: "❌ Failed",
    color: "error",
  },
};

export const StatusBadge = ({ status, ...chipProps }: StatusBadgeProps): JSX.Element => {
  if (!status || !(status in statusConfig)) {
    return <Chip label="Unknown" color="default" size="small" {...chipProps} />;
  }

  const config = statusConfig[status];

  return (
    <Chip
      label={config.label}
      color={config.color}
      size="small"
      {...chipProps}
    />
  );
};

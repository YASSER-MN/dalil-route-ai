interface Props {
  level: "Élevée" | "Moyenne" | "Faible";
}

const config: Record<Props["level"], { dot: string; label: string }> = {
  Élevée: { dot: "bg-green-600", label: "Confiance élevée" },
  Moyenne: { dot: "bg-amber-500", label: "Confiance moyenne" },
  Faible: { dot: "bg-accent", label: "Confiance faible" },
};

export default function ConfidenceBadge({ level }: Props) {
  const { dot, label } = config[level];
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted font-medium">
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
      {label}
    </span>
  );
}

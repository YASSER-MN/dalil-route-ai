"use client";

import { useState } from "react";
import { sendFeedback } from "@/lib/api";
import type { FeedbackRequest } from "@/lib/api";

interface Props {
  traceId: string;
}

type Rating = FeedbackRequest["rating"];

const buttons: Array<{ rating: Rating; label: string }> = [
  { rating: "helpful", label: "Utile" },
  { rating: "wrong", label: "Inexact" },
  { rating: "unsafe", label: "Dangereux" },
];

export default function FeedbackButtons({ traceId }: Props) {
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFeedback(rating: Rating) {
    try {
      await sendFeedback(traceId, rating);
      setSubmitted(true);
    } catch {
      setError("Impossible d'envoyer le retour.");
    }
  }

  if (submitted) {
    return <p className="mt-4 text-xs text-muted">Merci pour votre retour.</p>;
  }

  return (
    <div className="mt-5 flex flex-wrap items-center gap-2">
      <span className="text-xs text-muted">Cette réponse est :</span>
      {buttons.map(({ rating, label }) => (
        <button
          key={rating}
          onClick={() => handleFeedback(rating)}
          className="min-h-[44px] px-3 py-2 text-xs font-medium border border-ink/15 rounded hover:bg-ink/5 transition-colors"
        >
          {label}
        </button>
      ))}
      {error && <span className="text-xs text-accent">{error}</span>}
    </div>
  );
}

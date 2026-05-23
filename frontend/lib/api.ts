export interface Source {
  article_number: number;
  text: string;
  score: number;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
  valid: boolean;
  trace_id: string;
  pii_redacted: string[];
}

export interface FeedbackRequest {
  trace_id: string;
  rating: "helpful" | "wrong" | "unsafe";
  comment?: string;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function askDalil(question: string): Promise<AskResponse> {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    if (res.status === 429) {
      throw new Error(
        "Limite de requêtes atteinte. Veuillez réessayer dans une heure.",
      );
    }
    throw new Error(
      "Le service est temporairement indisponible. Veuillez réessayer.",
    );
  }

  return res.json() as Promise<AskResponse>;
}

export async function sendFeedback(
  trace_id: string,
  rating: FeedbackRequest["rating"],
  comment?: string,
): Promise<void> {
  const res = await fetch(`${API_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trace_id, rating, comment }),
  });

  if (!res.ok) {
    throw new Error("Impossible d'envoyer le retour. Veuillez réessayer.");
  }
}

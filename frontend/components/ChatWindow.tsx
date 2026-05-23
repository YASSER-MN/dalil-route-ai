"use client";

import { useState, useRef, useEffect } from "react";
import { askDalil } from "@/lib/api";
import type { AskResponse } from "@/lib/api";
import AnswerCard from "@/components/AnswerCard";

interface Message {
  id: string;
  question: string;
  response?: AskResponse;
  error?: string;
  pending: boolean;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    const id = crypto.randomUUID();
    setMessages((prev) => [...prev, { id, question, pending: true }]);
    setInput("");
    setLoading(true);

    try {
      const response = await askDalil(question);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id ? { ...m, response, pending: false } : m,
        ),
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id
            ? {
                ...m,
                error:
                  err instanceof Error ? err.message : "Erreur inconnue.",
                pending: false,
              }
            : m,
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 w-full max-w-3xl mx-auto px-4 py-6">
      <div className="flex-1 overflow-y-auto space-y-6 pb-4">
        {messages.length === 0 && (
          <div className="text-center text-muted text-sm mt-16 space-y-1">
            <p className="font-medium">
              Posez votre question sur le Code de la route
            </p>
            <p className="text-xs">
              Ex. : &laquo;&thinsp;Quelle est la limite de vitesse en
              agglomération ?&thinsp;&raquo;
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className="space-y-3">
            <div className="flex justify-end">
              <div className="bg-ink text-paper rounded-lg px-4 py-2.5 text-sm max-w-[80%] leading-relaxed">
                {msg.question}
              </div>
            </div>

            {msg.pending && (
              <div className="text-muted text-sm pl-1 animate-pulse">
                Recherche en cours…
              </div>
            )}

            {msg.error && (
              <div className="rounded-lg border border-accent/20 bg-accent/5 px-4 py-3 text-sm text-accent">
                {msg.error}
              </div>
            )}

            {msg.response && <AnswerCard response={msg.response} />}
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="mt-4 flex gap-2 items-end border-t border-ink/10 pt-4"
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void handleSubmit(e as unknown as React.FormEvent);
            }
          }}
          placeholder="Posez votre question sur le Code de la route marocain…"
          rows={2}
          disabled={loading}
          className="flex-1 resize-none rounded-lg border border-ink/20 bg-white px-4 py-3 text-sm placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-ink/20 leading-relaxed disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="min-h-[44px] px-5 py-2.5 rounded-lg bg-ink text-paper text-sm font-medium disabled:opacity-40 hover:bg-ink/90 transition-colors"
        >
          Envoyer
        </button>
      </form>
    </div>
  );
}

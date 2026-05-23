"use client";

import { useState } from "react";
import type { Source } from "@/lib/api";

interface Props {
  sources: Source[];
}

export default function SourcePanel({ sources }: Props) {
  const [open, setOpen] = useState<number | null>(null);

  if (sources.length === 0) return null;

  return (
    <div className="mt-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">
        Sources légales
      </p>
      <div className="space-y-1">
        {sources.map((src) => (
          <div
            key={src.article_number}
            className="border border-ink/10 rounded"
          >
            <button
              className="w-full flex justify-between items-center px-3 py-2.5 text-sm font-medium text-left hover:bg-ink/5 transition-colors"
              onClick={() =>
                setOpen(
                  open === src.article_number ? null : src.article_number,
                )
              }
              aria-expanded={open === src.article_number}
            >
              <span>Article {src.article_number}</span>
              <span className="text-muted text-xs ml-2">
                {open === src.article_number ? "▲" : "▼"}
              </span>
            </button>
            {open === src.article_number && (
              <div className="px-3 pb-3 pt-1 text-xs text-muted leading-relaxed border-t border-ink/10 max-w-[70ch]">
                {src.text}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

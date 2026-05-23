import ConfidenceBadge from "@/components/ConfidenceBadge";
import SourcePanel from "@/components/SourcePanel";
import FeedbackButtons from "@/components/FeedbackButtons";
import type { AskResponse } from "@/lib/api";

interface Props {
  response: AskResponse;
}

interface Section {
  title: string;
  content: string;
}

function parseSections(text: string): Section[] {
  const sections: Section[] = [];
  const re = /\*\*([^*\n]+?):\*\*/g;
  const indices: Array<{ title: string; matchIndex: number; contentStart: number }> = [];

  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    indices.push({ title: m[1].trim(), matchIndex: m.index, contentStart: m.index + m[0].length });
  }

  for (let i = 0; i < indices.length; i++) {
    const { title, contentStart } = indices[i];
    const contentEnd =
      i + 1 < indices.length ? indices[i + 1].matchIndex : text.length;
    const content = text.slice(contentStart, contentEnd).trim();
    sections.push({ title, content });
  }

  return sections;
}

function extractConfidence(
  sections: Section[],
): "Élevée" | "Moyenne" | "Faible" {
  const confidenceSection = sections.find((s) => s.title === "Confiance");
  const val = confidenceSection?.content ?? "";
  if (val.includes("Élevée") || val.includes("Elevée")) return "Élevée";
  if (val.includes("Faible")) return "Faible";
  return "Moyenne";
}

const SECTION_LABELS: Record<string, string> = {
  "Réponse courte": "Réponse",
  "Base légale": "Base légale",
  "Informations manquantes": "Informations manquantes",
};

export default function AnswerCard({ response }: Props) {
  const { answer, sources, valid, trace_id } = response;
  const sections = parseSections(answer);
  const confidence = extractConfidence(sections);

  const displaySections = sections.filter(
    (s) => s.title !== "Confiance" && s.title !== "Avertissement",
  );

  return (
    <div className="rounded-lg border border-ink/10 bg-white shadow-sm overflow-hidden">
      <div className="px-5 py-3.5 border-b border-ink/10 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted">
          Dalil Route
        </span>
        <ConfidenceBadge level={confidence} />
      </div>

      <div className="px-5 py-5 space-y-4">
        {sections.length > 0 ? (
          <>
            {displaySections.map((section) => (
              <div key={section.title}>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                  {SECTION_LABELS[section.title] ?? section.title}
                </p>
                <p className="text-sm text-ink leading-relaxed max-w-[70ch]">
                  {section.content}
                </p>
              </div>
            ))}
          </>
        ) : (
          <p className="text-sm text-ink leading-relaxed max-w-[70ch] whitespace-pre-wrap">
            {answer}
          </p>
        )}

        {!valid && (
          <p className="text-xs text-accent font-medium">
            Certaines citations n&apos;ont pas pu être vérifiées dans le corpus.
          </p>
        )}

        <SourcePanel sources={sources} />
        <FeedbackButtons traceId={trace_id} />
      </div>
    </div>
  );
}

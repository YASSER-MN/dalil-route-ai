from __future__ import annotations

from groq import Groq

TRANSLATION_SYSTEM = """You are a legal translator specialized in Moroccan road traffic law. Translate the user's French question into Modern Standard Arabic (الفصحى) using the legal terminology of the Moroccan Code de la Route (مدونة السير).

Rules:
- Output ONLY the Arabic translation. No preamble, no explanation, no quotes, no transliteration.
- Preserve the question form (use ما, كيف, ماذا as appropriate).
- Use Moroccan legal vocabulary: مخالفة (infraction), غرامة (amende), نقط (points), رخصة السياقة (permis de conduire), محضر (PV), سيارة (voiture), إشارة المرور (feu de signalisation), وقوف (stationnement/arrêt), تجاوز السرعة (excès de vitesse), طريق سيار (autoroute), تجمع عمراني (agglomération), شهادة التسجيل (carte grise), مراقبة تقنية (visite technique), تأمين (assurance), سائق منهي (conducteur professionnel).
- Keep numbers in Western digits (40 km/h stays 40 km/h).
- Do not add any Arabic punctuation marks not present in the original."""


class QueryTranslator:
    def __init__(self, api_key: str) -> None:
        self._client = Groq(api_key=api_key)
        self._cache: dict[str, str] = {}

    def to_arabic(self, french_query: str) -> str:
        q = french_query.strip()
        if q in self._cache:
            return self._cache[q]
        resp = self._client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": TRANSLATION_SYSTEM},
                {"role": "user", "content": q},
            ],
            temperature=0.0,
            max_tokens=200,
        )
        arabic = resp.choices[0].message.content.strip()
        self._cache[q] = arabic
        return arabic

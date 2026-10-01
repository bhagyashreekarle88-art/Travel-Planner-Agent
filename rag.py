"""
Retrieval-Augmented Generation (RAG) layer.

Pipeline:  load guides -> chunk by section (and per attraction) -> TF-IDF index
           -> cosine-similarity retrieval filtered by destination -> context
           block passed to the Itinerary Agent's prompt.

TF-IDF is used instead of neural embeddings so the prototype runs free,
offline and deterministically. The `Retriever` interface (index / retrieve)
is the same one you would keep if you swapped in sentence-transformer or
OpenAI embeddings + a vector DB such as FAISS or Chroma.
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = Path(__file__).resolve().parent  # destination guides are the kb_*.md files next to this script


@dataclass
class Chunk:
    chunk_id: str
    city: str
    section: str
    text: str
    meta: dict = field(default_factory=dict)


def _month_range(a: int, b: int) -> list[int]:
    """months 11-4 -> [11, 12, 1, 2, 3, 4] (wraps around the year)."""
    return list(range(a, b + 1)) if a <= b else list(range(a, 13)) + list(range(1, b + 1))


def parse_attraction(line: str, city: str) -> dict | None:
    """'- Name | setting | tags | hours | cost | best | area | description [| availability]' -> dict

    availability (optional) e.g. "months 11-4; days Sat,Sun" for seasonal or weekly openings."""
    parts = [p.strip() for p in line.lstrip("- ").split("|")]
    if len(parts) not in (8, 9):
        return None
    name, setting, tags, hours, cost, best, area, desc = parts[:8]
    avail = parts[8] if len(parts) == 9 else ""
    months = re.search(r"months\s+(\d+)-(\d+)", avail)
    days = re.search(r"days\s+([A-Za-z,]+)", avail)
    return {
        "open_months": _month_range(int(months.group(1)), int(months.group(2))) if months else list(range(1, 13)),
        "open_days": [d.strip()[:3].title() for d in days.group(1).split(",")] if days else
                     ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "name": name, "city": city, "setting": setting,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "hours": float(hours), "cost_inr": int(cost), "best_time": best,
        "area": area, "description": desc,
    }


def load_chunks(kb_dir: Path = KB_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(kb_dir.glob("kb_*.md")):
        text = path.read_text(encoding="utf-8")
        city = re.search(r"^# (.+)$", text, re.M).group(1).strip()
        sections = re.split(r"^## ", text, flags=re.M)[1:]
        for sec in sections:
            title, _, body = sec.partition("\n")
            title, body = title.strip(), body.strip()
            if title == "Attractions":
                for i, line in enumerate(l for l in body.splitlines() if l.startswith("- ")):
                    a = parse_attraction(line, city)
                    if a:
                        a["source"] = f"{city}:attr:{i}"
                        text_repr = (f"{a['name']} ({a['area']}, {city}) - {a['description']} "
                                     f"Type: {a['setting']}; tags: {', '.join(a['tags'])}; "
                                     f"about {a['hours']} h; approx entry INR {a['cost_inr']}; "
                                     f"best in the {a['best_time']}."
                                     + ("" if len(a["open_months"]) == 12 else f" Open months: {a['open_months']}.")
                                     + ("" if len(a["open_days"]) == 7 else f" Open days: {', '.join(a['open_days'])}."))
                        chunks.append(Chunk(f"{city}:attr:{i}", city, "Attractions", text_repr, a))
            else:
                chunks.append(Chunk(f"{city}:{title}", city, title, f"{city} - {title}: {body}"))
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform([c.text for c in chunks])

    def retrieve(self, query: str, city: str | None = None, k: int = 6,
                 section: str | None = None) -> list[tuple[Chunk, float]]:
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.matrix).ravel()
        ranked = sorted(range(len(self.chunks)), key=lambda i: -scores[i])
        out = []
        for i in ranked:
            c = self.chunks[i]
            if city and c.city != city:
                continue
            if section and c.section != section:
                continue
            out.append((c, float(scores[i])))
            if len(out) >= k:
                break
        return out

    def attractions(self, city: str) -> list[dict]:
        return [c.meta for c in self.chunks if c.city == city and c.section == "Attractions"]

    def section(self, city: str, title: str) -> str:
        for c in self.chunks:
            if c.city == city and c.section == title:
                return c.text.split(": ", 1)[-1]
        return ""


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever(load_chunks())


def format_context(results: list[tuple[Chunk, float]]) -> str:
    """Numbered context block with source IDs so the LLM can cite them."""
    return "\n".join(f"[{c.chunk_id}] {c.text}" for c, _ in results)

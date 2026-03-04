from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class RetrievalHit:
    label: str
    score: float


def retrieve_similar(query: str, corpus: list[str], labels: list[str], top_k: int = 3) -> list[RetrievalHit]:
    if not corpus:
        return []
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus + [query])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
    return [RetrievalHit(label=labels[idx], score=float(score)) for idx, score in ranked]


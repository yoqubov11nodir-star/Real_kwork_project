"""
Smart Matchmaking - AI orqali frilanser va buyurtma mosligini hisoblash.
OpenAI text-embedding-3-small yoki Sentence-Transformers ishlatiladi.
Agar ikkalasi ham mavjud bo'lmasa, TF-IDF asosida fallback ishlaydi.
"""
import math
import json
from django.conf import settings


def cosine_similarity(vec1: list, vec2: list) -> float:
    """Ikki vektor orasidagi cosine similarity hisoblash."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a ** 2 for a in vec1))
    magnitude2 = math.sqrt(sum(b ** 2 for b in vec2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)


def get_embedding_openai(text: str) -> list | None:
    """OpenAI text-embedding-3-small orqali embedding olish."""
    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception:
        return None


def get_embedding_local(text: str) -> list | None:
    """Sentence-Transformers orqali lokal embedding (bepul)."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception:
        return None


def get_embedding_tfidf(text: str, all_texts: list = None) -> list:
    """
    TF-IDF asosida oddiy embedding (fallback).
    Hech qanday kutubxona kerak emas.
    """
    import re
    from collections import Counter

    def tokenize(t):
        return re.findall(r'\b\w+\b', t.lower())

    tokens = tokenize(text)
    freq = Counter(tokens)
    vocab = sorted(set(tokens))
    vector = [freq.get(word, 0) for word in vocab]
    return vector


def get_embedding(text: str) -> list:
    """
    Eng yaxshi mavjud usul bilan embedding olish.
    Tartib: OpenAI → Sentence-Transformers → TF-IDF
    """
    if settings.OPENAI_API_KEY:
        emb = get_embedding_openai(text)
        if emb:
            return emb

    emb = get_embedding_local(text)
    if emb:
        return emb

    # Fallback: oddiy keyword matching
    return get_embedding_tfidf(text)


def calculate_match_score(freelancer_profile, vacancy) -> float:
    """
    Frilanser va vakansiya o'rtasidagi moslik foizini hisoblash.

    Args:
        freelancer_profile: Profile modeli instance
        vacancy: Vacancy modeli instance

    Returns:
        float: 0.0 dan 1.0 gacha moslik ball (1.0 = 100% mos)
    """
    # Frilanser matnini tayyorlash
    freelancer_text = f"""
    Skills: {freelancer_profile.skills}
    Bio: {freelancer_profile.bio}
    """.strip()

    # Vakansiya matnini tayyorlash
    vacancy_text = f"""
    {vacancy.title}
    {vacancy.description}
    Required skills: {vacancy.required_skills}
    """.strip()

    if not freelancer_text or not vacancy_text:
        return 0.0

    try:
        freelancer_embedding = get_embedding(freelancer_text)
        vacancy_embedding = get_embedding(vacancy_text)

        # Vektorlar uzunligi teng bo'lishi kerak
        min_len = min(len(freelancer_embedding), len(vacancy_embedding))
        if min_len == 0:
            return 0.0

        # Vektorlarni bir xil uzunlikka keltirish (TF-IDF uchun)
        if len(freelancer_embedding) != len(vacancy_embedding):
            # So'z asosidagi oddiy moslik
            return _keyword_match_score(freelancer_profile, vacancy)

        score = cosine_similarity(freelancer_embedding, vacancy_embedding)
        return max(0.0, min(1.0, score))

    except Exception:
        return _keyword_match_score(freelancer_profile, vacancy)


def _keyword_match_score(freelancer_profile, vacancy) -> float:
    """Kalit so'z asosidagi oddiy moslik hisoblash (fallback)."""
    freelancer_skills = set(
        s.lower().strip()
        for s in freelancer_profile.get_skills_list()
    )
    required_skills = set(
        s.lower().strip()
        for s in vacancy.get_skills_list() # Bu erda vacancy ishlatildi
    )
    bio_words = set(freelancer_profile.bio.lower().split())
    desc_words = set(vacancy.description.lower().split())

    if not required_skills and not desc_words:
        return 0.5

    skill_match = 0.0
    if required_skills:
        matched = freelancer_skills & required_skills
        skill_match = len(matched) / len(required_skills)

    text_match = 0.0
    if desc_words and bio_words:
        common = bio_words & desc_words
        text_match = len(common) / len(desc_words) if desc_words else 0

    # 70% skill, 30% bio text
    return min(1.0, skill_match * 0.7 + text_match * 0.3)


# Fayl boshida:
def get_top_workers_for_vacancy(vacancy, limit=10):
    from marketplace.models import Profile
    workers = Profile.objects.filter(
        role='freelancer'
    ).select_related('user')

    results = []
    for profile in workers:
        score = calculate_match_score(profile, vacancy)
        results.append({
            'profile': profile,
            'score': score,
            'score_percent': round(score * 100, 1),
        })
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def calculate_match_score(freelancer_profile, vacancy):
    freelancer_text = f"Skills: {freelancer_profile.skills}\nBio: {freelancer_profile.bio}"
    vacancy_text = f"{vacancy.title}\n{vacancy.description}\nRequired: {vacancy.required_skills}"

    if not freelancer_text.strip() or not vacancy_text.strip():
        return 0.0

    try:
        fe = get_embedding(freelancer_text)
        ve = get_embedding(vacancy_text)
        if len(fe) != len(ve):
            return _keyword_match_score(freelancer_profile, vacancy)
        return max(0.0, min(1.0, cosine_similarity(fe, ve)))
    except Exception:
        return _keyword_match_score(freelancer_profile, vacancy)


def _keyword_match_score(freelancer_profile, vacancy):
    worker_skills = set(s.lower().strip() for s in freelancer_profile.get_skills_list())
    required = set(s.lower().strip() for s in vacancy.get_skills_list())
    if not required:
        return 0.5
    matched = worker_skills & required
    return len(matched) / len(required)
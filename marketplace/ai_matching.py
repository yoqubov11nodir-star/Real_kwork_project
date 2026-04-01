import math

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("AI model yuklanmoqda... (faqat bir marta)")
            _model = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2'
            )
            print("✅ AI model tayyor!")
        except ImportError:
            _model = "keyword"  
    return _model


def cosine_similarity(vec1, vec2):
    dot = sum(a * b for a, b in zip(vec1, vec2))
    m1 = math.sqrt(sum(a ** 2 for a in vec1))
    m2 = math.sqrt(sum(b ** 2 for b in vec2))
    if m1 == 0 or m2 == 0:
        return 0.0
    return dot / (m1 * m2)


def get_embedding(text):
    model = get_model()
    if model == "keyword":
        return None
    try:
        return model.encode(text).tolist()
    except Exception:
        return None


def calculate_match_score(freelancer_profile, vacancy):
    worker_text = f"Skills: {freelancer_profile.skills}\nBio: {freelancer_profile.bio}"
    vacancy_text = f"{vacancy.title}\n{vacancy.description}\nRequired: {vacancy.required_skills}"

    if not worker_text.strip() or not vacancy_text.strip():
        return 0.0

    we = get_embedding(worker_text)
    ve = get_embedding(vacancy_text)

    if we and ve and len(we) == len(ve):
        return max(0.0, min(1.0, cosine_similarity(we, ve)))

    return _keyword_match(freelancer_profile, vacancy)


def _keyword_match(profile, vacancy):
    worker_skills = set(s.lower().strip() for s in profile.get_skills_list())
    required = set(s.lower().strip() for s in vacancy.get_skills_list())
    if not required:
        return 0.5
    matched = worker_skills & required
    return len(matched) / len(required)


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
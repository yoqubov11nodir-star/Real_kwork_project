# FreelanceUZ — Django Marketplace

## Loyiha haqida
Kwork analogidagi O'zbekiston frilanserlar platformasi:
- **AI Smart Matchmaking** — Frilanser ko'nikmalari va buyurtma tavsifini vector embedding bilan solishtiradi
- **Real-time Chat** — Django Channels + WebSocket orqali jonli xabar almashish
- **Narx kelishish (Offer)** — Frilanser narx/muddat yuboradi, mijoz Accept qilmagunicha loyiha boshlanmaydi
- **Vaqt nazorati** — Celery + Redis bilan avtomatik DELAYED status
- **Leveling tizimi** — Level 1/2/3, nishonlar (Badges), reyting
- **Mijoz review** ko'ra oladi muzokaradan oldin

---

## O'rnatish

### 1. Virtual muhit yaratish
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate       # Windows
```

### 2. Kutubxonalar o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Redis o'rnatish (kerak — Channels + Celery uchun)
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# Mac
brew install redis && brew services start redis

# Docker bilan (oson)
docker run -d -p 6379:6379 redis:alpine
```

### 4. .env fayl yaratish (ixtiyoriy)
```bash
OPENAI_API_KEY=sk-...    # Agar OpenAI ishlatilsa
```

### 5. Migratsiyalar
```bash
python manage.py makemigrations marketplace negotiation reputation
python manage.py migrate
```

### 6. Superuser yaratish
```bash
python manage.py createsuperuser
```

### 7. Ishga tushirish

**Terminal 1 — Django (Daphne ASGI):**
```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Terminal 2 — Celery worker:**
```bash
celery -A config worker -l info
```

**Terminal 3 — Celery beat (schedule):**
```bash
celery -A config beat -l info
```

---

## URL Tuzilishi

| URL | Nomi | Tavsif |
|-----|------|--------|
| `/` | Home | Bosh sahifa |
| `/marketplace/` | home | Asosiy |
| `/marketplace/orders/` | order_list | Buyurtmalar ro'yxati |
| `/marketplace/orders/create/` | order_create | Yangi buyurtma |
| `/marketplace/orders/<pk>/` | order_detail | Buyurtma detail + AI match |
| `/marketplace/profile/<username>/` | profile | Profil |
| `/marketplace/dashboard/` | dashboard | Dashboard |
| `/negotiation/chats/` | my_chats | Chatlar |
| `/negotiation/chat/<pk>/` | chat_room | Real-time chat |
| `/negotiation/chat/create/<order_pk>/` | create_chat_room | Chat boshlash |
| `/reputation/leaderboard/` | leaderboard | Top frilanserlar |
| `/reputation/review/create/<pk>/` | create_review | Baho berish |
| `/auth/login/` | login | Kirish |
| `/auth/register/` | register | Ro'yxatdan o'tish |
| `/admin/` | admin | Admin panel |

---

## AI Matchmaking

**3 bosqichli fallback:**

1. **OpenAI** `text-embedding-3-small` — Agar `OPENAI_API_KEY` bo'lsa
2. **Sentence-Transformers** `paraphrase-multilingual-MiniLM-L12-v2` — Lokal (bepul, multilingual)
3. **Keyword matching** — Hech biri bo'lmasa oddiy kalit so'z taqqoslash

**Ishlatish:** `marketplace/ai_matching.py` → `calculate_match_score(profile, order)`

---

## Leveling Tizimi

| Level | Shart |
|-------|-------|
| Level 1 | Default (yangi) |
| Level 2 | 5+ ish + 4.5+ reyting |
| Level 3 | 20+ ish |

---

## API Endpoints (DRF)

- `GET /api/marketplace/orders/` — Buyurtmalar
- `GET /api/marketplace/orders/<pk>/top_freelancers/` — AI tavsiyalar
- `GET /api/reputation/reviews/?username=<user>` — Sharhlar
- `GET /api/negotiation/rooms/` — Chat xonalari

---

## Struktura

```
kwork_marketplace/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── celery.py
│   └── wsgi.py
├── marketplace/
│   ├── models.py          # Profile, Order
│   ├── views.py
│   ├── ai_matching.py     # ★ AI moslik tizimi
│   ├── forms.py
│   ├── urls.py
│   ├── auth_urls.py
│   ├── api_urls.py
│   ├── api_views.py
│   └── serializers.py
├── negotiation/
│   ├── models.py          # ChatRoom, Message, Offer
│   ├── views.py
│   ├── consumers.py       # WebSocket consumer
│   ├── tasks.py           # Celery tasks
│   ├── routing.py
│   └── ...
├── reputation/
│   ├── models.py          # Review, Badge, LevelHistory
│   ├── views.py
│   └── ...
├── templates/
│   ├── base/base.html
│   ├── marketplace/
│   ├── negotiation/
│   └── reputation/
├── manage.py
└── requirements.txt
```

# 🧠 Focus Journal – Backend

Focus Journal is a productivity and self-reflection journal platform designed to help users track their focus, mood, goals, and personal growth through structured journaling and insightful analytics.

---

## 🚀 Tech Stack

- **Backend Framework:** FastAPI (async)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy Core (via reflection)
- **Caching:** Redis (Upstash)
- **Authentication:** OTP-based, JWT
- **Queue System:** Redis (mocked queue support)
- **Payment Gateway:** Stripe (for future premium features)

---

## ✅ Features

### 🔐 Authentication
- OTP-based login via email
- Google, GitHub, LinkedIn OAuth (planned)
- JWT-protected routes

### 📓 Journal Entries
- `POST /journal` – Add new journal entry
- `GET /journal` – List all journal entries
- `GET /journal/{id}` – Get single journal entry
- `DELETE /journal/{id}` – Delete journal entry

### 📅 Calendar View
- `GET /journal/calendar` – Fetch entries organized by date

### 🔍 Search & Tags
- `GET /journal/search?keyword=` – Search journal entries by keyword
- `GET /journal/tags` – Frequently used tags

### 📈 Journal Insights
- `GET /journal/insights` – AI-powered insights (focus %, mood, keywords)
- `GET /journal/sentiment-analysis` – Sentiment trend over time (Premium)
- `GET /journal/summary/weekly` – Weekly summary (Premium)
- `POST /journal/compare` – Compare two time ranges (Premium)

### 🔥 Daily Streaks & Goal Setting
- `GET /streak` – Current & longest journal streak
- `POST /goal` – Set or update personal productivity goals
- `GET /goal` – View current goal

### 💬 Chatroom (Gemini-style AI Copilot)
- `GET /chatroom` – List all chatrooms
- `GET /chatroom/{id}` – Chatroom details + messages
- `POST /chatroom/{id}/message` – Send message, receive AI response (async)
- Messages are queued and handled asynchronously

### 💳 Subscription & Payments
- `POST /subscribe/pro` – Subscribe to premium (Stripe)
- `GET /subscription/status` – Check current subscription status
- `POST /webhook/stripe` – Stripe webhook handler

---

## 🧪 API Response Format

All APIs return consistent responses:
```json
{
  "message": "Success message",
  "data": { ... }
}

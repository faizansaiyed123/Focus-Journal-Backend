# 📘 Focus Journal — Complete Feature & API Breakdown (Explained in Detail)

This document lists **all features** (including **unique ones**) of the Focus Journal platform — with clear explanations for each feature's **purpose, value, and API implementation**.

---

## ✅ 1. Authentication (Signup, Login, Change Password)

### 💡 What & Why
Allow users to securely sign up, log in using OAuth (Google, GitHub, LinkedIn), and change their password for account safety.

### APIs
- `POST /auth/register`: Signup using email, Google, LinkedIn
- `POST /auth/login`: JWT login
- `POST /auth/login/github`: GitHub login
- `POST /auth/change-password`: Securely change current password (requires old password)

---

## ✅ 2. Journal Entries

### 💡 What & Why
Users write daily journals (title, body, tags). Helps reflection and tracking mental health, productivity, habits, etc.

### APIs
- `GET /journal/`: List all entries for the user
- `POST /journal/`: Create a new journal entry
- `GET /journal/{entry_id}`: Get single entry by ID
- `PUT /journal/{entry_id}`: Update an entry
- `DELETE /journal/{entry_id}`: Delete an entry

---

## ✅ 3. Daily Mood + Focus Tracker

### 💡 What & Why
Track how users feel and how focused they were each day (0-100 scale). Great for trend analytics and wellbeing insights.

### APIs
- `POST /daily/checkin`: Submit today's mood and focus %
- `GET /daily/today`: Get today’s check-in (if already done)
- `GET /daily/history`: Get entire history of daily mood/focus check-ins

---

## ✅ 4. Analytics Dashboard

### 💡 What & Why
Visual dashboards that summarize patterns like:
- Average mood/focus over time
- Most used tags
- Most productive days
- Mood → Tag correlation

### APIs
- `GET /analytics/summary`: Avg. mood/focus, top tags, etc.
- `GET /analytics/trends`: Weekly/Monthly chart data
- `GET /analytics/tags`: Breakdown of tags and their frequency

---

## ✅ 5. AI Copilot (Unique!)

### 💡 What & Why
LLM-based AI that assists with journaling:
- Auto-analyze your entries
- Suggest improvements
- Auto-tag & generate title
- Ask reflective questions

### APIs
- `POST /copilot/ask`: User chats with AI ("What can I improve?")
- `POST /copilot/review`: AI reviews an entry and gives feedback
- `POST /copilot/suggestions`: Suggests habits, title, tags from entry

---

## ✅ 6. Goal System (SMART + Weekly Review)

### 💡 What & Why
Set SMART (Specific, Measurable, Achievable...) goals, and review them weekly. Encourages self-growth and reflection.

### APIs
- `GET /goals`: List user goals
- `POST /goals`: Create a new goal
- `GET /goals/{id}`: Get one goal
- `PUT /goals/{id}`: Update a goal
- `DELETE /goals/{id}`: Delete goal
- `GET /goals/weekly-review`: Summary of weekly goal progress + reflection prompts

---

## ✅ 7. Subscription (Stripe Integration)

### 💡 What & Why
Free users get basic features. Pro users get AI Copilot, full analytics, unlimited goals, etc.

### APIs
- `POST /subscribe/pro`: Redirects to Stripe checkout
- `GET /subscription/status`: Check if user is Pro
- `POST /webhook/stripe`: Stripe webhook to handle upgrade/downgrade

---

## ✅ 8. User Profile & Settings

### 💡 What & Why
Manage user profile settings such as name, timezone, journal visibility, and preferred AI model.

### APIs
- `GET /profile`: Get current profile
- `PUT /profile/update`: Update profile fields
- `POST /auth/change-password`: Secure password change

---

## ⭐️ 9. Journal Streak Tracker (Unique)

### 💡 What & Why
Encourages consistency by tracking how many days in a row the user has written a journal.

### APIs
- `GET /streak`: Get current streak count
- Calculated automatically during `/journal/` creation

---

## ⭐️ 10. Distraction Log (Unique)

### 💡 What & Why
Let users log distractions during the day (category, time). Over time, AI will help reduce them.

### APIs
- `POST /distraction`: Log a new distraction
- `GET /distraction`: List all distractions
- `GET /distraction/summary`: Most common times, categories

---

## ⭐️ 11. Gratitude Journal (Unique)

### 💡 What & Why
Separate section to log 3 things the user is grateful for every day — improves mood & perspective.

### APIs
- `POST /gratitude`: Log daily gratitude
- `GET /gratitude/today`: See today’s gratitude log
- `GET /gratitude/history`: Full gratitude history

---

## ⭐️ 12. Energy Level Tracker (Unique)

### 💡 What & Why
Track energy level (0-10) multiple times daily — correlates with mood, focus, goals.

### APIs
- `POST /energy`: Log energy level (with time)
- `GET /energy/today`: Current day's log
- `GET /energy/summary`: Trend and chart data

---

## ⭐️ 13. Monthly Review Prompts (Unique)

### 💡 What & Why
At month-end, prompt user to write about:
- Wins
- Learnings
- Challenges
- Goals for next month

### APIs
- `GET /review/monthly`: Get prompts
- `POST /review/monthly`: Submit answers

---

## ⭐️ 14. Distraction-to-Focus AI Coach (Unique)

### 💡 What & Why
Based on past distractions, suggest techniques (like Pomodoro, breathing, etc.) via AI.

### APIs
- `GET /focus/coach`: AI-generated focus advice
- `POST /focus/update`: Feedback loop to improve suggestions

---

## ⭐️ 15. AI-Driven Weekly Digest (Unique)

### 💡 What & Why
Summarize past week's:
- Mood/focus trend
- Journal highlights
- AI review of tone/emotions

### APIs
- `GET /digest/weekly`: AI-written digest from past week
- `POST /digest/send`: Trigger sending email/report

---

## ⭐️ 16. Tag Intelligence & Auto Suggest (Unique)

### 💡 What & Why
AI auto-tags journal entries or suggests new tags based on content.

### APIs
- Auto-run during `/journal/` creation or via:
- `POST /tags/suggest`: Get AI-suggested tags

---

## ⭐️ 17. Archive / Export Journals (Unique)

### 💡 What & Why
Let users export all their journal entries as PDF, DOCX, or JSON.

### APIs
- `GET /export/pdf`
- `GET /export/json`
- `GET /export/docx`

---

## ⭐️ 18. Journal Search + Filters (Unique)

### 💡 What & Why
Let users search entries by keyword, date range, tag, or mood.

### APIs
- `GET /journal/search?keyword=&tag=&mood=`

---

## ⭐️ 19. Time-of-Day Reflection (Unique)

### 💡 What & Why
Users reflect in morning and evening. AI can later compare mindset shift.

### APIs
- `POST /reflection/morning`: Morning reflection
- `POST /reflection/evening`: Evening reflection
- `GET /reflection/compare`: See shift between them

---

## ⭐️ 20. Milestone Celebrations (Unique)

### 💡 What & Why
Celebrate 7-day, 30-day, 100-day streaks with animations, badges, or emails.

### APIs
- `GET /milestone/status`: Current milestone progress
- Trigger celebration on backend when reached

---

> ✅ **All of the features marked `⭐️` are unique or very rare in other journaling platforms** like Day One, Journey, Penzu, or Stoic.

---

## 🧠 Final Notes

- All APIs follow **JWT Auth**, **async DB access**, and **consistent response format**
- AI features will use OpenAI or Claude (via queue-based async architecture)
- Each feature can be built, tested, and deployed independently

---
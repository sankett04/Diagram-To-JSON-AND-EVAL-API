# Image to JSON API

FastAPI backend for converting answer sheet images to JSON and evaluating student responses. Designed to integrate with Next.js frontend.


## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
```
bash
pip install -r requirements.txt
```

2. **Run the server:**
```
bash
uvicorn app:app --reload
```

3. **API will be available at:** `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/`

---

## 📡 API Endpoints

Link : https://diagram-to-json-and-eval-api.onrender.com/docs
### 1. Teacher Upload

```
http
POST /api/teacher/upload
Content-Type: multipart/form-data

Parameters:
- question_id: string (e.g., "Q1")
- teacher_id: string (e.g., "T001")
- file: image (PNG, JPG, JPEG)
```

### 2. Student Upload (Get Score)
```
http
POST /api/student/upload
Content-Type: multipart/form-data

Parameters:
- student_id: string (e.g., "S001")
- question_id: string (e.g., "Q1")
- file: image (PNG, JPG, JPEG)

Response:
{
  "success": true,
  "data": {
    "score": 8.5,
    "features": {
      "keyword_match_ratio": 0.9,
      "edge_match_ratio": 0.85,
      ...
    },
    "student_json": {...},
    "teacher_json": {...}
  }
}
```

### 3. Get Teacher Answer
```
http
GET /api/teacher/answer/{question_id}
```

### 4. Get Student Results
```
http
GET /api/student/results
GET /api/student/results/{student_id}
```

---


## 🔧 Environment Variables

Create a `.env` file:
```
env
DATABASE_URL=postgresql://user:password@localhost:5432/examdb
API_KEY=your-api-key-here
OPENAI_API_KEY=your-openai-key
```

---

## 🔄 Next.js Integration Example

```
typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function uploadTeacherAnswer(
  questionId: string,
  teacherId: string,
  file: File
) {
  const formData = new FormData();
  formData.append('question_id', questionId);
  formData.append('teacher_id', teacherId);
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/teacher/upload`, {
    method: 'POST',
    body: formData,
  });
  
  return res.json();
}

export async function uploadStudentAnswer(
  studentId: string,
  questionId: string,
  file: File
) {
  const formData = new FormData();
  formData.append('student_id', studentId);
  formData.append('question_id', questionId);
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/student/upload`, {
    method: 'POST',
    body: formData,
  });
  
  return res.json();
}
```

---

## 📦 Production Deployment Options

### Option 1: Railway
```bash
# Connect GitHub repo, set environment variables
railway init
railway deploy
```

### Option 2: Render
```
bash
# Connect GitHub repo, automatically deploys on push
# Set start command: uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Option 3: Fly.io
```
bash
fly launch
fly deploy
```

---

## 📁 Project Structure

```
imgtojson/
├── app.py                  # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container
├── docker-compose.yml     # Docker Compose config
├── README.md             # This file
├── Module/
│   ├── imgtojson.py      # Image to JSON conversion
│   ├── ExtractFeatures.py # Feature extraction
│   └── mlmodel/          # ML models
└── .env                  # Environment variables (create)
```

---

## ⚠️ Notes

- Currently uses in-memory storage. For production, integrate with a database (PostgreSQL recommended).
- Teacher answer must be uploaded before student answers for a given question.
- The ML model is loaded from `Module/mlmodel/EvaluateScoreXG.joblib`.
"# Diagram-To-JSON-AND-EVAL-API" 

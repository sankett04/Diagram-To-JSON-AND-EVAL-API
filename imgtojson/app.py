import os
import tempfile
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
from motor.motor_asyncio import AsyncIOMotorClient

# Importing updated async functions
from Module.imgtojson import image_to_json
from Module.ExtractFeatures import evaluate_diagram

# ============================================
# DATABASE SETUP (MongoDB)
# ============================================
# Use environment variables for secrets in production!
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://sankettalele:Diagrameval@backend.hzwnqoj.mongodb.net/?appName=Backend")
DB_NAME = "Score"

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db_helper = MongoDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    db_helper.client = AsyncIOMotorClient(MONGO_URL)
    db_helper.db = db_helper.client[DB_NAME]
    print(f"✅ Connected to MongoDB Atlas - Database: {DB_NAME}")
    yield
    # Shutdown: Close connection
    db_helper.client.close()
    print("❌ MongoDB connection closed")

app = FastAPI(
    title="Image to JSON API (MongoDB Edition)",
    description="API for converting answer sheet images to JSON and evaluating student responses",
    version="1.1.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ML MODEL LOADING
# ============================================
MODEL_PATH = "Module/mlmodel/EvaluateScoreXG.joblib"
try:
    model = joblib.load(MODEL_PATH)
    print("✅ ML Model loaded successfully")
except Exception as e:
    print(f"Warning: Could not load model: {e}")
    model = None

# ============================================
# HELPER FUNCTIONS
# ============================================
def format_doc(doc):
    """Helper to make MongoDB docs JSON serializable (converts ObjectId to str)"""
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

@app.get("/")
def root():
    return {"status": "running", "database": "MongoDB Atlas"}

# ============================================
# BACKGROUND TASK FUNCTION
# ============================================
async def process_teacher_image_async(temp_path: str, question_id: str, teacher_id: str):
    """Processes the image and updates the DB in the background"""
    try:
        # Call the async HuggingFace function
        teacher_json = await image_to_json(temp_path)
        
        # MongoDB Upsert
        await db_helper.db.teacher_answers.update_one(
            {"question_id": question_id, "teacher_id": teacher_id},
            {
                "$set": {
                    "teacher_json": teacher_json,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
        print(f"✅ Teacher answer processed for Q:{question_id}")
    except Exception as e:
        print(f"❌ Background processing failed: {e}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ============================================
# TEACHER ENDPOINT
# ============================================
@app.post("/api/teacher/upload")
async def teacher_upload(
    background_tasks: BackgroundTasks,
    question_id: str = Form(...),
    teacher_id: str = Form(...),
    file: UploadFile = File(...)
):
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    # Save file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        content = await file.read()
        tmp.write(content)
        temp_path = tmp.name
    
    # Schedule background task
    background_tasks.add_task(process_teacher_image_async, temp_path, question_id, teacher_id)
    
    return {
        "success": True, 
        "message": "Image received, processing in background.",
        "data": {"teacher_id": teacher_id, "question_id": question_id}
    }

# ============================================
# STUDENT ENDPOINT
# ============================================
@app.post("/api/student/upload")
async def student_upload(
    student_id: str = Form(...),
    question_id: str = Form(...),
    file: UploadFile = File(...)
):
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type.")
    # Fetch teacher answer from MongoDB
    teacher_data = await db_helper.db.teacher_answers.find_one({"question_id": question_id})
    
    if not teacher_data:
        raise HTTPException(status_code=404, detail="Teacher answer not found for this question.")
    
    teacher_json = teacher_data["teacher_json"]
    teacher_id = teacher_data["teacher_id"]

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        
        # --- FIX: Await the async function here ---
        student_json = await image_to_json(temp_path) 
        
        # ---
        features = evaluate_diagram(student_json, teacher_json)
        
        # Scoring Logic
        if model is not None:
            features_array = pd.DataFrame([features])
            pred_score = model.predict(features_array)[0]
            score_out_of_10 = float(round(pred_score / 10, 2))
        else:
            score_out_of_10 = round((features["keyword_match_ratio"] * 0.6 + features["edge_match_ratio"] * 0.4) * 10, 2)
        
        # Store Result in MongoDB
        result_doc = {
            "student_id": student_id,
            "question_id": question_id,
            "teacher_id": teacher_id,
            "score": score_out_of_10,
            "features": features,
            "student_json": student_json,
            "created_at": datetime.now()
        }
        await db_helper.db.student_results.insert_one(result_doc)
        
        os.remove(temp_path)
        return {"success": True, "score": score_out_of_10, "data": {"student_id": student_id, "features": features}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# QUERY ENDPOINTS
# ============================================
@app.get("/api/student/results/{student_id}")
async def get_student_results(student_id: str):
    cursor = db_helper.db.student_results.find({"student_id": student_id}).sort("created_at", -1)
    results = [format_doc(doc) async for doc in cursor]
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found.")
    return {"success": True, "data": results}

@app.get("/api/student/results")
async def get_all_results():
    cursor = db_helper.db.student_results.find().sort("created_at", -1)
    results = [format_doc(doc) async for doc in cursor]
    return {"success": True, "data": results}

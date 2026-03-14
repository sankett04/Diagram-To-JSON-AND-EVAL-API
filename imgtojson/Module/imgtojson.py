import os
import base64
import json
import asyncio
from openai import AsyncOpenAI  # <-- Use AsyncOpenAI
from PIL import Image
from io import BytesIO

# It is better to load the API key from an environment variable
HF_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

# Initialize the Async client
client = AsyncOpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_API_KEY,
)

async def image_to_json(image_path: str) -> dict:                # <-- Marked as async
    # Convert image → base64 (This part is fast, keep it sync)
    img = Image.open(image_path).convert("RGB")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    # Instruction
    instruction = (
        """You are an AI that converts a flowchart diagram image into structured JSON.
    Requirements:
     1. Extract all elements in the flowchart as **nodes**:
                    - Each node must have:
                        - "id": a unique integer
                        - "type": the shape of the node ("process", "decision", "start_end", "input_output", etc.)
                        - "label": the text inside the node

    2. Extract all **connections** as edges:
                    - Each edge must have:
                    - "source": id of the source node
                    - "target": id of the target node
    
    3. Output **JSON only**, with this structure:
                    {
                    "nodes": [
                        {"id": 1, "type": "start_end", "label": "Start"},
                        {"id": 2, "type": "process", "label": "Input Number"},
                        {"id": 3, "type": "decision", "label": "Number is even?"}
                    ],
                    "edges": [
                        {"source": 1, "target": 2},
                        {"source": 2, "target": 3}
                    ]
                    }

    
    4. Do not include any explanation or text outside the JSON.""")

    # Call HuggingFace API asynchronously
    try:
        completion = await client.chat.completions.create(     # <-- Added 'await'
            model="Qwen/Qwen3-VL-8B-Instruct:together",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_b64}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )

        response = completion.choices[0].message.content
        
        # --- Extract clean JSON ---
        clean = response.replace("```json", "").replace("```", "").strip()
        json_str = clean[clean.find("{"): clean.rfind("}") + 1]
        data = json.loads(json_str)
        return data

    except Exception as e:
        print("⚠️ Error during API call or JSON parsing:", e)

        return {"nodes": [], "edges": []}

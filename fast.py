from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import base64
import io
from main import remove_background, analyze_image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze/")
async def analyze_clothing(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            return JSONResponse(status_code=400, content={"error": "Uploaded file must be an image."})
        image_bytes = await file.read()

        pil_img, no_bg_bytes = remove_background(image_bytes)
        if not no_bg_bytes:
            return JSONResponse(status_code=400, content={"error": "Failed to remove background."})

        result = analyze_image(no_bg_bytes)
        if result is None:
            return JSONResponse(status_code=500, content={"error": "Failed to analyze image."})

        img_buffer = io.BytesIO()
        pil_img.save(img_buffer, format="PNG")
        base64_img = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

        return {
            "status": "success",
            "result": result,
            "preview_base64": f"data:image/png;base64,{base64_img}"
        }

    except Exception as e:
        print(f"❌ Server error: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal server error."})
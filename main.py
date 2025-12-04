import base64
import io
import json
import re
from PIL import Image
from rembg import remove
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def remove_background(image_bytes):
    try:
        output_data = remove(image_bytes)
        pil_image = Image.open(io.BytesIO(output_data)).convert("RGBA")
        return pil_image, output_data
    except Exception as e:
        print(f"❌ Background removal failed: {e}")
        return None, None

def encode_image_to_base64(image_bytes):
    try:
        return base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        print(f"❌ Encoding error: {e}")
        return None

def extract_json(response_text):
    cleaned = response_text.strip().replace("```json", "").replace("```", "").strip()
    match = re.search(r'(\[.*\]|\{.*\})', cleaned, re.DOTALL)
    return match.group(0) if match else cleaned

def analyze_image(image_bytes):
    encoded = encode_image_to_base64(image_bytes)
    if not encoded:
        return None

    prompt = """Look at the image and return clothing item(s) details.
If there are multiple items, return a list of objects.
If there is only one item, still return it inside a list.
Always use **this exact JSON format**:

[
  {
    "color": "",
    "category": "",
    "pattern": ""
  }
]"""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encoded}"
                    }
                }
            ]
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=700,
            temperature=0.3,
        )
        response_text = response.choices[0].message["content"].strip()
        json_output = extract_json(response_text)
        parsed = json.loads(json_output)
        return [parsed] if isinstance(parsed, dict) else parsed
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        return None

if __name__ == "__main__":
    input_image_path = r"C:\Users\Ramisa\Desktop\chloe\background.jpg"
    output_path = r"C:\Users\Ramisa\Desktop\chloe\removed_background.png"

    try:
        with open(input_image_path, "rb") as f:
            image_bytes = f.read()

        pil_img, bg_removed_bytes = remove_background(image_bytes)

        if pil_img and bg_removed_bytes:
            analysis_result = analyze_image(bg_removed_bytes)

            if analysis_result:
                print("🧠 Clothing Analysis Result:")
                print(json.dumps(analysis_result, indent=2))

                pil_img.save(output_path)
                print(f"🖼️ Saved background-removed image to: {output_path}")
            else:
                print("⚠️ Analysis failed.")
        else:
            print("⚠️ Background removal failed.")

    except Exception as e:
        print(f"❌ Error: {e}")
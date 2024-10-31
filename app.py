from spello.model import SpellCorrectionModel
from flask import Flask,request,jsonify,abort
from groq import Groq
import json
import pytesseract
from PIL import Image
from flask_cors import CORS
import io
import os
import base64
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv


app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

load_dotenv()

GROQ_TOKEN = os.getenv("GROQ_TOKEN")

client = Groq(api_key=GROQ_TOKEN)

# Constants
DATA_TO_TRAIN = ["bone", "woman","man","immune","nervous", "respiratory","vitamin A","Bronson Vitamin A 10,000 IU Premium Non-GMO Formula Supports Healthy Vision 180 Softgels","vitamin test","Bronson Vitamin A 10,000 IU Premium Non-GMO Formula Supports Healthy Vision 45 Softgels","Polygon Hair, Skin, and Nails","Polygon Omega 3","Polygon Prenatal","Polygon Saw Palmtto","Polygon Vitamin D3, 4000 IU","Vitamin A is a fat-soluble vitamin that is naturally present in many foods. Vitamin A is important for normal vision, the immune system, reproduction, and growth and development. Vitamin A also helps your heart, lungs, and other organs work properly.","For adults, take 1 capsule daily at mealtime with enough liquid or as directed by healthcare professional. Do not exceed the recommended daily allowance.", "used i pregnancy"]
ALLOWED_EXT = ["png", "jpeg", "jpg"]
ALLOWED_WORDS = ["supplements, facts", "nutrition", 'serving', 'warnings',"ingredient"]


# Helpers
def get_text_from_image(imageFile):
    # pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Update the path as needed
    return pytesseract.image_to_string(imageFile)

def pil_image_to_base64(image):
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")  # Save the image in JPEG format
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str   

def is_allowed_extension(file_name):
    return "." in file_name and file_name.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def is_allowed_image_for_extraction(text):
    return any(word.lower() in text.lower() for word in ALLOWED_WORDS)




@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "msg": e.description,
    })
    response.content_type = "application/json"
    return response

sp = SpellCorrectionModel(language="en")
sp.train(DATA_TO_TRAIN)

@app.route("/correct-query", methods=['POST'])
def get_correct_query_spell():
    corrected = sp.spell_correct(request.json["query"])
    return corrected


@app.route("/parse", methods=["POST"])
def parse_nf():
        
    image =  request.files["image"]
    
    if image.filename == "" or image is None:
        abort(404, description="No file provided")
        
    
    if not is_allowed_extension(image.filename):
        abort(400, description="The file extension is not allowed")
    
    img = Image.open(image)
    
    text = get_text_from_image(img)
    if not any(word.lower() in text.lower() for word in ALLOWED_WORDS):
        abort(400, description="Please provide a proper image for extraction")
    
    img_base64  = pil_image_to_base64(img)
    
    completion = client.chat.completions.create(
        model="llama-3.2-90b-vision-preview",
        messages=[
            
            {
                "role": "user",
                "content": [{
                        "type": "text",
                        "text": 
                        "extract the name, amount_per_serving and daily_value for every ingredient in table from image related to nutrition facts of certain product"
                        "extract the name, amount_per_serving and daily_value for every ingredient in table from image related to nutrition facts of certain product"
                        "extract serving size"
                        "extract serving per container"
                        "extract ingredients under other ingredients section"
                        "extract direction of use"
                        "extract warnings"
                        "extract storage condition"
                        "extract NFSA regesteration number"
                        "structure and structure them in JSON schema like this: {ingredients: [name: str\n   amount_per_serving: str\n    daily_value: str or **], other_ingredients: str\n  warnings: str or null\n  storage_conditions: str or null\n  direction_of_use: str or null\n  nfsa_reg_no: str, serving_size: str\n  serving_per_container: str}"
                        "note: The Nutrition/Supplement facts info is found in table boundry"
                        "note: if not found any section replace it with null (as a value not string)"
                                            
                                            },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f'data:image/jpeg;base64,{img_base64}'
                        }
                    },
                    
                    ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stream=False,
    )

    output_dict = json.loads(completion.choices[0].message.content)
    
    return jsonify({"data":output_dict })


if __name__ == "__main__":
    app.run(debug=True)
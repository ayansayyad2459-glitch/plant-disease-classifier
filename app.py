"""
AgroScan AI — Flask Prediction Server
Loads a trained MobileNetV2 model and exposes a /predict endpoint
that accepts plant leaf images and returns disease classification results.
"""

import os
import io
import json

import numpy as np
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
from urllib.parse import quote

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

# ---------------------------------------------------------------------------
# Disease Information Database
# Each entry contains bilingual (EN/HI) disease names, explanations,
# and recommended pesticides with Google Shopping purchase links.
# ---------------------------------------------------------------------------

disease_info = {
    "Apple___Apple_scab": {
        "disease_name_en": "Apple Scab",
        "disease_name_hi": "सेब का स्कैब",
        "explanation_en": (
            "Apple Scab is a common fungal disease that affects apple trees, "
            "causing dark, scabby spots on leaves and fruit. It thrives in cool, "
            "wet spring weather and can lead to significant crop loss if not managed."
        ),
        "explanation_hi": (
            "एप्पल स्कैब एक आम फंगल रोग है जो सेब के पेड़ों को प्रभावित करता है, "
            "जिससे पत्तियों और फलों पर गहरे, खुरदरे धब्बे हो जाते हैं। यह ठंडे, गीले "
            "वसंत के मौसम में पनपता है और अगर इसका प्रबंधन न किया जाए तो फसल का भारी नुकसान हो सकता है।"
        ),
        "pesticides_en": [
            {"name": "Mancozeb", "link": f"https://www.google.com/search?q=buy+{quote('Mancozeb')}&tbm=shop"},
            {"name": "Captan", "link": f"https://www.google.com/search?q=buy+{quote('Captan')}&tbm=shop"},
            {"name": "Myclobutanil", "link": f"https://www.google.com/search?q=buy+{quote('Myclobutanil')}&tbm=shop"},
        ],
        "pesticides_hi": [
            {"name": "मैनकोज़ेब", "link": f"https://www.google.com/search?q=buy+{quote('Mancozeb')}&tbm=shop"},
            {"name": "कैप्टन", "link": f"https://www.google.com/search?q=buy+{quote('Captan')}&tbm=shop"},
            {"name": "माइक्लोबुटानिल", "link": f"https://www.google.com/search?q=buy+{quote('Myclobutanil')}&tbm=shop"},
        ],
    },
    "Apple___Black_rot": {
        "disease_name_en": "Apple Black Rot",
        "disease_name_hi": "सेब का ब्लैक रॉट",
        "explanation_en": (
            "Black Rot is a fungal disease that creates a firm, brown to black rot "
            "on apples, often starting at the blossom end. It also causes 'frogeye' "
            "leaf spots and cankers on branches."
        ),
        "explanation_hi": (
            "ब्लैक रॉट एक फंगल रोग है जो सेब पर एक कठोर, भूरे से काले रंग की सड़न "
            "पैदा करता है, जो अक्सर फूल के सिरे से शुरू होती है। यह पत्तियों पर 'फ्रॉगआई' "
            "धब्बे और शाखाओं पर कैंकर भी पैदा करता है।"
        ),
        "pesticides_en": [
            {"name": "Thiophanate-methyl", "link": f"https://www.google.com/search?q=buy+{quote('Thiophanate-methyl')}&tbm=shop"},
            {"name": "Captan", "link": f"https://www.google.com/search?q=buy+{quote('Captan')}&tbm=shop"},
            {"name": "Ferbam", "link": f"https://www.google.com/search?q=buy+{quote('Ferbam')}&tbm=shop"},
        ],
        "pesticides_hi": [
            {"name": "थियोफैनेट-मिथाइल", "link": f"https://www.google.com/search?q=buy+{quote('Thiophanate-methyl')}&tbm=shop"},
            {"name": "कैप्टन", "link": f"https://www.google.com/search?q=buy+{quote('Captan')}&tbm=shop"},
            {"name": "फरबाम", "link": f"https://www.google.com/search?q=buy+{quote('Ferbam')}&tbm=shop"},
        ],
    },
    "Tomato___Bacterial_spot": {
        "disease_name_en": "Tomato Bacterial Spot",
        "disease_name_hi": "टमाटर का बैक्टीरियल स्पॉट",
        "explanation_en": (
            "Bacterial spot is a widespread disease in tomatoes, causing small, "
            "water-soaked spots on leaves and fruit that later turn greasy and dark. "
            "It is spread by splashing water and handling wet plants."
        ),
        "explanation_hi": (
            "बैक्टीरियल स्पॉट टमाटर में एक व्यापक बीमारी है, जिससे पत्तियों और फलों "
            "पर छोटे, पानी से लथपथ धब्बे हो जाते हैं जो बाद में चिकने और गहरे हो जाते "
            "हैं। यह पानी के छींटों और गीले पौधों को संभालने से फैलता है।"
        ),
        "pesticides_en": [
            {"name": "Copper-based bactericides", "link": f"https://www.google.com/search?q=buy+{quote('Copper-based bactericides')}&tbm=shop"},
            {"name": "Mancozeb", "link": f"https://www.google.com/search?q=buy+{quote('Mancozeb')}&tbm=shop"},
            {"name": "Streptomycin", "link": f"https://www.google.com/search?q=buy+{quote('Streptomycin')}&tbm=shop"},
        ],
        "pesticides_hi": [
            {"name": "ताम्र-आधारित जीवाणुनाशक", "link": f"https://www.google.com/search?q=buy+{quote('Copper bactericides')}&tbm=shop"},
            {"name": "मैनकोज़ेब", "link": f"https://www.google.com/search?q=buy+{quote('Mancozeb')}&tbm=shop"},
            {"name": "स्ट्रेप्टोमाइसिन", "link": f"https://www.google.com/search?q=buy+{quote('Streptomycin')}&tbm=shop"},
        ],
    },
    "default": {
        "disease_name_en": "Analysis Inconclusive or Healthy",
        "disease_name_hi": "विश्लेषण अनिर्णायक या स्वस्थ",
        "explanation_en": (
            "The plant appears to be healthy or the disease could not be identified "
            "from the image. For healthy plants, continue with good watering, "
            "fertilization, and pest monitoring practices."
        ),
        "explanation_hi": (
            "पौधा स्वस्थ प्रतीत होता है या चित्र से रोग की पहचान नहीं हो सकी। "
            "स्वस्थ पौधों के लिए, अच्छी सिंचाई, उर्वरक और कीट निगरानी प्रथाओं को जारी रखें।"
        ),
        "pesticides_en": [{"name": "No pesticides recommended. Monitor plant regularly.", "link": "#"}],
        "pesticides_hi": [{"name": "किसी कीटनाशक की सिफारिश नहीं की गई है। पौधे की नियमित निगरानी करें।", "link": "#"}],
    },
}

for key in [k for k in disease_info if "healthy" in k]:
    disease_info[key] = disease_info["default"]

# ---------------------------------------------------------------------------
# Model Loading
# ---------------------------------------------------------------------------

MODEL_PATH = "plant_disease_classifier.h5"

try:
    model = load_model(MODEL_PATH)
    with open("class_indices.json", "r") as f:
        class_indices = json.load(f)
    class_labels = {v: k for k, v in class_indices.items()}
    print("[INFO] Model and class indices loaded successfully.")
except Exception as e:
    print(f"[ERROR] Could not load model or class indices: {e}")
    model = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def prepare_image(image, target_size):
    """Resize and normalize an image for model input."""
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0) / 255.0
    return image


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/predict", methods=["POST"])
def predict():
    """Accept an image upload and return disease prediction with details."""
    if model is None:
        return jsonify({"error": "Model is not loaded."}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        image = Image.open(io.BytesIO(file.read()))
        processed_image = prepare_image(image, target_size=(224, 224))

        predictions = model.predict(processed_image)
        predicted_index = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_index])

        predicted_class = class_labels.get(predicted_index, "Unknown")
        details = disease_info.get(predicted_class, disease_info["default"])

        return jsonify({"confidence": confidence, "details": details})

    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        return jsonify({"error": "Error during prediction."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

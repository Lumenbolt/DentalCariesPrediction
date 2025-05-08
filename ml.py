import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input
import cv2

def calculate_genderwise_caries_risk(fingerprint_probs, gender):
    """Calculate caries risk based on fingerprint pattern probabilities and gender."""
    gender = gender.lower()
    if gender not in ["male", "female"]:
        raise ValueError("Gender must be 'male' or 'female'.")

    # Risk by gender
    risk_by_gender = {
        "male":   [66.7, 37.5, 59.5, 50.0, 49.0],
        "female": [87.5, 34.8, 59.5, 69.6, 51.6],
    }

    if len(fingerprint_probs) != 5:
        raise ValueError("Input must be an array of 5 probabilities.")

    if not all(0 <= p <= 1 for p in fingerprint_probs):
        raise ValueError("Probabilities must be between 0 and 1.")

    if abs(sum(fingerprint_probs) - 1.0) > 0.01:
        print("Warning: Probabilities do not sum exactly to 1.0")

    # Weighted average risk for the gender
    risks = risk_by_gender[gender]
    weighted_risk = sum(p * r for p, r in zip(fingerprint_probs, risks))

    return round(weighted_risk, 2)

class MLPredictor:
    def __init__(self):
        self.fingerprint_model = load_model('resNet_model_for_fingerprintClassification.keras')
        self.patterns = ["Arch", "Left Loop", "Right Loop", "Whorl", "Tented Arch"]

    def analyze_fingerprint(self, image_path, gender):
        """Run the fingerprint model and calculate caries risk based on gender."""
        try:
            # Load and preprocess the image
            img_size = 256
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (img_size, img_size))
            image = image.astype(np.float32)
            image = preprocess_input(image)

            # Convert the image back to uint8 for saving
            image_to_save = (image - image.min()) / (image.max() - image.min()) * 255  # Normalize to 0-255
            image_to_save = image_to_save.astype(np.uint8)
            cv2.imwrite("temp_preprocessed_image.png", cv2.cvtColor(image_to_save, cv2.COLOR_RGB2BGR))

            image = np.expand_dims(image, axis=0)

            # Predict fingerprint pattern probabilities
            pattern_probs = self.fingerprint_model.predict(image)[0]

            # Calculate caries risk based on gender
            risk = calculate_genderwise_caries_risk(pattern_probs.tolist(), gender)

            # Get the most probable pattern
            pattern = self.patterns[np.argmax(pattern_probs)]

            return f"""📋 Analysis Results:
            Pattern Type: {pattern}
            Caries Risk: {risk}%"""
        except Exception as e:
            raise RuntimeError(f"Analysis failed: {str(e)}")
import cv2
import serial.tools.list_ports
import tempfile
import os
from pyfingerprint.pyfingerprint import PyFingerprint
import numpy as np

def detect_sensor_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "CP2102" in port.description or "Silicon Labs" in port.manufacturer:
            return port.device
    return None

def capture_fingerprint(status_callback=None):
    """Capture fingerprint and save it to a temporary file."""
    sensor = None
    try:
        port = detect_sensor_port()
        if not port:
            raise RuntimeError("Sensor not connected")

        sensor = PyFingerprint(port, 115200, 0xFFFFFFFF, 0x00000000)
        if not sensor.verifyPassword():
            raise ValueError("Sensor authentication failed")

        # Wait for finger
        while not sensor.readImage():
            pass

        if status_callback:
            status_callback("🔬 Scanning fingerprint...")

        # Save the raw fingerprint image to a temporary location
        temp_dir = tempfile.gettempdir()
        raw_path = os.path.join(temp_dir, "fingerprint_raw.bmp")
        sensor.downloadImage(raw_path)

        # Enhance the fingerprint image
        enhanced_path = os.path.join(temp_dir, "fingerprint_enhanced.png")
        #enhanced_img = enhance_fingerprint(raw_path, enhanced_path)

        return enhanced_path  # Return the path to the enhanced image
    except Exception as e:
        raise RuntimeError(f"Capture failed: {str(e)}")
    finally:
        if sensor:
            del sensor

def enhance_fingerprint(raw_path, enhanced_path):
    """Enhance the fingerprint image and save it."""
    img = cv2.imread(raw_path, cv2.IMREAD_GRAYSCALE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
    enhanced = cv2.adaptiveThreshold(enhanced, 255, 
                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
    cv2.imwrite(enhanced_path, enhanced)  # Save the enhanced image
    return enhanced_path
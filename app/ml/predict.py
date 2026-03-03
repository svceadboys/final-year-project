import os
import json
from pathlib import Path
from typing import Tuple, List, Optional

import numpy as np
from PIL import Image
import tensorflow as tf


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(
    os.getenv("WASTE_MODEL_PATH", BASE_DIR / "app" / "ml" / "saved_model.h5")
)
CLASSES_PATH = Path(
    os.getenv("WASTE_CLASSES_PATH", BASE_DIR / "app" / "ml" / "classes.json")
)

IMG_SIZE = (224, 224)


def _load_class_names() -> List[str]:
    if CLASSES_PATH.exists():
        with CLASSES_PATH.open() as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
    # Fallback in case classes.json is missing; indices will map to strings
    return []


CLASS_NAMES: List[str] = _load_class_names()


def load_model() -> tf.keras.Model:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_PATH}. "
            "Run app/ml/train_model.py to create saved_model.h5."
        )
    model = tf.keras.models.load_model(MODEL_PATH)
    return model


def preprocess_image(image_path: Path) -> np.ndarray:
    img = Image.open(image_path).convert("RGB")
    img = img.resize(IMG_SIZE)
    arr = np.array(img).astype("float32") / 255.0
    arr = np.expand_dims(arr, axis=0)
    return arr


def predict_image(
    image_path: Path, model: Optional[tf.keras.Model] = None
) -> Tuple[str, float]:
    if model is None:
        model = load_model()
    input_arr = preprocess_image(image_path)
    preds = model.predict(input_arr)
    class_idx = int(np.argmax(preds, axis=1)[0])
    confidence = float(np.max(preds))

    if 0 <= class_idx < len(CLASS_NAMES):
        label = CLASS_NAMES[class_idx]
    else:
        label = str(class_idx)

    return label, confidence


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run waste classification on a single image."
    )
    parser.add_argument("image_path", type=str, help="Path to input image")
    args = parser.parse_args()

    model = load_model()
    label, confidence = predict_image(Path(args.image_path), model)
    print(f"Predicted: {label} (confidence={confidence:.4f})")


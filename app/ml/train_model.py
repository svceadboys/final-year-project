import os
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import classification_report, confusion_matrix


BASE_DIR = Path(__file__).resolve().parents[2]

# Use the attached TrashType image dataset located in the project root:
# Final year proj/TrashType_Image_Dataset/{cardboard, glass, metal, paper, plastic, trash}
DATA_DIR = Path(
    os.getenv("WASTE_DATA_DIR", BASE_DIR / "TrashType_Image_Dataset")
)

MODEL_OUTPUT_PATH = Path(
    os.getenv("WASTE_MODEL_PATH", BASE_DIR / "app" / "ml" / "saved_model.h5")
)
METRICS_OUTPUT_PATH = Path(
    os.getenv("WASTE_METRICS_PATH", BASE_DIR / "app" / "ml" / "metrics.txt")
)
CLASSES_OUTPUT_PATH = Path(
    os.getenv("WASTE_CLASSES_PATH", BASE_DIR / "app" / "ml" / "classes.json")
)

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = int(os.getenv("WASTE_TRAIN_EPOCHS", "10"))
LEARNING_RATE = float(os.getenv("WASTE_LEARNING_RATE", "1e-4"))


def build_model(num_classes: int) -> Model:
    base_model = MobileNetV2(
        weights="imagenet", include_top=False, input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3)
    )
    base_model.trainable = False

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation="relu")(x)
    outputs = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=outputs)
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def create_generators():
    # Use a single dataset folder and let Keras create a validation split.
    # Folder layout:
    # TrashType_Image_Dataset/
    #   cardboard/
    #   glass/
    #   metal/
    #   paper/
    #   plastic/
    #   trash/
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
        fill_mode="nearest",
        validation_split=0.2,
    )

    val_datagen = ImageDataGenerator(rescale=1.0 / 255, validation_split=0.2)

    train_gen = train_datagen.flow_from_directory(
        DATA_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=True,
        subset="training",
    )

    val_gen = val_datagen.flow_from_directory(
        DATA_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
        subset="validation",
    )

    return train_gen, val_gen


def main():
    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Expected dataset folder at {DATA_DIR}. "
            "Update WASTE_DATA_DIR or change DATA_DIR in train_model.py."
        )

    train_gen, val_gen = create_generators()
    num_classes = len(train_gen.class_indices)

    # Persist class index mapping for use at inference time
    class_indices = train_gen.class_indices
    idx_to_class = [None] * len(class_indices)
    for class_name, idx in class_indices.items():
        idx_to_class[idx] = class_name

    CLASSES_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CLASSES_OUTPUT_PATH.open("w") as f:
        json.dump(idx_to_class, f)

    model = build_model(num_classes)

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        verbose=1,
    )

    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_OUTPUT_PATH)

    val_gen.reset()
    y_prob = model.predict(val_gen, verbose=1)
    y_pred = np.argmax(y_prob, axis=1)
    y_true = val_gen.classes
    target_names = idx_to_class

    report = classification_report(
        y_true, y_pred, target_names=target_names, digits=4
    )
    cm = confusion_matrix(y_true, y_pred)

    METRICS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_OUTPUT_PATH.open("w") as f:
        f.write("Classification Report:\n")
        f.write(report)
        f.write("\n\nConfusion Matrix:\n")
        f.write(str(cm))
        f.write("\n\nTraining History Keys:\n")
        f.write(str(history.history.keys()))

    print("Model saved to:", MODEL_OUTPUT_PATH)
    print("Class labels saved to:", CLASSES_OUTPUT_PATH)
    print("Metrics saved to:", METRICS_OUTPUT_PATH)


if __name__ == "__main__":
    # Make TF behave nicely with limited CPUs
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    main()


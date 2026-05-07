"""
AgroScan AI — Model Training Script
Uses transfer learning with MobileNetV2 (pre-trained on ImageNet) to classify
38 plant disease classes from the New Plant Diseases Dataset.
"""

import json
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import AveragePooling2D, Dropout, Flatten, Dense, Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

TRAIN_DIR = "New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/train"
VALID_DIR = "New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/valid"
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
LEARNING_RATE = 1e-4
EPOCHS = 10

# ---------------------------------------------------------------------------
# Data Generators
# ---------------------------------------------------------------------------

train_datagen = ImageDataGenerator(
    rotation_range=30,
    zoom_range=0.15,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.15,
    horizontal_flip=True,
    fill_mode="nearest",
    rescale=1.0 / 255,
)

valid_datagen = ImageDataGenerator(rescale=1.0 / 255)

train_generator = train_datagen.flow_from_directory(
    TRAIN_DIR,
    target_size=IMAGE_SIZE,
    class_mode="categorical",
    batch_size=BATCH_SIZE,
)

valid_generator = valid_datagen.flow_from_directory(
    VALID_DIR,
    target_size=IMAGE_SIZE,
    class_mode="categorical",
    batch_size=BATCH_SIZE,
    shuffle=False,
)

# ---------------------------------------------------------------------------
# Model Architecture (Transfer Learning)
# ---------------------------------------------------------------------------

base_model = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_tensor=Input(shape=(IMAGE_SIZE[0], IMAGE_SIZE[1], 3)),
)

head = base_model.output
head = AveragePooling2D(pool_size=(7, 7))(head)
head = Flatten(name="flatten")(head)
head = Dense(128, activation="relu")(head)
head = Dropout(0.5)(head)
head = Dense(len(train_generator.class_indices), activation="softmax")(head)

model = Model(inputs=base_model.input, outputs=head)

for layer in base_model.layers:
    layer.trainable = False

# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

print("[INFO] Compiling model...")
model.compile(
    loss="categorical_crossentropy",
    optimizer=Adam(learning_rate=LEARNING_RATE),
    metrics=["accuracy"],
)

print("[INFO] Training head...")
history = model.fit(
    train_generator,
    steps_per_epoch=train_generator.samples // BATCH_SIZE,
    validation_data=valid_generator,
    validation_steps=valid_generator.samples // BATCH_SIZE,
    epochs=EPOCHS,
)

# ---------------------------------------------------------------------------
# Save Artifacts
# ---------------------------------------------------------------------------

print("[INFO] Saving model...")
model.save("plant_disease_classifier.h5")

with open("class_indices.json", "w") as f:
    json.dump(train_generator.class_indices, f)

print("[INFO] Training complete!")

#!/usr/bin/env python

import sys
sys.path.append('./')
sys.path.append('../')

from lab_utils import (
    os, np, plt, logger, ap, BooleanAction,
    debug, toc
)

ap.add_argument('--epochs', type=int, default=10, help='number of epochs: 10*')
ap.add_argument('--batch', type=int, default=64, help='batch size: 64*')
args, extra_args = ap.parse_known_args()
logger.info(args)
# logger.info(extra_args)

if args.debug:
    import pdb
    import rlcompleter
    pdb.Pdb.complete=rlcompleter.Completer(locals()).complete
    # import code
    # code.interact(local=locals())
    debug = breakpoint

import time
from PIL import Image
import pathlib

import tensorflow as tf
physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

print("\n#################################################")
print("Version: ", tf.__version__)
print("Eager mode: ", tf.executing_eagerly())
print("GPU is", "available" if tf.config.list_physical_devices("GPU") else "NOT AVAILABLE")

from tensorflow.keras import Sequential, Model, Input
from tensorflow.keras.layers import Flatten, Dense, Dropout, Softmax
from tensorflow.keras.layers import Conv2D, MaxPooling2D


### Step #0 - TOC
if args.step == 0:
    toc(__file__)


### Step #1 - Download and explore the dataset
if args.step >= 1:
    print("\n### Step #1 - Download and explore the dataset")

    dataset_url = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"
    data_dir = tf.keras.utils.get_file(
        'flower_photos', 
        origin=dataset_url, 
        untar=True
    )

    data_dir = pathlib.Path(data_dir)
    logger.info(f'data_dir: {data_dir}')

    image_count = len(list(data_dir.glob('*/*.jpg')))
    logger.info(f'image_count: {image_count}')

    if args.step == 1 and args.plot:
        roses = list(data_dir.glob('roses/*'))
        # image = Image.open(str(roses[0]))
        image = tf.io.read_file(str(roses[0]))
        image = tf.image.decode_jpeg(image)
        plt.figure()
        plt.imshow(image)
        plt.show(block=False)


### Step #2 - Create a dataset
if args.step >= 2:
    print("\n### Step #2 - Create a dataset")

    batch_size = 32
    img_height = 180
    img_width = 180

    train_ds = tf.keras.preprocessing.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(img_height, img_width),
        batch_size=batch_size
    )

    val_ds = tf.keras.preprocessing.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(img_height, img_width),
        batch_size=batch_size
    )

    class_names = train_ds.class_names
    logger.info(f'class_names: {class_names}')


### Step #3 -  Visualize the data
if args.step == 3:
    print("\n### Step #3 - Visualize the data")

    if args.plot:
        plt.figure(figsize=(10, 10))
        for images, labels in train_ds.take(1):
            for i in range(9):
                ax = plt.subplot(3, 3, i + 1)
                plt.imshow(images[i].numpy().astype("uint8"))
                plt.title(class_names[labels[i]])
                plt.axis("off")
        plt.show(block=False)

    for image_batch, labels_batch in train_ds:
        logger.info(f'image_batch.shape: {image_batch.shape}')
        logger.info(f'labels_batch.shape: {labels_batch.shape}')
        break


### Step #4 - Configure the dataset for performance
if args.step >= 4:
    print("\n### Step #4 - Configure the dataset for performance")

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)


### Step #5 - Standardize the data
if args.step == 5:
    print("\n### Step #5 - Standardize the data")

    normalization_layer = tf.keras.layers.experimental.preprocessing.Rescaling(1./255)
    normalized_ds = train_ds.map(lambda x, y: (normalization_layer(x), y))

    image_batch, labels_batch = next(iter(normalized_ds))
    first_image = image_batch[0]
    # Notice the pixels values are now in `[0,1]`.
    logger.info(f'pixel ranges: {np.min(first_image)}~{np.max(first_image)}')


### Step #6 - Create and compile the model
if args.step in [6, 7, 8, 9]:
    print("\n### Step #6 - Create and compile the model")

    num_classes = 5
    model = Sequential([
        tf.keras.layers.experimental.preprocessing.Rescaling(1./255, input_shape=(img_height, img_width, 3)),
        Conv2D(16, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Conv2D(32, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Conv2D(64, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Flatten(),
        Dense(128, activation='relu'),
        Dense(num_classes)
    ])

    model.compile(
        optimizer='adam',
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=['accuracy']
    )


### Step #7 - Model summary
if args.step == 7:
    print("\n### Step #7 - Model summary")

    model.summary()


### Step #8 - Train the model
if args.step in [8, 9]:
    print("\n### Step #8 - Train the model")

    logger.info('model.fit():')
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        verbose=2
    )


### Step #9 - Visualize training results
if args.step == 9:
    print("\n### Step #9 - Visualize training results")

    if args.plot:
        acc = history.history['accuracy']
        val_acc = history.history['val_accuracy']

        loss = history.history['loss']
        val_loss = history.history['val_loss']

        epochs_range = range(args.epochs)

        plt.figure(figsize=(8, 8))
        plt.subplot(1, 2, 1)
        plt.plot(epochs_range, acc, label='Training Accuracy')
        plt.plot(epochs_range, val_acc, label='Validation Accuracy')
        plt.legend(loc='lower right')
        plt.title('Training and Validation Accuracy')

        plt.subplot(1, 2, 2)
        plt.plot(epochs_range, loss, label='Training Loss')
        plt.plot(epochs_range, val_loss, label='Validation Loss')
        plt.legend(loc='upper right')
        plt.title('Training and Validation Loss')
        plt.show(block=False)


### Step #10 - Overfitting
if args.step >= 10:
    print("\n### Step #10 - Overfitting")


### Step #11 - Data augmentation
if args.step >= 11:
    print("\n### Step #11 - Data augmentation")

    data_augmentation = Sequential([
        tf.keras.layers.experimental.preprocessing.RandomFlip(
            "horizontal",
            input_shape=(img_height, img_width, 3)
        ),
        tf.keras.layers.experimental.preprocessing.RandomRotation(0.1),
        tf.keras.layers.experimental.preprocessing.RandomZoom(0.1),
    ])

    if args.step == 11 and args.plot:
        plt.figure(figsize=(10, 10))
        for images, _ in train_ds.take(1):
            for i in range(9):
                augmented_images = data_augmentation(images)
                ax = plt.subplot(3, 3, i + 1)
                plt.imshow(augmented_images[0].numpy().astype("uint8"))
                plt.axis("off")
        plt.show(block=False)


### Step #12 - Dropout
if args.step >= 12:
    print("\n### Step #12 - Dropout")

    num_classes = 5
    model = Sequential([
        data_augmentation,
        tf.keras.layers.experimental.preprocessing.Rescaling(1./255),
        Conv2D(16, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Conv2D(32, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Conv2D(64, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Dropout(0.2),
        Flatten(),
        Dense(128, activation='relu'),
        Dense(num_classes)
    ])  


### Step #13 - Compile and train the model
if args.step >= 13:
    print("\n### Step #13 - Compile and train the model")

    model.compile(
        optimizer='adam',
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=['accuracy']
    )

    if args.step == 13:
        model.summary()

    logger.info('model.fit():')
    history = model.fit(
        train_ds, 
        validation_data=val_ds, 
        epochs=args.epochs,
        verbose=2
    )


### Step #14 - Visualize training results
if args.step == 14:
    print("\n### Step #14 - Visualize training results")

    if args.plot:
        acc = history.history['accuracy']
        val_acc = history.history['val_accuracy']

        loss = history.history['loss']
        val_loss = history.history['val_loss']

        epochs_range = range(args.epochs)

        plt.figure(figsize=(8, 8))
        plt.subplot(1, 2, 1)
        plt.plot(epochs_range, acc, label='Training Accuracy')
        plt.plot(epochs_range, val_acc, label='Validation Accuracy')
        plt.legend(loc='lower right')
        plt.title('Training and Validation Accuracy')

        plt.subplot(1, 2, 2)
        plt.plot(epochs_range, loss, label='Training Loss')
        plt.plot(epochs_range, val_loss, label='Validation Loss')
        plt.legend(loc='upper right')
        plt.title('Training and Validation Loss')
        plt.show(block=False)


### Step #15 - Predict on new data
if args.step == 15:
    print("\n### Step #15 - Predict on new data")

    sunflower_url = "https://storage.googleapis.com/download.tensorflow.org/example_images/592px-Red_sunflower.jpg"
    sunflower_path = tf.keras.utils.get_file(
        'Red_sunflower', 
        origin=sunflower_url
    )

    # read, maxtrix, resize 
    img = tf.keras.preprocessing.image.load_img(
        sunflower_path, target_size=(img_height, img_width)
    )
    # img = tf.io.read_file(sunflower_path)
    # img = tf.image.decode_jpeg(img)
    # img = tf.image.resize(img, (image_height, img_width))
    # img = tf.cast(img, tf.uint8)

    img_array = tf.keras.preprocessing.image.img_to_array(img) # (180,180,3)
    img_array = tf.expand_dims(img_array, 0) # Create a batch => #(1,180,180,3)

    predictions = model.predict(img_array)
    score = tf.nn.softmax(predictions[0])

    logger.info(
        "This image most likely belongs to {} with a {:.2f} percent confidence."
        .format(class_names[np.argmax(score)], 100 * np.max(score))
    )


### End of File
if args.plot:
    plt.show()
debug()



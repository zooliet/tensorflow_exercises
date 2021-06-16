#!/usr/bin/env python

import sys
sys.path.append('./')
sys.path.append('../../')

from lab_utils import (
    tf, os, np, plt, logger, ap, BooleanAction,
    debug, toc, auto_increment
)

ap.add_argument('--epochs', type=int, default=2, help='number of epochs: 2*')
# ap.add_argument('--batch', type=int, default=32, help='batch size: 32*')
args, extra_args = ap.parse_known_args()
logger.info(args)
# logger.info(extra_args)

if args.all:
    args.step = 0 # forced to 0

if args.debug:
    import pdb
    import rlcompleter
    pdb.Pdb.complete=rlcompleter.Completer(locals()).complete
    # import code
    # code.interact(local=locals())
    debug = breakpoint

import time
from PIL import Image

from tensorflow.keras import Model, Input
from tensorflow.keras.layers import Layer, Dense


### TOC
if args.step == 0:
    toc(__file__)


if True:
    # Prepare the training dataset.
    batch_size = 64
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    x_train = np.reshape(x_train, (-1, 784))
    x_test = np.reshape(x_test, (-1, 784))

    # Reserve 10,000 samples for validation.
    x_val = x_train[-10000:]
    y_val = y_train[-10000:]
    x_train = x_train[:-10000]
    y_train = y_train[:-10000]

    # Prepare the training dataset.
    train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train))
    train_dataset = train_dataset.shuffle(buffer_size=1024).batch(batch_size)
    train_dataset = train_dataset.cache().prefetch(tf.data.AUTOTUNE)

    # Prepare the validation dataset.
    val_dataset = tf.data.Dataset.from_tensor_slices((x_val, y_val))
    val_dataset = val_dataset.batch(batch_size)    
    val_dataset = val_dataset.cache().prefetch(tf.data.AUTOTUNE)

    # model
    def get_model():
        inputs = Input(shape=(784,), name="digits")
        x1 = Dense(64, activation="relu")(inputs)
        x2 = Dense(64, activation="relu")(x1)
        outputs = Dense(10, name="predictions")(x2)
        model = Model(inputs=inputs, outputs=outputs)
        return model


args.step = auto_increment(args.step, args.all)
### Step #1 - Using the GradientTape: a first end-to-end example 
if args.step == 1:
    print("\n### Step #1 - Using the GradientTape: a first end-to-end example")

    model = get_model()

    # Instantiate an optimizer.
    optimizer = tf.keras.optimizers.SGD(learning_rate=1e-3)
    # Instantiate a loss function.
    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    epochs = args.epochs
    for epoch in range(epochs):
        logger.info("Start of epoch %d" % (epoch,))

        # Iterate over the batches of the dataset.
        for step, (x_batch_train, y_batch_train) in enumerate(train_dataset):
            # Open a GradientTape to record the operations run
            # during the forward pass, which enables auto-differentiation.
            with tf.GradientTape() as tape:
                # Run the forward pass of the layer.
                # The operations that the layer applies
                # to its inputs are going to be recorded
                # on the GradientTape.
                logits = model(x_batch_train, training=True)  # Logits for this minibatch
                # Compute the loss value for this minibatch.
                loss_value = loss_fn(y_batch_train, logits)

            # Use the gradient tape to automatically retrieve
            # the gradients of the trainable variables with respect to the loss.
            grads = tape.gradient(loss_value, model.trainable_weights)

            # Run one step of gradient descent by updating
            # the value of the variables to minimize the loss.
            optimizer.apply_gradients(zip(grads, model.trainable_weights))

            # Log every 200 batches.
            if step % 200 == 0:
                logger.info(
                    "Training loss (for one batch) at step %d: %.4f"
                    % (step, float(loss_value))
                )
                logger.info("Seen so far: %s samples" % ((step + 1) * batch_size))


args.step = auto_increment(args.step, args.all)
### Step #2 - Low-level handling of metrics
if args.step == 2:
    print("\n### Step #2 - Low-level handling of metrics")

    model = get_model()

    # Instantiate an optimizer to train the model.
    optimizer = tf.keras.optimizers.SGD(learning_rate=1e-3)
    # Instantiate a loss function.
    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    # Prepare the metrics.
    train_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()
    val_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()

    epochs = args.epochs
    for epoch in range(epochs):
        logger.info("Start of epoch %d" % (epoch,))
        start_time = time.time()

        # Iterate over the batches of the dataset.
        for step, (x_batch_train, y_batch_train) in enumerate(train_dataset):
            with tf.GradientTape() as tape:
                logits = model(x_batch_train, training=True)
                loss_value = loss_fn(y_batch_train, logits)
            grads = tape.gradient(loss_value, model.trainable_weights)
            optimizer.apply_gradients(zip(grads, model.trainable_weights))

            # Update training metric.
            train_acc_metric.update_state(y_batch_train, logits)

            # Log every 200 batches.
            if step % 200 == 0:
                logger.debug(
                    "Training loss (for one batch) at step %d: %.4f"
                    % (step, float(loss_value))
                )
                logger.debug("Seen so far: %d samples" % ((step + 1) * batch_size))

        # Display metrics at the end of each epoch.
        train_acc = train_acc_metric.result()
        logger.info("Training acc over epoch: %.4f" % (float(train_acc),))

        # Reset training metrics at the end of each epoch
        train_acc_metric.reset_states()

        # Run a validation loop at the end of each epoch.
        for x_batch_val, y_batch_val in val_dataset:
            val_logits = model(x_batch_val, training=False)
            # Update val metrics
            val_acc_metric.update_state(y_batch_val, val_logits)
        val_acc = val_acc_metric.result()
        val_acc_metric.reset_states()
        logger.info("Validation acc: %.4f" % (float(val_acc),))
        logger.info("Time taken/epoch: %.2fs" % (time.time() - start_time))


args.step = auto_increment(args.step, args.all)
### Step #3 - Speeding-up your training step with tf.function
if args.step == 3:
    print("\n### Step #3 - Speeding-up your training step with tf.function")

    model = get_model()

    # Instantiate an optimizer to train the model.
    optimizer = tf.keras.optimizers.SGD(learning_rate=1e-3)
    # Instantiate a loss function.
    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    # Prepare the metrics.
    train_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()
    val_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()

    @tf.function
    def train_step(x, y):
        with tf.GradientTape() as tape:
            logits = model(x, training=True)
            loss_value = loss_fn(y, logits)
        grads = tape.gradient(loss_value, model.trainable_weights)
        optimizer.apply_gradients(zip(grads, model.trainable_weights))
        train_acc_metric.update_state(y, logits)
        return loss_value

    @tf.function
    def test_step(x, y):
        val_logits = model(x, training=False)
        val_acc_metric.update_state(y, val_logits)

    epochs = args.epochs
    for epoch in range(epochs):
        logger.info("Start of epoch %d" % (epoch,))
        start_time = time.time()

        # Iterate over the batches of the dataset.
        for step, (x_batch_train, y_batch_train) in enumerate(train_dataset):
            loss_value = train_step(x_batch_train, y_batch_train)

            # Log every 200 batches.
            if step % 200 == 0:
                logger.debug(
                    "Training loss (for one batch) at step %d: %.4f"
                    % (step, float(loss_value))
                )
                logger.debug("Seen so far: %d samples" % ((step + 1) * batch_size))

        # Display metrics at the end of each epoch.
        train_acc = train_acc_metric.result()
        logger.info("Training acc over epoch: %.4f" % (float(train_acc),))

        # Reset training metrics at the end of each epoch
        train_acc_metric.reset_states()

        # Run a validation loop at the end of each epoch.
        for x_batch_val, y_batch_val in val_dataset:
            test_step(x_batch_val, y_batch_val)

        val_acc = val_acc_metric.result()
        val_acc_metric.reset_states()
        logger.info("Validation acc: %.4f" % (float(val_acc),))
        logger.info("Time taken/epoch: %.2fs" % (time.time() - start_time))


args.step = auto_increment(args.step, args.all)
### Step #4 - Low-level handling of losses tracked by the model
if args.step == 4:
    print("\n### Step #4 - Low-level handling of losses tracked by the model")

    class ActivityRegularizationLayer(Layer):
        def call(self, inputs):
            self.add_loss(1e-2 * tf.reduce_sum(inputs))
            return inputs

    inputs = Input(shape=(784,), name="digits")
    x = Dense(64, activation="relu")(inputs)
    # Insert activity regularization as a layer
    x = ActivityRegularizationLayer()(x)
    x = Dense(64, activation="relu")(x)
    outputs = Dense(10, name="predictions")(x)

    model = Model(inputs=inputs, outputs=outputs)

    # Instantiate an optimizer to train the model.
    optimizer = tf.keras.optimizers.SGD(learning_rate=1e-3)
    # Instantiate a loss function.
    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    # Prepare the metrics.
    train_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()
    val_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()

    @tf.function
    def train_step(x, y):
        with tf.GradientTape() as tape:
            logits = model(x, training=True)
            loss_value = loss_fn(y, logits)
            # Add any extra losses created during the forward pass.
            loss_value += sum(model.losses)
        grads = tape.gradient(loss_value, model.trainable_weights)
        optimizer.apply_gradients(zip(grads, model.trainable_weights))
        train_acc_metric.update_state(y, logits)
        return loss_value

    @tf.function
    def test_step(x, y):
        val_logits = model(x, training=False)
        val_acc_metric.update_state(y, val_logits)

    epochs = args.epochs
    for epoch in range(epochs):
        logger.info("Start of epoch %d" % (epoch,))
        start_time = time.time()

        # Iterate over the batches of the dataset.
        for step, (x_batch_train, y_batch_train) in enumerate(train_dataset):
            loss_value = train_step(x_batch_train, y_batch_train)

            # Log every 200 batches.
            if step % 200 == 0:
                logger.debug(
                    "Training loss (for one batch) at step %d: %.4f"
                    % (step, float(loss_value))
                )
                logger.debug("Seen so far: %d samples" % ((step + 1) * batch_size))

        # Display metrics at the end of each epoch.
        train_acc = train_acc_metric.result()
        logger.info("Training acc over epoch: %.4f" % (float(train_acc),))

        # Reset training metrics at the end of each epoch
        train_acc_metric.reset_states()

        # Run a validation loop at the end of each epoch.
        for x_batch_val, y_batch_val in val_dataset:
            test_step(x_batch_val, y_batch_val)

        val_acc = val_acc_metric.result()
        val_acc_metric.reset_states()
        logger.info("Validation acc: %.4f" % (float(val_acc),))
        logger.info("Time taken/epoch: %.2fs" % (time.time() - start_time))


args.step = auto_increment(args.step, args.all)
### Step #5 - End-to-end example: a GAN training loop from scratch
if args.step == 5:
    print("\n### Step #5 - End-to-end example: a GAN training loop from scratch")
    pass


### End of File
if args.plot:
    plt.show()
debug()


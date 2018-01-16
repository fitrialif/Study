__author__ = "kdhht5022@gmail.com"
# -*- coding: utf-8 -*-

import keras
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.engine import Input, Model
import multiprocessing
import multi_process as T
import os

try:
    from importlib import reload
    reload(T)
except:
    reload(T)

batch_size = 32
num_classes = 10
epochs = 100
data_augmentation = True
num_predictions = 20
save_dir = os.path.join(os.getcwd(), 'saved_models')
model_name = 'keras_cifar10_trained_model.h5'

def simple_cnn(inp):
    
    x = Conv2D(32, (3, 3), padding='same', activation='relu')(inp)
    x = Conv2D(32, (3, 3), padding='same', activation='relu')(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)
    x = Dropout(0.25)(x)
    
    x = Conv2D(64, (3, 3), padding='same', activation='relu')(x)
    x = Conv2D(64, (3, 3), padding='same', activation='relu')(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)
    x = Dropout(0.25)(x)
    
    x1 = Flatten()(x)
    x1 = Dense(512, activation='relu')(x1)
    out1 = Dense(num_classes, activation='softmax')(x1)
    
    x2 = Flatten()(x)
    x2 = Dense(512, activation='relu')(x2)
    x2 = Dropout(0.5)(x2)
    out2 = Dense(num_classes, activation='softmax')(x2)
    
    return out1, out2

def main():

    # The data, shuffled and split between train and test sets:
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    print('x_train shape:', x_train.shape)
    print(x_train.shape[0], 'train samples')
    print(x_test.shape[0], 'test samples')

    # Convert class vectors to binary class matrices.
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)

    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255

    inputs = Input(shape=(32, 32, 3))

    out1, out2 = simple_cnn(inputs)

    model = Model(inputs=inputs, outputs=[out1, out2])
    # model.summary()

    opt = keras.optimizers.rmsprop(lr=0.0001, decay=1e-6)
    model.compile(optimizer=opt,
                  loss=['categorical_crossentropy', 'categorical_crossentropy'],
                  metrics=['accuracy'])


    if not data_augmentation:
        print('Not using data augmentation.')
        model.fit(x_train, [y_train, y_train],
                  batch_size=batch_size,
                  epochs=epochs,
                  validation_data=(x_test, [y_test, y_test]),
                  shuffle=True)
    else:
        print('Using real-time data augmentation.')
        n_process = 4
        pool = multiprocessing.Pool(processes=n_process)
        def train_generator(x, y, batch_size):
            train_datagen = T.ImageDataGenerator(
                            pool=pool, 
                            width_shift_range=0.1,   # randomly shift images horizontally (fraction of total width)
                            height_shift_range=0.1,  # randomly shift images vertically (fraction of total height)
                            horizontal_flip=True)    # randomly flip images
            generator = train_datagen.flow(x, y, batch_size=batch_size)
            while 1:
                x_batch, y_batch = generator.next()
                yield (x_batch, [y_batch, y_batch])

        # Fit the model on the batches generated by datagen.flow().
        model.fit_generator(generator=train_generator(x_train, y_train, batch_size),
                            steps_per_epoch=int(y_train.shape[0] / batch_size),
                            epochs=epochs,
                            validation_data=(x_test, [y_test, y_test]),
                            callbacks=[])
        
        pool.terminate()

    # Save model and weights
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    model_path = os.path.join(save_dir, model_name)
    model.save(model_path)
    print('Saved trained model at %s ' % model_path)

    # Score trained model.
    scores = model.evaluate(x_test, [y_test, y_test], verbose=1)
    print('Test loss:', scores[0])
    print('Test accuracy:', scores[1])


if __name__ == "main":
    main()

from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, Bidirectional
from keras.layers import LSTM, Flatten, Conv1D, LocallyConnected1D, CuDNNLSTM, CuDNNGRU, MaxPooling1D, GlobalAveragePooling1D, GlobalMaxPooling1D
from math import sqrt
from keras.layers.embeddings import Embedding
from keras.callbacks import ModelCheckpoint
# from matplotlib import pyplot
import keras
from sklearn.preprocessing import OneHotEncoder
from keras.layers.normalization import BatchNormalization
import tensorflow as tf
import numpy as np
import argparse
import os
from keras.callbacks import CSVLogger

import models

tf.set_random_seed(42)
np.random.seed(0)

parser = argparse.ArgumentParser()
parser.add_argument('-d', action='store', default=None,
                    dest='data',
                    help='choose sequence file')
parser.add_argument('-gpu', action='store', default="0",
                    dest='gpu',
                    help='choose gpu number')
parser.add_argument('-name', action='store', default="model1",
                    dest='name',
                    help='weights will be stored with this name')
parser.add_argument('-model_name', action='store', default=None,
                    dest='model_name',
                    help='name of the model to call')
parser.add_argument('-log_file', action='store',
                    dest='log_file',
                    help='Log file')

import keras.backend as K

def loss_fn(y_true, y_pred):
        return 1/np.log(2) * K.categorical_crossentropy(y_true, y_pred)

def strided_app(a, L, S):  # Window len = L, Stride len/stepsize = S
        nrows = ((a.size - L) // S) + 1
        n = a.strides[0]
        return np.lib.stride_tricks.as_strided(a, shape=(nrows, L), strides=(S * n, n), writeable=False)


def generate_single_output_data(file_path,batch_size,time_steps):
        series = np.load(file_path)
        series = series.reshape(-1, 1)
        onehot_encoder = OneHotEncoder(sparse=False)
        onehot_encoded = onehot_encoder.fit(series)

        series = series.reshape(-1)

        data = strided_app(series, time_steps+1, 1)
        l = int(len(data)/batch_size) * batch_size

        data = data[:l] 
        X = data[:, :-1]
        Y = data[:, -1:]
        
        Y = onehot_encoder.transform(Y)
        return X,Y

        
def fit_model(X, Y, bs, nb_epoch, model):
        y = Y
        optim = keras.optimizers.Adam(lr=1e-3, beta_1=0.9, beta_2=0.999, epsilon=1e-3, decay=0, amsgrad=False)
        model.compile(loss=loss_fn, optimizer=optim)
        checkpoint = ModelCheckpoint(arguments.name, monitor='loss', verbose=1, save_best_only=True, mode='min', save_weights_only=True)
        csv_logger = CSVLogger(arguments.log_file, append=True, separator=';')
        callbacks_list = [checkpoint, csv_logger]
        for i in range(nb_epoch):
                model.fit(X, y, epochs=1, batch_size=bs, verbose=1, shuffle=True, callbacks=callbacks_list)
                model.reset_states()
 

                
                
arguments = parser.parse_args()
print(arguments)

batch_size=1024
sequence_length=64
num_epochs=10

X,Y = generate_single_output_data(arguments.data,batch_size, sequence_length)
model = getattr(models, arguments.model_name)(batch_size, sequence_length, Y.shape[1])
fit_model(X, Y, batch_size,num_epochs , model)

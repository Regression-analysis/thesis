import os, sys
import numpy as np
from keras.models import Sequential
from keras.layers import Dense


def main():

    model = Sequential()

    model.add(Dense(units=8, activation='relu', input_dim=8))
    model.add(Dense(units=8, activation='relu'))
    model.add(Dense(units=1, activation='sigmoid'))

    model.compile(loss='binary_crossentropy',
                optimizer='rmsprop',
                metrics=['binary_accuracy'])

    x_data, y_data = get_data()

    cutoff = int( .9 * len(x_data) )

    x_train = np.array(x_data[:cutoff])
    y_train = np.array(y_data[:cutoff])
    x_test = np.array(x_data[cutoff:])
    y_test = np.array(y_data[cutoff:])


    model.fit(x_train, y_train, epochs=5, batch_size=32)

    loss_and_metrics = model.evaluate(x_test, y_test, batch_size=32)

    print(loss_and_metrics)


def get_data():
    x_data = []
    y_data = []

    with open(os.getcwd() + '/' + sys.argv[1]) as f:
        next(f) # Skip headers
        for line in f:
            cols = line.split(',')
            inputs = [
                float(cols[3]),
                float(cols[4]),
                float(cols[5]),
                float(cols[6]),
                float(cols[7]),
                0,              #float(cols[8]),
                float(cols[9]),
                float(cols[10]),
            ]
            outputs = [ int(cols[11]) ]

            x_data.append(inputs)
            y_data.append(outputs)

    return x_data, y_data


if __name__ == '__main__':
    main()

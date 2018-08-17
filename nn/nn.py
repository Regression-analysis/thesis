import os, sys
import numpy as np
from random import random
from matplotlib import pyplot
from keras import backend as K
from keras.callbacks import Callback
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import sgd, rmsprop

def main():
    with open(sys.argv[2], 'a') as f:
        optimizers = ['sgd']
        samples = 5
        loss_functions = [G, tp_loss]

        for loss_function in loss_functions:
            for optimizer in optimizers:
                s_TP = 0
                s_TN = 0
                s_FN = 0
                s_FP = 0
                s_hr = 0
                s_dr = 0
                f.write('loss_function: %s\n' % loss_function.__name__)
                f.write('optimizer: %s\n' % optimizer)
                f.write('tp, tn, fn, fp, hr, dr\n')
                for i in range(0, samples):
                    TP, TN, FN, FP, hr, dr = doit(loss_function, optimizer)
                    f.write("%s, %s, %s, %s, %s, %s\n" % (TP, TN, FN, FP, hr, dr))
                    f.flush()
                    s_TP += TP
                    s_TN += TN
                    s_FN += FN
                    s_FP += FP
                    s_hr += hr
                    s_dr += dr
                f.write("Averages:\n")
                f.write("%s, %s, %s, %s, %s, %s\n" % (s_TP / samples,
                                              s_TN / samples,
                                              s_FN / samples,
                                              s_FP / samples,
                                              s_hr / samples,
                                              s_dr / samples))


def doit(loss_function, optimizer):

    model = Sequential()

    model.add(Dense(units=64, activation='relu', input_dim=8))
    model.add(Dense(units=64, activation='relu'))
    model.add(Dense(units=1, activation='sigmoid'))


    model.compile(loss=loss_function,
                optimizer=optimizer,
                metrics=['accuracy', tp, tn, fp, fn])

    x_data, y_data = get_data()

    cutoff = int( .9 * len(x_data) )

    x_train = np.array(x_data[:cutoff])
    y_train = np.array(y_data[:cutoff])
    x_test = np.array(x_data[cutoff:])
    y_test = np.array(y_data[cutoff:])


    history = model.fit(x_train, y_train, epochs=10, batch_size=32)

    n_N = 0
    n_P = 0
    n_FN = 0
    n_FP = 0
    n_TN = 0
    n_TP = 0
    r_FN = 0
    r_FP = 0
    r_TN = 0
    r_TP = 0
    for index, x in enumerate(x_data):
        truth = y_data[index][0]
        random_prediction = round(random())
        prediction = round(model.predict(np.array([x]))[0][0])
        if truth == 0:
            n_N += 1
            if prediction == 0:
                n_TN += 1
            else:
                n_FP += 1

            if random_prediction == 0:
                r_TN += 1
            else:
                r_FP += 1

        else:
            n_P += 1
            if prediction == 0:
                n_FN += 1
            else:
                n_TP += 1

            if random_prediction == 0:
                r_FN += 1
            else:
                r_TP += 1

    print("Model:",
          "tp", n_TP,
          "tn", n_TN, 
          "fn", n_FN, 
          "fp", n_FP,
          "hr", "%.3f" % (n_TP / n_P),
          "dr", "%.3f" % (n_TN / n_N))

    print("Random:",
          "tp", r_TP,
          "tn", r_TN, 
          "fn", r_FN, 
          "fp", r_FP,
          "hr", "%.3f" % (r_TP / n_P),
          "dr", "%.3f" % (r_TN / n_N))


    loss_and_metrics = model.evaluate(x_test, y_test, batch_size=1)

    print(loss_and_metrics[2:])

    return n_TP, n_TN, n_FN, n_FP, n_TP / n_P, n_TN / n_N


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


def differentiable_round(tensor):
    # round numbers less than 0.5 to zero;
    # by making them negative and taking the maximum with 0
    res = K.maximum(tensor-0.499,0)
    # scale the remaining numbers (0 to 0.5) to greater than 1
    # the other half (zeros) is not affected by multiplication
    res = res * 10000
    # take the minimum with 1
    res = K.minimum(res, 1)
    return res

def confusion(y_true, y_pred):
    y_pos = differentiable_round(y_true)
    y_neg = 1 - y_pos
    y_pred_pos = differentiable_round(y_pred)
    y_pred_neg = 1 - y_pred_pos
    tp = K.sum(y_pos * y_pred_pos) / (K.sum(y_pos) + K.epsilon())
    tn = K.sum(y_neg * y_pred_neg) / (K.sum(y_neg) + K.epsilon())
    fn = K.sum(y_pos * y_pred_neg) / (K.sum(y_pos) + K.epsilon())
    fp = K.sum(y_neg * y_pred_pos) / (K.sum(y_neg) + K.epsilon())
    return { "tp": tp, "tn": tn, "fn": fn, "fp": fp }

def fn(y_true, y_pred):
    return confusion(y_true, y_pred)["fn"]

def tp(y_true, y_pred):
    return confusion(y_true, y_pred)["tp"]

def tp_loss(y_true, y_pred):
    return 1 - confusion(y_true, y_pred)["tp"]

def tn(y_true, y_pred):
    return confusion(y_true, y_pred)["tn"]

def fp(y_true, y_pred):
    return confusion(y_true, y_pred)["fp"]

def F(y_true, y_pred):
    c = confusion(y_true, y_pred)
    return .1 * c["fp"] + c["fn"]

def G(y_true, y_pred):
    c = confusion(y_true, y_pred)
    tpl = 1 - c["tp"]
    tnl = 1 - c["tn"]
    return tpl + tnl + c["fn"]

if __name__ == '__main__':
    main()

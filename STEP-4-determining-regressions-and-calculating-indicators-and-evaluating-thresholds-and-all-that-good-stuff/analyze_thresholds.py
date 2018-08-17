import sys
import math

"""

This is for analyzing the individual indicators. In the original paper,
do you remember seeing the graphs? There are graphs of hit and dismiss
rates for each indicator, when considered individually? That's what this
file does. It makes csv files, which you can open in google sheets
and easily turn into a graph just like in the paper

"""


def evaluate_thresholds(thresholds):
    hit_truths = 0
    dismiss_truths = 0
    hits = [0,0,0,0, 0,0,0,0]
    dismisses = [0,0,0,0, 0,0,0,0]
    with open(sys.argv[1]) as f:
        headers = next(f)
        for line in f:
            columns = line.split(',')
            commit_pair = (columns[0], columns[1])
            test = columns[2].split('.sh')[0]
            is_significant = True if '1' in columns[11] else False

            if is_significant:
                hit_truths += 1
            else:
                dismiss_truths += 1

            for index, indicator_result in enumerate(columns[9:-1]):
                if indicator_result == 'False':
                    indicator_result = 0
                indicator_result = float(indicator_result)
                if indicator_result >= thresholds[index] and is_significant:
                    hits[index] += 1
                elif indicator_result < thresholds[index] and not is_significant:
                    dismisses[index] += 1

    return ([h / hit_truths for h in hits], [d / dismiss_truths for d in dismisses])


def make_csv():
    """ The original main function """
    everything = { 'thresholds': [], 'hit_rates': [], 'dismiss_rates': [] }
    thresholds = [0,0,0,0, 0,0,0,0]
    for i in range(0, 1000):
        results = evaluate_thresholds(thresholds)
        everything['thresholds'].append(thresholds)
        everything['hit_rates'].append(results[0])
        everything['dismiss_rates'].append(results[1])

        print(i)

        thresholds = [(t + .01) for t in thresholds]

    for i in range(0, 8):
        print('Indicator', i+1)
        for t, h, d in zip(everything['thresholds'],
                everything['hit_rates'],
                everything['dismiss_rates']):
            print('%.3f' % t[i], '%.3f' % h[i], '%.3f' % d[i])



def main():
    make_csv()


if __name__ == '__main__':
    main()

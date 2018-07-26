import math
from determine_significant_changes import determine_significant_changes


def evaluate_thresholds(thresholds, significant_changes):
    hit_truths = 0
    dismiss_truths = 0
    hits = [0,0,0,0, 0,0,0,0]
    dismisses = [0,0,0,0, 0,0,0,0]
    with open('perphecy_raw_number_results.csv') as f:
        headers = next(f)
        for line in f:
            columns = line.split(',')
            commit_pair = (columns[0], columns[1])
            test = columns[2].split('.sh')[0]
            this_pair_is_significant = False
            for cp in significant_changes[test]:
                if commit_pair[0] in cp[0] and commit_pair[1] in cp[1]:
                    this_pair_is_significant = True
                    break

            if this_pair_is_significant:
                hit_truths += 1
            else:
                dismiss_truths += 1

            for index, indicator_result in enumerate(columns[3:]):
                if indicator_result == 'False':
                    indicator_result = 0
                indicator_result = float(indicator_result)
                if indicator_result >= thresholds[index] and this_pair_is_significant:
                    hits[index] += 1
                elif indicator_result < thresholds[index] and not this_pair_is_significant:
                    dismisses[index] += 1

    return ([h / hit_truths for h in hits], [d / dismiss_truths for d in dismisses])


def make_csv():
    """ The original main function """
    significant_changes = determine_significant_changes("results.csv")
    everything = { 'thresholds': [], 'hit_rates': [], 'dismiss_rates': [] }
    thresholds = [0,0,0,0, 0,0,0,0]
    for i in range(0, 1000):
        results = evaluate_thresholds(thresholds, significant_changes)
        everything['thresholds'].append(thresholds)
        everything['hit_rates'].append(results[0])
        everything['dismiss_rates'].append(results[1])

        print(i)

        thresholds = [(t + 0.01) for t in thresholds]

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

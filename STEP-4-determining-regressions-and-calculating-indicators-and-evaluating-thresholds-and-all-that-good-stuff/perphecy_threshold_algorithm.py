import math
import sys

def get_H_and_D():
    """
    Determine the set of significant and insignificant
    (commit, commit, benchmark) tuples
    """
    H = []
    D = []
    with open(sys.argv[1]) as f:
        headers = next(f)
        for line in f:
            columns = line.split(',')
            if len(columns) == 1:
                continue
            commit_pair = (columns[0], columns[1])
            test = columns[2].split('.sh')[0]
            is_significant = True if '1' in columns[11] else False

            if is_significant:
                values = [0 if v == 'False' else float(v) for v in columns[3:]]
                H.append( (commit_pair[0], commit_pair[1], test, values) )
            else:
                values = [0 if v == 'False' else float(v) for v in columns[3:]]
                D.append( (commit_pair[0], commit_pair[1], test, values) )

    return H, D


def get_I():
    return [
        'Del Func X',
        'New Func X',
        'Reached Del Func X',
        'Top Chg by Call X',
        'Top X% by Call Chg by >= 10%',
        'Top Chg by Instr X',
        'Top Chg Len X',
        'Top Reached Chg Len X',
    ]

def maxthresh(h, i):
    i_index = get_I().index(i)
    return h[3][i_index]

def allhits(i, thresh_for_hs, S):
    i_index = get_I().index(i)
    return [d for d in S if d[3][i_index] >= thresh_for_hs]


def perphecy_threshold_algorithm():
    T = set()
    H, D = get_H_and_D()
    I = get_I()
    min_price_thresh = {}
    min_price = {}
    min_price_ind = {}

    for h_info in H:
        h = (h_info[0], h_info[1], h_info[2])
        min_price_thresh[h] = None
        min_price[h] = math.inf
        min_price_ind[h] = None
        for i in I:
            thresh_for_hs = maxthresh(h_info, i)
            price_for_hs = len( allhits(i, thresh_for_hs, D) )
            if price_for_hs < min_price[h]:
                min_price[h] = price_for_hs
                min_price_thresh[h] = thresh_for_hs
                min_price_ind[h] = i


    C = H # I know this does a reference and not a copy, but it's fine
    while len(C) != 0:
        max_min_price = 0
        target_ind = None
        target_thresh = None
        for h_info in C:
            h = (h_info[0], h_info[1], h_info[2])
            if min_price[h] > max_min_price:
                target_thresh = min_price_thresh[h]
                max_min_price = min_price[h]
                target_ind = min_price_ind[h]

        T.add( (target_ind, target_thresh) )
        C = [c for c in C if c not in allhits(target_ind, target_thresh, C)]


    return T


def main():
    indicators = perphecy_threshold_algorithm()
    print(indicators)


if __name__ == '__main__':
    main()

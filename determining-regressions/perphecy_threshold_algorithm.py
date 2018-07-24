def get_H_and_D():
    """
    Determine the set of significant and insignificant
    (commit, commit, benchmark) tuples
    """
    H = set()
    D = set()
    significant_changes = determine_significant_changes('results.csv')
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

            if this_pair_is_significant:
                H.add( (commit_pair[0], commit_pair[1], test) )
            else:
                D.add( (commit_pair[0], commit_pair[1], test) )

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
    pass

def allhits(i, thresh_for_hs, D):
    pass


def perphecy_threshold_algorithm():
    H, D = get_H_and_D()
    I = get_I()
    min_price_thresh = {}
    min_price = {}
    min_price_ind = {}

    for h in H:
        min_price_thresh[h] = None
        min_price[h] = math.inf
        min_price_ind[h] = None
        for i in I:
            thresh_for_hs = maxthresh(h, i)
            price_for_hs = len( allhits(i, thresh_for_hs, D) )
            if price_for_hs < min_price[h]:
                min_price[h] = price_for_hs
                min_price_thresh[h] = thresh_for_hs
                min_price_ind[h] = i



    import ipdb; ipdb.set_trace()


def main():
    perphecy_threshold_algorithm()


if __name__ == '__main__':
    main()

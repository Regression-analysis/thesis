import sys

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

def main():
    ### This is where you put in the predictor you generated
    predictor = [
        ('New Func X', 44),
        ('Top Chg by Call X', .07),
        ('Reached Del Func X', 2),
        ('Top Reached Chg Len X', 1.0),
    ]

    tp = 0
    tn = 0
    fp = 0
    fn = 0
    total_dismisses = 0
    total_hits = 0

    with open(sys.argv[1]) as f:
        header = next(f)
        for line in f:
            columns = line.split(',')
            indicators = columns[3:len(columns)-1]
            assert len(indicators) is 8

            predict_hit = False
            for ind in predictor:
                if float(indicators[get_I().index(ind[0])]) >= ind[1]:
                    predict_hit = True

            if int(columns[len(columns)-1]) == 1:
                total_hits += 1

                if predict_hit:
                    tp += 1
                else:
                    fn += 1
            else:
                total_dismisses += 1

                if predict_hit:
                    fp += 1
                else:
                    tn += 1

    print(tp, tn, fp, fn)
    print('Hit Rate:', tp / total_hits)
    print('Dismiss Rate:', tn / total_dismisses)



if __name__ == '__main__':
    main()

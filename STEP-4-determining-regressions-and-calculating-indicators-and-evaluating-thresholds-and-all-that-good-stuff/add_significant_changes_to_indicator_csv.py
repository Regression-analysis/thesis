import sys
from determine_significant_changes import determine_significant_changes

significant_changes = determine_significant_changes(sys.argv[2])

with open('outpuuuuut', 'a') as o:
    with open(sys.argv[1]) as f:
        o.write(next(f)[:-1] + ',Hit/Dismiss\n')
        for l in f:
            cols = l.split(',')
            if len(cols) <= 1:
                print('Not enough columns', l)
                continue

            test = cols[2].split('.sh')[0]
            c1 = cols[0]
            c2 = cols[1]
            hit = 0
            if test in significant_changes:
                for c_pair in significant_changes[test]:
                    if c1 in c_pair[0] and c2 in c_pair[1]:
                        hit = 1

            o.write(l[:-1] + ',' + str(hit) + '\n')

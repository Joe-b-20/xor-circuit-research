import pickle, sys, collections
P = pickle.load(open(sys.argv[1], 'rb'))
c = collections.Counter(zip(P['b'], P['j']))
print('distinct (b,j):', len(c), 'multiplicity histogram:', collections.Counter(c.values()), 'b=0 members:', sum(1 for b in P['b'] if b == 0))

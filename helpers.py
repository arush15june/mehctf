from collections import OrderedDict

def sortScoreDict(unsorted):
     return OrderedDict(sorted(unsorted.items(), key=lambda t: t[1]['solved'], reverse=True))

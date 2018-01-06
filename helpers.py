from collections import OrderedDict
from operator import attrgetter

def sortScoreDict(unsorted):
    return OrderedDict(sorted(unsorted.items(), key=lambda t: t[1]['score'], reverse=True))

def sortSolvedQuesDict(unsorted):
    return OrderedDict(sorted(unsorted.items(), key=lambda solvedq: solvedq['date']))
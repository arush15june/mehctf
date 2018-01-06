from collections import OrderedDict
from operator import attrgetter

def sortScoreDict(unsorted):
    return OrderedDict(sorted(unsorted.items(), key=lambda t: (t[1]['last_question_date'], t[1]['score']) , reverse=True))

def sortSolvedQuesList(unsorted):
    return sorted(unsorted, key=lambda solvedq: solvedq.date)
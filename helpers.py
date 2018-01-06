from collections import OrderedDict
from operator import attrgetter

def sortScoreDict(unsorted):
    sorted_list = sorted(unsorted.items(), key=lambda t: (t[1]['last_question_date']) )
    sorted_list = sorted(sorted_list, key=lambda t: (t[1]['score']), reverse=True)
    return OrderedDict(sorted_list)

def sortSolvedQuesList(unsorted):
    return sorted(unsorted, key=lambda solvedq: solvedq.date)
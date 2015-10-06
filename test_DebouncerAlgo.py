#!/usr/bin/python -u

def debounce(val) :
    if val != debounce.state :
        if debounce.toggle_count == 0 :
            debounce.back_count = 0

        if debounce.toggle_count == debounce.debounce :
            debounce.state = val
            debounce.back_count = 0
            debounce.toggle_count = 0
        else :
            debounce.toggle_count += 1
    else :
        if debounce.toggle_count > 0 :
            if debounce.back_count < debounce.debounce :
                debounce.back_count += 1

    if debounce.back_count == debounce.debounce :
        debounce.toggle_count = 0
        
    return debounce.state


def test(signal) :
    debounce.state = 1
    debounce.back_count = 0
    debounce.toggle_count = 0
    debounce.debounce = 3

    print signal
    result = []
    for v in signal :
        result.append( debounce(v) )
    print result
    print
    
regular = [1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1]
test(regular)

twobounces = [1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1]
test(twobounces)

threebounces = [1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1]
test(threebounces)

mixbounces = [1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0]
test(mixbounces)

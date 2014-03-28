import os

def truncate_front(line, length=70):
    reduce_amt = len(line) - length
    # If it already fits
    if reduce_amt <= 0 or length <= 0:
        return line 

    reduce_amt += 3 # for the ellipsis
    return '...'+line[reduce_amt:]

def truncate_middle(line, length=70):
    reduce_amt = len(line) - length

    # If it already fits
    if reduce_amt <= 0 or length <= 0:
        return line 

    reduce_amt += 3 # for the ellipsis

    start = (len(line) / 2) - (reduce_amt / 2)
    end = start + reduce_amt
    return "%s...%s" % (line[:start], line[end:])

def rec_dir_up(dir):
    if os.path.isdir(dir):
        while True:
            yield dir 
            newdir = os.path.split(dir)[0]
            if newdir == dir: break
            dir = newdir


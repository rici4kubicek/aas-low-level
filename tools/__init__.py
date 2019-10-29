
def valmap(value, istart, istop, ostart, ostop):
    """ Re-maps a number from one range to another. That is, a value of istart would get mapped to ostart, a value of
        istop to ostop, values in-between to values in-between, etc.
    """
    if value <= istart:
        return ostart
    elif value >= istop:
        return ostop
    else:
        return (value - istart) * (ostop - ostart) / (istop - istart) + ostart

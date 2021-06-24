import datetime
from dateutil.relativedelta import relativedelta


def day_suffix(day):
    day = int(day)
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return suffix


def time_ago(time_input):
    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)

    if type(time_input) is datetime.datetime:
        then = time_input.replace(microsecond=0)
    elif type(time_input) is float or type(time_input) is int:
        then = datetime.datetime.fromtimestamp(time_input)
        then = then.replace(microsecond=0)
    else:
        raise TypeError("Wrong type input for time_ago function")

    delta = relativedelta(now, then)

    attrs = ["years", "months", "weeks", "days", "hours", "minutes", "seconds"]
    results = []

    for attr in attrs:
        elem = getattr(delta, attr)
        if not elem:
            continue
        else:
            if attr == "days":
                weeks = delta.weeks
                if weeks > 0:
                    elem -= weeks * 7

            if elem is 1:
                results.append("{} {}".format(elem, attr[:-1]))
            else:
                results.append("{} {}".format(elem, attr))

    result_str = ", ".join(results)
    last_comma_index = result_str.rfind(",")
    if last_comma_index != -1:
        result_str = result_str[:last_comma_index] + " and " + result_str[last_comma_index+2:]
    return result_str

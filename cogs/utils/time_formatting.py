import datetime
from dateutil.relativedelta import relativedelta


def time_ago(time_input):
    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)

    if type(time_input) is datetime.datetime:
        # print("dt")
        then = time_input.replace(microsecond=0)
    elif type(time_input) is float or type(time_input) is int:
        # print("number", time_input)
        # then_ts = now.timestamp() - time_input
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
            # print(elem)
            if elem is 1:
                results.append("{} {}".format(elem, attr[:-1]))
            else:
                results.append("{} {}".format(elem, attr))

    return ", ".join(results)

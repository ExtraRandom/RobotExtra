import datetime
from dateutil.relativedelta import relativedelta
import pytz

UTC = pytz.utc


def day_suffix(day: int):
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return suffix


def seconds_to_time(time_input):
    return "{}".format(str(datetime.timedelta(seconds=time_input)))


def time_ago(time_input, brief=False, force_into_utc=False):
    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)

    if type(time_input) is datetime.datetime:
        then = time_input.replace(microsecond=0)
    elif type(time_input) is float or type(time_input) is int:
        if not force_into_utc:
            then = datetime.datetime.fromtimestamp(time_input)
        else:
            then = datetime.datetime.utcfromtimestamp(time_input)
        then = then.replace(microsecond=0)
    else:
        raise TypeError("Wrong type input for time_ago function")

    now = now.replace(tzinfo=UTC)  # print(now)
    then = then.replace(tzinfo=UTC)  # print(then)

    delta = relativedelta(now, then)

    attrs = ["years", "months", "weeks", "days", "hours", "minutes", "seconds"]

    results = []
    r_count = 0  # count how attrs have been added (used for brief)

    for attr in attrs:
        elem = getattr(delta, attr)
        if not elem:
            continue
        else:

            if attr == "days":
                weeks = delta.weeks
                if weeks > 0:
                    elem -= weeks * 7

                if elem == 0:
                    continue

            if brief is True and (attr == "hours" or attr == "minutes" or attr == "seconds"):
                if r_count > 1:  # if more than one attr exists (e.g. month + day) then break to keep it brief
                    break

            if elem == 1:
                results.append("{} {}".format(elem, attr[:-1]))
            else:
                results.append("{} {}".format(elem, attr))

            r_count += 1

    result_str = ", ".join(results)
    last_comma_index = result_str.rfind(",")
    if last_comma_index != -1:
        result_str = result_str[:last_comma_index] + " and " + result_str[last_comma_index+2:]
    return result_str

import datetime


def time_ago(time_input):
    if type(time_input) is datetime.datetime:
        # print("dt yeah")
        return datetime_to_time_ago(time_input)
    elif type(time_input) is float:
        # print("float yeah")
        return timestamp_to_time_ago(time_input)
    else:
        print("{} no".format(type(time_input)))
        return 0


def datetime_to_time_ago(dt):
    now = datetime.datetime.utcnow().timestamp()
    then = dt.timestamp()
    passed = now - then
    return timestamp_to_time_ago(passed)


def timestamp_to_time_ago(timestamp):
    def pluralise(time_number: int, time_name):
        if time_number == 1:
            return "{} {}".format(time_number, time_name)
        else:
            return "{} {}s".format(time_number, time_name)

    times_dict = timestamp_breakdown(timestamp)
    result = []

    years = times_dict["years"]
    months = times_dict["months"]
    weeks = times_dict["weeks"]
    days = times_dict["days"]
    hours = times_dict["hours"]
    minutes = times_dict["minutes"]
    seconds = times_dict["seconds"]

    if years > 0:
        result.append(pluralise(years, "year"))

    if months > 0:
        result.append(pluralise(months, "month"))

    if weeks > 0:
        result.append(pluralise(weeks, "week"))

    if days > 0:
        result.append(pluralise(days, "day"))

    if hours > 0:
        result.append(pluralise(hours, "hour"))

    if minutes > 0:
        result.append(pluralise(minutes, "minute"))

    if seconds > 0:
        result.append(pluralise(seconds, "second"))

    if len(result) == 0:
        return "Less than a second"

    return ", ".join(result)


def timestamp_breakdown(timestamp):
    t = datetime.timedelta(seconds=timestamp)

    total_seconds = t.total_seconds()  # total_weeks = t.days // 7
    years = t.days // 365  # total_weeks // 52

    without_years = datetime.timedelta(seconds=total_seconds - (years * 60 * 60 * 24 * 365))  # 7 * 52
    months = without_years.days // 30  # // (7 * 4)
    months_seconds = months * 60 * 60 * 24 * 30  # * 7 * 4

    without_months = datetime.timedelta(seconds=without_years.total_seconds() - months_seconds)
    weeks = without_months.days // 7
    weeks_seconds = weeks * 7 * 24 * 60 * 60

    without_weeks = datetime.timedelta(seconds=without_months.total_seconds() - weeks_seconds)
    days = without_weeks.days
    hours = without_weeks.seconds//3600
    minutes = (without_weeks.seconds//60) % 60
    seconds = without_weeks.seconds - hours*3600 - minutes*60

    result = {
        "years": years,
        "months": months,
        "weeks": weeks,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds
    }

    return result


def old_timestamp_to_time_ago(timestamp):
    def pluralise(time_number: int, time_name):
        if time_number == 1:
            return "{} {}".format(time_number, time_name)
        else:
            return "{} {}s".format(time_number, time_name)

    t = datetime.timedelta(seconds=timestamp)

    days = t.days
    hours = t.seconds//3600
    minutes = (t.seconds//60) % 60
    seconds = t.seconds - hours*3600 - minutes*60

    result = []

    if days > 0:
        result.append(pluralise(days, "day"))

    if hours > 0:
        result.append(pluralise(hours, "hour"))

    if minutes > 0:
        result.append(pluralise(minutes, "minute"))

    if seconds > 0:
        result.append(pluralise(seconds, "second"))

    if len(result) == 0:
        return "Less than a second"

    return ", ".join(result)

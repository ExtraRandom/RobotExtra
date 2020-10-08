import datetime


def timestamp_to_time_ago(timestamp):
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

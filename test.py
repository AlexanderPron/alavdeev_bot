import datetime
from datetime import date
import time


def get_free_daytime(day, time_start="0:0", time_end="23:59"):
    t1 = time.strptime(time_start, "%H:%M")
    t2 = time.strptime(time_end, "%H:%M")
    ts = (day + datetime.timedelta(hours=t1.tm_hour, minutes=t1.tm_min)).strftime('%Y-%m-%dT%H:%M:%S+03:00')
    te = (day + datetime.timedelta(hours=t2.tm_hour, minutes=t2.tm_min)).strftime('%Y-%m-%dT%H:%M:%S+03:00')
    return((ts, te))


def main():
    day = datetime.datetime(2022, 6, 16)
    ts = "10:30"
    te = "18:30"
    print(get_free_daytime(day, ts, te))
    print(get_free_daytime(day))


if __name__ == '__main__':
    main()

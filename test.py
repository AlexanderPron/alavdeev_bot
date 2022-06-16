import datetime
from datetime import date
import time


# def get_free_daytime(day, time_start="0:0", time_end="23:59"):
def get_free_daytime():
    # t1 = time.strptime(time_start, "%H:%M")
    # t2 = time.strptime(time_end, "%H:%M")
    # ts = (day + datetime.timedelta(hours=t1.tm_hour, minutes=t1.tm_min)).strftime('%Y-%m-%dT%H:%M:%S+03:00')
    # te = (day + datetime.timedelta(hours=t2.tm_hour, minutes=t2.tm_min)).strftime('%Y-%m-%dT%H:%M:%S+03:00')
    start = datetime.datetime.strptime('2022-06-18T15:00+03:00', '%Y-%m-%dT%H:%M+03:00')
    end = datetime.datetime.strptime('2022-06-18T17:00+03:00', '%Y-%m-%dT%H:%M+03:00')
    return((end - start).total_seconds() / 60)


def main():
    # day = datetime.datetime(2022, 6, 16)
    # ts = "10:30"
    # te = "18:30"
    # print(get_free_daytime(day, ts, te))
    # print(get_free_daytime(day))
    print(get_free_daytime())


if __name__ == '__main__':
    main()

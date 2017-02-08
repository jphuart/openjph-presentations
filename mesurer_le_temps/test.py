import datetime
from dateutil.tz import gettz

utc_zone = gettz('UTC')

delta = datetime.datetime(2017,01,01,01,00,00,00,tzinfo=utc_zone)-datetime.datetime(2016,12,31,23,00,00,00,tzinfo=utc_zone)
print delta
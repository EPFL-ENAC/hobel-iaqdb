## How readings are combined

The studies in the database measure at different time steps. Some instruments take a reading every minute, others every 10 minutes or every hour. A passive sampler gives one value for a period of several days. Before Explore draws a chart, it puts these readings on one time scale.

#### Hourly means

For each dataset, space, instrument and pollutant, Explore takes the mean of the readings in each clock hour. An instrument that reads every minute gives the mean of 60 readings. An instrument that reads every 10 minutes gives the mean of 6 readings. An instrument that reads every hour gives its one reading. An hour without a reading has no hourly mean. The hours are those of the local clock time that the study recorded.

#### Daily means and the mean of a space

A daily mean is the mean of all the readings of one day, for one dataset, space, instrument and pollutant. If an instrument read only in the morning, the daily mean is the mean of the morning. The mean of a space is the mean of all its readings in the selected period.

#### Which mean a chart uses

In most charts, the values use the averaging time of the reference. A one-hour reference compares with hourly means, and a daily reference with daily means. A yearly reference compares with the mean of each space. If a chart has no reference, it uses daily means. The monthly pattern always shows daily means, and only its share above the reference uses the averaging time of the reference. The reading note under the title of each chart says which mean it uses.

The relationship charts use hourly means. If one dataset measured two pollutants in the same space in the same hour, the two hourly means make a pair. The charts put the pairs of all the datasets in scope together.

#### How much each record counts

The medians, the percentiles and the shares above a reference count each hourly or daily mean once. A space measured for one year gives 8,760 hourly means, and a space measured for one week gives 168. A long record thus counts more than a short one.

The record counts, for example in "Records by pollutant", count every reading. An instrument that reads every minute gives 60 records in one hour, and an hourly instrument gives one.

#### What is left out, and what is not

Explore leaves out summary statistics that a study reports for a period in place of readings, for example a monthly mean or a 95th percentile. The database keeps them, but the charts do not show them yet.

Explore does not leave out samples taken over a period, for example a passive sampler left in a room for 7 days. Each sample counts as one reading in the first hour and on the first day of its period. The charts thus treat a 7-day mean like a 1-hour mean. This matters most for pollutants that are often measured with passive samplers, for example formaldehyde, nitrogen dioxide and benzene.

"""
Analytic tools for evaluating telemetry performance
"""

__all__ = [
    "find_full_range",
    "date_range",
    "get_timestamps",
    "get_messages_per_hour",
    "create_telemetry_report",
    "create_telemetry_report_figure",
]

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd

from datetime import datetime, timezone, timedelta
from microSWIFTtelemetry.pull_telemetry import pull_telemetry_as_json, pull_telemetry_as_var


#%%
def find_full_range(
    X1: np.ndarray,
    X2: np.ndarray,
)-> tuple:
    """
    Compare two arrays of datetimes to determine the full range of their union.

    Arguments:
        - X1 (np.ndarray), first array of datetimes
        - X2 (np.ndarray), second array of datetimes

    Returns:
        - (tuple), range of union(X1,X2)
    """
    x_min = min([X1.min(), X2.min()])
    x_max = max([X1.max(), X2.max()])
    return (x_min, x_max)

def date_range(
    start: datetime,
    end: datetime, 
    msgPerHr: float,
)-> pd.DatetimeIndex:
    """
    Helper function for generating a date range with a frequency corresponding
    to the number of telemetered messages per hour.

    Arguments:
        - start (datetime), start of date range
        - end (datetime), end of date range
        - msgPerHr (float), messages per hour

    Returns:
        - (pd.DatetimeIndex), date range with frequency of msgPerHr
    """
    dateRange = pd.date_range(
        start, 
        end, 
        freq = f'{msgPerHr}H', 
        tz = timezone.utc
    ) 
    return dateRange

def get_timestamps(
    buoyID: str,
    startDate: datetime,
    endDate: datetime = datetime.utcnow(),
):
    """
    TODO: _summary_

    Arguments:
        - buoyID (_type_), _description_
        - start (_type_), _description_
        - end (_type_), _description_

    Returns:
        - (_type_), _description_
    """
    SWIFT_json = pull_telemetry_as_json(buoyID = buoyID, startDate = startDate, endDate = endDate)
    serverTimestamps = [msg['timestamp'] for msg in SWIFT_json['buoys'][0]['data']]
    serverTimestamps = pd.to_datetime(serverTimestamps, format='%Y-%m-%dT%H:%M:%S%Z') # datetime.strptime(serverTimes[0], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)

    SWIFT_dict = pull_telemetry_as_var(buoyID = buoyID, startDate = startDate, endDate = endDate, varType = 'dict')
    onboardTimestamps = SWIFT_dict['datetime']

    return serverTimestamps, onboardTimestamps

def get_messages_per_hour(onboardTimestamps, burstInterval):

    if burstInterval is None:
        msgRate = np.diff(onboardTimestamps)
        msgPerHr = np.round(np.mean(msgRate[msgRate > timedelta(0)]).total_seconds() / 3600)
        print(f'Inferred burst rate of {msgPerHr} messages per hour.')
    else:
        msgPerHr = burstInterval/60
        print(f'Burst rate of {msgPerHr} messages per hour.')
    
    return msgPerHr

def create_telemetry_report(
    buoyID: str, 
    startDate: datetime, 
    endDate: datetime, 
    burstInterval: int = None,
    trim_to_query_limits: bool = True,
)-> dict:
    #TODO:
    serverTimestamps, onboardTimestamps = get_timestamps(buoyID, startDate, endDate)
    msgPerHr = get_messages_per_hour(onboardTimestamps, burstInterval)

    startRange = onboardTimestamps.min().replace(minute=0, second=0)
    endRange = onboardTimestamps.max().replace(minute=0, second=0)

    onboardDateRange = date_range(startRange, endRange, msgPerHr)
    queriedDateRange = date_range(startDate, endDate, msgPerHr) 
    #TODO: queriedDateRange = date_range(startDate, endDate + timedelta(hours=msgPerHr), msgPerHr)
    minDate, maxDate = find_full_range(onboardDateRange, queriedDateRange)
    allCallWindows = date_range(minDate, maxDate, msgPerHr)

    if trim_to_query_limits == True:
        plotLimits = (startDate, endDate)
    else:
        plotLimits = (minDate, maxDate + timedelta(hours=msgPerHr))

    fig, ax = create_telemetry_report_figure(
        (startDate, endDate),
        serverTimestamps, 
        onboardTimestamps, #TODO: queriedDateRange?
        allCallWindows,
        msgPerHr,
        plotLimits,
        barLabelLimit = 65,
    )
    fig.suptitle('microSWIFT' + buoyID)
    # fig.show()
    print('')


def create_telemetry_report_figure(
    queryLimits,
    serverTimestamps, 
    onboardTimestamps,
    allCallWindows,
    msgPerHr,
    plotLimits,
    barLabelLimit = 50,
)-> mpl.axes.Axes:

    if (plotLimits[1] - plotLimits[0]).total_seconds()/3600/msgPerHr > barLabelLimit:
        label_bars = False
    else:
        label_bars = True

    fig,ax = plt.subplots(figsize = (8, 3))

    serverCounts, _, serverBars = ax.hist(
        serverTimestamps,
        bins= allCallWindows,
        color='red',
        edgecolor='red',
        alpha=0.5,
        label= f'received (n={len(serverTimestamps)})'
    )

    onboardCounts, _, onboardBars = ax.hist(
        onboardTimestamps,
        bins= allCallWindows,
        color='royalblue',
        edgecolor='royalblue',
        alpha=0.5,
        label= f'recorded (n={len(onboardTimestamps)})',
    )

    ax.axvline(
        queryLimits[0],
        color='darkorange',
        alpha=0.75,
        linewidth = 1.5,
        label = 'query start',
        clip_on = False,
    )

    ax.axvline(
        queryLimits[1], 
        color='darkorange',
        alpha=0.75,
        linewidth = 1.5,
        label = 'query end',
        clip_on = False,
    )

    if label_bars == True:
        plt.bar_label(
            serverBars,
            color='red',
            alpha=0.75,
        )
       
        plt.bar_label(
            onboardBars,
            color='royalblue',
            alpha=0.75,
        )

    dtFmt = mpl.dates.DateFormatter('%d%b %H:%M') # define the formatting
    plt.gca().xaxis.set_major_formatter(dtFmt) 
    plt.xticks(rotation = 90)

    ylims = np.round(ax.get_ylim()) #+ np.array([0,1])
    yticks = ax.get_yticks()
    ax.set_yticks(np.unique(np.round(yticks,0)))
    yminor_ticks = np.arange(0, ylims[1], 1)

    ax.set_xticks(allCallWindows, minor=True)
    ax.set_yticks(yminor_ticks, minor=True)

    # grid settings:
    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.2)

    ax.set_xlim(plotLimits)
    ax.set_ylim(ylims)
    # ax.legend(loc='upper right')
    ax.legend(
        loc='upper center', 
        bbox_to_anchor=(0.5, 1.35),
        ncol=4, 
        fancybox=True, 
        shadow=False,
    )
    ax.set_ylabel('messages per burst window')

    return fig, ax
    
# #%%

# startDate = datetime(2022,10,31,21,0,0)
# # startDate = datetime(2022,11,1,18,0,0)
# endDate   = datetime.utcnow()
# buoyIDs = ['005','068','073','067','062','058','060','018','011','002']
# # buoyIDs = ['068','062','058','060','011']

# burstInterval = 60 # minutes
# trim_to_query_limits = True
# for buoyID in buoyIDs:
#     print(buoyID)

#     create_telemetry_report(
#         buoyID, 
#         startDate,
#         endDate,
#         burstInterval,
#         trim_to_query_limits = trim_to_query_limits,
#     )

#%%
# inTimes = np.searchsorted(dateRange.tolist(), onboardTimestamps, side='left')

# [dateRange[i] for i in inTimes]
# inTimesServer = np.searchsorted(dateRange.tolist(), serverTimes, side='left')

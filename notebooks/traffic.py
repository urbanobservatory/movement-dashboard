import matplotlib
import pandas as pd
import numpy as np
import pickle
import urllib.request
import dateutil.parser
import dateutil.rrule
import dateutil.tz
import datetime
import warnings
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
import matplotlib.ticker as mtick
import math

warnings.filterwarnings('ignore')

matplotlib.rcParams.update({
    'font.size': 13,
    'timezone': 'Europe/London',
    'figure.max_open_warning': False
})

tzLocal = dateutil.tz.gettz('Europe/London')
dateToday = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()).replace(tzinfo=tzLocal)
dateBaselineEnd = datetime.datetime.strptime('2020-03-15T23:59:59Z', '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tzLocal)
plottableTypes = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
govChartStart = datetime.datetime.strptime('2020-03-01T00:00:00Z', '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tzLocal)
lastWeekStart = dateToday - pd.Timedelta(days=6)
lastWeekEnd = dateToday + pd.Timedelta(hours=24)

bankHolidays = [
    '10-04-2020',
    '13-04-2020',
    '08-05-2020',
    '25-05-2020',
    '31-08-2020'
]

def makeRelativeToBaseline(pdInput, maxMissing = 4, includeHours=list(range(0, 24))):  
    pdTrafficAnalysis = pdInput.copy() #.replace(0.0, np.nan)
    
    pdTrafficAnalysis.insert(0, 'Date', pdTrafficAnalysis.index.to_series().apply(lambda t: t.date()))
    pdTrafficAnalysis.insert(0, 'Day of week', pdTrafficAnalysis.index.to_series().apply(lambda t: t.strftime('%A')))
    pdTrafficAnalysis.insert(1, 'Time of day', pdTrafficAnalysis.index.to_series().apply(lambda t: t.strftime('%H:%M:%S')))
    pdTrafficAnalysis.insert(1, 'Hour of day', pdTrafficAnalysis.index.to_series().apply(lambda t: t.hour))

    # Take each day with complete data, and calculate a sum of vehicles per day
    # then convert it to an average per day of the week using the median
    # There are no peak hours on a weekend
    pdTrafficHoursSelected = pdTrafficAnalysis \
        [pdTrafficAnalysis['Hour of day'].apply(lambda hour: hour in includeHours) == True] \
        [pdTrafficAnalysis['Date'].apply(lambda date: len(includeHours) >= 20 or date.strftime('%d-%m-%Y') not in bankHolidays) == True] \
        [pdTrafficAnalysis['Day of week'].apply(lambda day: len(includeHours) >= 20 or day not in ['Saturday', 'Sunday']) == True] \
        .drop(columns=['Hour of day'])
    
    # What's the interval?
    dataInterval = pdTrafficHoursSelected.index.to_series().diff().quantile(0.01).seconds
    
    #print('Hours included %f' % (len(includeHours)/24 * 24))
    #print('Minimum points %u' % math.floor(len(includeHours)/24 * 24 * (3600 / dataInterval) - maxMissing / dataInterval))
    
    pdTrafficDaySum = pdTrafficHoursSelected[ : dateBaselineEnd] \
        .groupby(['Date', 'Day of week'], as_index=False) \
        .sum(min_count=math.floor(len(includeHours)/24 * 24 * (3600 / dataInterval) - maxMissing / dataInterval))
    pdTrafficDayOfWeekAverage = pdTrafficDaySum \
        .groupby(['Day of week'], as_index=False) \
        .median()
    pdTrafficDayOfWeekCount = pdTrafficDaySum \
        .groupby(['Day of week'], as_index=False) \
        .count()
    
    pdTrafficRecent = pdTrafficHoursSelected[govChartStart :] \
        .groupby(['Date', 'Day of week'], as_index=False) \
        .sum(min_count=math.floor(len(includeHours)/24 * 24 * (3600 / dataInterval) - maxMissing / dataInterval)) \
        .replace(0, np.nan)
    #print(pdTrafficRecent)
    
    # Normally minimum 90... (24 * 4 = 96)

    pdTrafficRecentRelativePc = pdTrafficRecent[pdTrafficRecent.select_dtypes(plottableTypes).columns]
    pdTrafficRecentRelativePc.index = pdTrafficRecent['Date']
    #pdTrafficRecentRelativePc.insert(0, 'Day of week', pdTrafficRecentRelativePc.index.to_series().apply(lambda t: t.strftime('%A')))

    def convertToPercentage(row):
        dayOfWeek = row.name.strftime('%A')
        dayOfWeekBaselineCount = pdTrafficDayOfWeekCount[pdTrafficDayOfWeekAverage['Day of week'] == dayOfWeek].iloc[:, 1:].values[0]
        dayOfWeekNormal = pdTrafficDayOfWeekAverage[pdTrafficDayOfWeekAverage['Day of week'] == dayOfWeek].iloc[:, 1:].values[0]
        return (row / dayOfWeekNormal * 100)

    pdTrafficRecentRelativePc = pdTrafficRecentRelativePc.apply(convertToPercentage, axis=1)

    # Output tables:
    #pdTrafficDayOfWeekAverage
    #pdTrafficRecentRelativePc
    
    return pdTrafficRecentRelativePc

def plotTraffic(pdTrafficRecentRelativePc, dfMedianPcSet, tsAdditionalDetail, fullLegend = False, normalLineAlpha=0.5):
    fig, ax = plt.subplots(1,1, figsize=(18,9), constrained_layout=True)

    ax.set_xlabel('Date')
    ax.set_ylim([0, 120])
    ax.set_ylabel('Percentage')
    ax.set_yticks(np.arange(0, 120, 10))

    # Median passed can be a single series or a dict of series with different times of the day etc.
    dfMedianPc = dfMedianPcSet['Median'] if type(dfMedianPcSet) is dict else dfMedianPcSet
    
    timeLocatorMajor = mdates.AutoDateLocator(minticks=15, maxticks=60)
    conciseZeroFormats = ['', '%Y', '%b', '%d-%b', '%H:%M', '%H:%M']
    conciseOffsetFormats = ['', '%Y', '%b-%Y', '%d-%b-%Y-%b', '%d-%b-%Y', '%d-%b-%Y %H:%M']
    ax.xaxis.set_tick_params(which='major')
    ax.xaxis.set_major_locator(timeLocatorMajor)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator=timeLocatorMajor, zero_formats=conciseZeroFormats, offset_formats=conciseOffsetFormats))

    ax.grid(axis='y', linestyle='--', alpha=0.5)

    tsAnnotationOffset = 1
    annotationColours = iter(plt.get_cmap('Dark2').colors + plt.get_cmap('Set1').colors)
    tsAnnotationOffsetAlternator = -8

    for ts in reversed(sorted(list(pdTrafficRecentRelativePc.columns))):
        dfTs = pdTrafficRecentRelativePc[ts]
        dfTs.index = dfTs.index.map(lambda d: datetime.datetime.combine(d, datetime.time.min).replace(tzinfo=tzLocal))
        dfTs = dfTs[((dfTs < 160) & (dfTs > 10)) | (dfTs.isnull())] # Sanity limits :-)

        if ts in tsAdditionalDetail.keys():
            seriesColour = next(annotationColours)

            if fullLegend == True:
                ax.plot(dfTs, color=seriesColour, alpha=0.8, linewidth=1.5, label=tsAdditionalDetail[ts], zorder=2)
            else:
                ax.plot(dfTs, color=seriesColour, alpha=0.8, linewidth=1.5)
                
                arrowDay = dateToday - pd.Timedelta(days=tsAnnotationOffset)

                arrowPointsAt = list(dfTs[dfTs.index == arrowDay].to_dict().values())
                arrowPointsAt = None if len(arrowPointsAt) <= 0 else arrowPointsAt[0]
                arrowMedian = list(dfMedianPc[dfMedianPc.index == arrowDay].to_dict().values())
                arrowMedian = None if len(arrowMedian) <= 0 else arrowMedian[0]

                shiftAttempt = 0
                while (arrowPointsAt is None or arrowMedian is None or abs(arrowPointsAt - arrowMedian) < 3.5) and shiftAttempt < 15:
                    tsAnnotationOffset = tsAnnotationOffset + 1
                    shiftAttempt = shiftAttempt + 1
                    arrowDay = dateToday - pd.Timedelta(days=tsAnnotationOffset)
                    arrowPointsAt = list(dfTs[dfTs.index == arrowDay].to_dict().values())
                    arrowPointsAt = None if len(arrowPointsAt) <= 0 else arrowPointsAt[0]
                    arrowMedian = list(dfMedianPc[dfMedianPc.index == arrowDay].to_dict().values())
                    arrowMedian = None if len(arrowMedian) <= 0 else arrowMedian[0]

                tsAnnotationOffsetAlternator = -tsAnnotationOffsetAlternator

                if arrowPointsAt is not None and arrowMedian is not None:
                    ax.annotate(tsAdditionalDetail[ts],
                        xy=(arrowDay, arrowPointsAt),
                        xycoords='data',
                        xytext=(arrowDay, max(12.5, arrowPointsAt + ((+20 + tsAnnotationOffsetAlternator) if arrowPointsAt > arrowMedian else (-20 + tsAnnotationOffsetAlternator)))),
                        textcoords='data',
                        arrowprops=dict(arrowstyle="->, head_length=0.5, head_width=0.5", connectionstyle="angle,angleA=90,angleB=0"),
                        horizontalalignment='center',
                        verticalalignment='top',
                        fontsize=11,
                        path_effects=[pe.withStroke(linewidth=4, foreground='#ffffffa0')]
                    )
                    ax.annotate('●',
                        xy=(arrowDay, max(7, arrowPointsAt + ((+25 + tsAnnotationOffsetAlternator) if arrowPointsAt > arrowMedian else (-26 + tsAnnotationOffsetAlternator)))),
                        xycoords='data',
                        xytext=(arrowDay, max(7, arrowPointsAt + ((+25 + tsAnnotationOffsetAlternator) if arrowPointsAt > arrowMedian else (-26 + tsAnnotationOffsetAlternator)))),
                        textcoords='data',
                        horizontalalignment='center',
                        verticalalignment='top',
                        fontsize=14,
                        color=seriesColour
                    )
                    tsAnnotationOffset = tsAnnotationOffset + round((dateToday.date() - govChartStart.date()).days / 10)

        else:
            ax.plot(dfTs, color='#909090', alpha=normalLineAlpha, linewidth=0.35)

    for date in dfMedianPc.index:
        if date.strftime('%A') in ['Saturday', 'Sunday'] or date.strftime('%d-%m-%Y') in bankHolidays:
            #print(date)
            ax.axvspan(
                date - pd.Timedelta(days=0.5),
                date + pd.Timedelta(days=0.5),
                alpha=0.15 if date.strftime('%A') in ['Saturday', 'Sunday'] else 0.08,
                color='#707070',
                zorder=3
            )

    if type(dfMedianPcSet) is dict:
        for name, series in dfMedianPcSet.items():
            if name == 'Median':
                ax.plot(dfMedianPc, color='#f64a8a', linewidth=2.0, marker='s', markersize=8, label='Median', zorder=10)
            else:
                if 'Inter' in name:
                    marker='v'
                    linestyle='dashed'
                elif 'Peak' in name:
                    marker='^'
                    linestyle='dashdot'
                else:
                    marker = 'o'
                ax.plot(series, color='#233067', linewidth=1, marker=marker, linestyle=linestyle, markersize=7, alpha=0.75, label=name, zorder=5)
    else:
        ax.plot(dfMedianPc, color='#f64a8a', linewidth=2.0, marker='s', markersize=8, label='Median', zorder=10)
        
    plt.xticks(ha='center')
    plt.legend(loc='upper right', ncol=1 if fullLegend == False else 3)
    
    return [plt, fig, ax]

def generateDailyProfiles(sourceData, interval = 60 * 8):
    timezoneOffset = ((60 - np.min(sourceData.index).time().minute) * 60) if np.min(sourceData.index).time().minute > 0 else 0
    
    pdTrafficPreCV = sourceData[sourceData.index < dateBaselineEnd]
    pdTrafficPostCV = sourceData[(sourceData.index >= dateBaselineEnd) & (sourceData.index < np.max(sourceData.index) - pd.Timedelta(seconds=interval))]
    #pdTrafficPostCV

    pdTrafficPreCV.insert(0, 'Day of week', pdTrafficPreCV.index.to_series().apply(lambda t: t.strftime('%A')))
    pdTrafficPreCV.insert(0, 'Time of day', pdTrafficPreCV.index.to_series().apply(lambda t: (t if bool(t.dst()) == False else (t - pd.Timedelta(seconds=timezoneOffset))).strftime('%H:%M:%S')))
    pdTrafficPreCVAverage = pdTrafficPreCV \
        .groupby(['Day of week', 'Time of day'], as_index=False) \
        .median()
    pdTrafficPreCVLowerQuantile = pdTrafficPreCV \
        .groupby(['Day of week', 'Time of day'], as_index=False) \
        .quantile(0.10)
    pdTrafficPreCVUpperQuantile = pdTrafficPreCV \
        .groupby(['Day of week', 'Time of day'], as_index=False) \
        .quantile(0.90)

    pdTrafficPostCV.insert(0, 'Day of week', pdTrafficPostCV.index.to_series().apply(lambda t: t.strftime('%A')))
    pdTrafficPostCV.insert(0, 'Time of day', pdTrafficPostCV.index.to_series().apply(lambda t: (t if bool(t.dst()) == False else (t - pd.Timedelta(seconds=timezoneOffset))).strftime('%H:%M:%S')))

    # Give the proper order to the days in the last week
    weekDaysOrder = list(map(lambda daysAgo: (dateToday - pd.Timedelta(days=6) + pd.Timedelta(days=daysAgo)).strftime('%A'), list(range(0, 7))))
    pdTrafficPreCVAverage.insert(0, 'Days into last week', pdTrafficPreCVAverage['Day of week'].apply(lambda day: weekDaysOrder.index(day)))
    pdTrafficPreCVLowerQuantile.insert(0, 'Days into last week', pdTrafficPreCVAverage['Day of week'].apply(lambda day: weekDaysOrder.index(day)))
    pdTrafficPreCVUpperQuantile.insert(0, 'Days into last week', pdTrafficPreCVAverage['Day of week'].apply(lambda day: weekDaysOrder.index(day)))

    pdTrafficPreCVAverage.sort_values(['Days into last week', 'Time of day'], inplace=True)
    pdTrafficPreCVLowerQuantile.sort_values(['Days into last week', 'Time of day'], inplace=True)
    pdTrafficPreCVUpperQuantile.sort_values(['Days into last week', 'Time of day'], inplace=True)
    pdTrafficPreCVAverage = pdTrafficPreCVAverage.reset_index(drop=True)
    pdTrafficPreCVLowerQuantile = pdTrafficPreCVLowerQuantile.reset_index(drop=True)
    pdTrafficPreCVUpperQuantile = pdTrafficPreCVUpperQuantile.reset_index(drop=True)
    
    pdTrafficPreCVAverage.index = pdTrafficPreCVAverage.index.to_series().apply(
      lambda rowId: lastWeekStart + pd.Timedelta(seconds=rowId * interval)
    )
    pdTrafficPreCVLowerQuantile.index = pdTrafficPreCVLowerQuantile.index.to_series().apply(
      lambda rowId: lastWeekStart + pd.Timedelta(seconds=rowId * interval)
    )
    pdTrafficPreCVUpperQuantile.index = pdTrafficPreCVUpperQuantile.index.to_series().apply(
      lambda rowId: lastWeekStart + pd.Timedelta(seconds=rowId * interval)
    )
    
    baselineStart = np.min(pdTrafficPreCV.index)
    baselineEnd = np.max(pdTrafficPreCV.index)
    baselineLength = (baselineEnd - baselineStart).days
    
    return {
        'profile': {
            'average': pdTrafficPreCVAverage,
            'lq': pdTrafficPreCVLowerQuantile,
            'uq': pdTrafficPreCVUpperQuantile,
            'length': baselineLength,
            'start': baselineStart,
            'end': baselineEnd
        },
        'recent': pdTrafficPostCV
    }

def plotDailyProfile(dp, maxChange=0.25, minBaselineDays=90, title=None):
    fig, axs = plt.subplots(
        4, 2,
        figsize = (15, 6 * 4),
        constrained_layout=True
    )

    for idx, dayOfWeek in enumerate(['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']):
        #dayOfWeek = 'Saturday'

        ax = axs[math.floor(idx / 2), idx % 2]

        # Normalise the data against the normal maximum for this day of the week...
        normalisedVolume = dp['profile']['average'][dp['profile']['average']['Day of week'] == dayOfWeek]['Total'].max(axis=0)

        medianPlot = ax.plot(dp['profile']['average'][dp['profile']['average']['Day of week'] == dayOfWeek]['Total'] / normalisedVolume, label='%s average (Jul 2019 -)' % dayOfWeek, color='#233067')    
        
        if dp['profile']['length'] < minBaselineDays:
            percentileLegend = None
        else:
            percentileLegend = ax.fill_between(
                dp['profile']['lq'][dp['profile']['lq']['Day of week'] == dayOfWeek]['Total'].index,
                dp['profile']['lq'][dp['profile']['lq']['Day of week'] == dayOfWeek]['Total'] / normalisedVolume,
                dp['profile']['uq'][dp['profile']['uq']['Day of week'] == dayOfWeek]['Total'] / normalisedVolume,
                color='#233067',
                linewidth=0,
                alpha=0.1,
                label='15-85%%ile for %s' % dayOfWeek
            )

        plotWeeks = 4
        plotAlpha = 1.0
        plotLegends = []

        for weeksAgo in range(0, plotWeeks):
            postCVSingleWeek = dp['recent'][
                (dp['recent'].index >= lastWeekStart - pd.Timedelta(days = 7 * weeksAgo)) &
                (dp['recent'].index < lastWeekEnd - pd.Timedelta(days = 7 * weeksAgo))
            ].shift(
                periods=7 * weeksAgo,
                freq='d'
            )
            
            # Normalise and set some limits on crazy changes (usually comms outages)
            pdWeekNormalised = postCVSingleWeek[postCVSingleWeek['Day of week'] == dayOfWeek]['Total'] / normalisedVolume
            pdWeekNormalised = pdWeekNormalised.mask(abs(pdWeekNormalised.diff(periods=-1)) > maxChange)
            
            plotLegends.append(ax.plot(
                pdWeekNormalised,
                label=None if plotAlpha < 1.0 else '%s for last %u weeks' % (dayOfWeek, plotWeeks),
                linestyle='solid' if plotAlpha == 1.0 else '--',
                dashes=(2, weeksAgo * 2),
                color='#f64a8a',
                alpha=plotAlpha
            )[0])
            plotAlpha = plotAlpha - 0.25


        timeLocatorMajor = mdates.AutoDateLocator(minticks=6, maxticks=10)
        conciseZeroFormats = ['', '%Y', '%b', '%d-%b', '%H:%M', '%H:%M']
        conciseOffsetFormats = ['', '%Y', '%b-%Y', '%d-%b-%Y', '%d-%b-%Y', '%d-%b-%Y %H:%M']
        ax.xaxis.set_tick_params(which='major')
        ax.xaxis.set_major_locator(timeLocatorMajor)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator=timeLocatorMajor, zero_formats=conciseZeroFormats, offset_formats=conciseOffsetFormats, tz=tzLocal))

        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        ax.set_facecolor('white')
        ax.set_clip_on(False)

        ax.set_title(dayOfWeek)
        ax.set_ylabel('Normalised vehicle counts')

    # Hide the final plot...
    ax = axs[3][1]
    ax.axis('off')

    ax.legend(
        [
            medianPlot[0],
            plt.Line2D([0],[0],color="w") if percentileLegend is None else percentileLegend,
            plt.Line2D([0],[0],color="w"),
            plt.Line2D([0],[0],color="w")
        ] + plotLegends,
        [
            'Median profile for day of week',
            '10-90%ile for day of week' if percentileLegend is not None else 'Not enough data for quantile bounds',
            'Baseline %s - %s' % (dp['profile']['start'].strftime('%b %Y'), dp['profile']['end'].strftime('%b %Y')),
            ''
        ] + [
            'Vehicles observed in the last week',
            '    One week ago',
            '    Two weeks ago',
            '    Three weeks ago'
        ],
        loc='upper left',
        ncol=1
    )

    # plt.legend(ncol=1, loc='upper left', fontsize=10)
    # plt.tight_layout()
    
    if title is not None:
        fig.suptitle(title)
        
    plt.show()
    
    return fig, axs

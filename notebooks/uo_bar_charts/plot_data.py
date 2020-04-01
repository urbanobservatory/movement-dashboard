import json
import os
import sys
import pandas as pd
import smopy
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as mpatches
import datetime
from collections import OrderedDict
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__

PATTERNS = ['ooo','+++', 'xxx', '\\\\', '...']

def sensor_location(bar_chart,sensor_name,pretty_name):

    map_img_path = '{folder}/{sensor_name}.png'.format(
        folder=bar_chart.sensor_map_folder,
        sensor_name=sensor_name
    )

    if not os.path.exists(map_img_path):
        fig, ax2 = plt.subplots(figsize=(500/300, 500/300), dpi=300)
        geojson = json.load(open('{geojson_folder}/{sensor_name}.json'.format(
            sensor_name=sensor_name,
            geojson_folder=bar_chart.geojson_folder,
        )))
        blockPrint()
        mini_map = smopy.Map(
            (
                geojson['coordinates'][1] - 0.00001,
                geojson['coordinates'][0] - 0.00001,
                geojson['coordinates'][1] + 0.00001,
                geojson['coordinates'][0] + 0.00001
            ),
            z=40)

        enablePrint()
        x, y = mini_map.to_pixels(geojson['coordinates'][1], geojson['coordinates'][0])
        ax = mini_map.show_mpl(ax2)
        ax.plot(x, y, 'or', ms=5, mew=1);
        plt.xticks([])
        plt.yticks([])
        plt.grid(False)
        plt.xlim(0, mini_map.w)
        plt.ylim(mini_map.h, 0)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(map_img_path)
    return map_img_path


def plot_data(bar_chart,rename_function):
    mpl.style.use('seaborn')
    sensor_json = json.load(open(bar_chart.sensor_json))

    for db_name in sensor_json['sensors']:
        pretty_name = rename_function(db_name)





        df = pd.read_pickle('{data_folder}/{sensor_name}.tar.gz'.format(
                sensor_name=db_name,
                data_folder=bar_chart.data_folder
            ))
        df.index = pd.to_datetime(df['Timestamp'])
        if df.empty:
            continue

        minimap = sensor_location(bar_chart, db_name,pretty_name)

        df['dayofweek'] = df.index.weekday

        max_monday = pd.to_datetime(df[df.index.weekday == 0]['Timestamp']).max()
        last_monday = datetime.datetime(max_monday.year,max_monday.month,max_monday.day)

        df['week'] = df.index.week
        bars = OrderedDict()
        for week, week_frame in df.groupby('week'):
            day_values = OrderedDict(zip(range(7), [None] * 7))
            for dayofweek, day_frame in week_frame.groupby('dayofweek'):
                day_values[dayofweek] = [0] * 5
                day_values[dayofweek][0] = day_frame[day_frame.index.time < datetime.time(7, 0)]['Value'].sum()
                day_values[dayofweek][1] = day_frame[
                    (day_frame.index.time < datetime.time(10, 0)) & (day_frame.index.time >= datetime.time(7, 0))][
                    'Value'].sum()
                day_values[dayofweek][2] = day_frame[
                    (day_frame.index.time >= datetime.time(10, 0)) & (day_frame.index.time < datetime.time(16, 0))][
                    'Value'].sum()
                day_values[dayofweek][3] = day_frame[
                    (day_frame.index.time >= datetime.time(16, 0)) & (day_frame.index.time < datetime.time(19, 0))][
                    'Value'].sum()
                day_values[dayofweek][4] = day_frame[
                    day_frame.index.time >= datetime.time(19, 0)][
                    'Value'].sum()
            bars[week] = list(day_values.values())
        # set width of bar
        barWidth = 0.2
        my_dpi = 300
        fig, ax1 = plt.subplots(figsize=(1600/my_dpi, 1600/my_dpi), dpi=my_dpi)
        for i, (week_num, sub_bars) in enumerate(bars.items()):
            for j, stack in enumerate(sub_bars):
                if stack == None:
                    stack = [0, ] * 5
                for k, bar in enumerate(stack):
                    ax1.bar(j + barWidth * i,
                            bar,
                            bottom=sum(stack[:k]),
                            width=barWidth,
                            color='white',
                            edgecolor='C' + str(i),
                            hatch=PATTERNS[k],
                            linewidth=1
                            )

        # Add xticks on the middle of the group bars
        ax1.set_ylabel('Vehicle Count', fontweight='bold')
        ax1.set_xlabel('Day of the Week', fontweight='bold')

        ax1.set_xticks([r + (barWidth * 1.5) for r in range(7)])
        ax1.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])

        # Create legend & Show graphic
        legend_items = []
        for i in range(4):
            label = 'Week of ' + (last_monday - datetime.timedelta(weeks=3 - i)).strftime('%a %e %B')
            legend_items.append(mpatches.Patch(facecolor='white', edgecolor='C' + str(i), linewidth=1, label=label))

        hatch_times = [
            datetime.datetime(1, 1, 1, 0, 0),
            datetime.datetime(1, 1, 1, 7, 0),
            datetime.datetime(1, 1, 1, 10, 0),
            datetime.datetime(1, 1, 1, 16, 0),
            datetime.datetime(1, 1, 1, 19, 0),
            datetime.datetime(1, 1, 1, 0, 0),
        ]
        hatch_labels = [
            hatch_times[0].strftime('%R') + ' - ' + hatch_times[1].strftime('%R'),
            hatch_times[1].strftime('%R') + ' - ' + hatch_times[2].strftime('%R'),
            hatch_times[2].strftime('%R') + ' - ' + hatch_times[3].strftime('%R'),
            hatch_times[3].strftime('%R') + ' - ' + hatch_times[4].strftime('%R'),
            hatch_times[4].strftime('%R') + ' - ' + hatch_times[5].strftime('%R'),
        ]
        for i in range(5):
            label = hatch_labels[i]

            legend_items.append(
                mpatches.Patch(facecolor='white', edgecolor='black', hatch=PATTERNS[i], linewidth=1, label=label))

        ax1.legend(handles=legend_items,prop={'size': 6})

        fig.tight_layout()
       
        fig_path = '{data_folder}/{sensor_name}.png'.format(
            sensor_name=db_name,
            data_folder=bar_chart.plots_folder
        )
        plt.savefig(fig_path)

        yield pretty_name,minimap,fig_path

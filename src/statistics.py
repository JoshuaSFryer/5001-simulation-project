import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys

TIME_STEP = 10  # seconds
SIM_DURATION = 1000


def load_file(path):
    return pd.read_csv(path)


def average_value(df, val_name):
    total = df.iloc[-1][val_name]
    return total / SIM_DURATION


def products_over_time(df):
    prod_1 = value_over_time('total_P1', integer=True)
    prod_2 = value_over_time('total_P2', integer=True)
    prod_3 = value_over_time('total_P3', integer=True)
    return (prod_1, prod_2, prod_3)


def value_over_time(val_name, integer=False):
    vals = list()
    curr_time = 0.0
    while curr_time < SIM_DURATION:
        curr_rows = df.loc[(df['time'] > curr_time) & (
            df['time'] <= curr_time + TIME_STEP)]
        if not curr_rows.empty:
            last_count = curr_rows.iloc[-1][val_name]
            first_count = curr_rows.iloc[0][val_name]
            difference = last_count - first_count
            if integer:
                difference = int(difference)
            vals.append(difference)
        else:
            vals.append(0)
        
        curr_time = curr_time + TIME_STEP
    return vals


def plot_product(prod):
    x = np.linspace(0, SIM_DURATION, int(SIM_DURATION/TIME_STEP))
    y = prod
    plt.plot(x, y)
    plt.show()


if __name__ == '__main__':
    log_dir = sys.argv[1]
    csv_dir = os.path.join(log_dir, 'csv')

    p1_means = list()
    p2_means = list()
    p3_means = list()

    IN1_times = list()
    IN2_times = list()

    log_files = os.listdir(csv_dir)
    for filename in log_files:
        print(f'Processing {filename}...')
        df = load_file(os.path.join(csv_dir, filename))

        p1, p2, p3 = products_over_time(df)
        IN1 = df.iloc[-1]['blocked_IN1']
        IN2 = df.iloc[-1]['blocked_IN2']

        p1_means.append(p1)
        p2_means.append(p2)
        p3_means.append(p3)
        IN1_times.append(IN1)
        IN2_times.append(IN2)

    products = (p1_means, p2_means, p3_means)
    names = ('P1', 'P2', 'P3')
    for product, name in zip(products, names):
        path = os.path.join(log_dir, name + '.csv')
        with open(path, 'w') as f:
            for row in product:
                for num in row:
                    f.write(str(num) + ',')
                f.write('\n')

    inspectors = (IN1_times, IN2_times)
    names = ('IN1', 'IN2')
    for list, name in zip(inspectors, names):
        path = os.path.join(log_dir, name + '.csv')
        with open(path, 'w') as f:
            for time in list:
                f.write(str(time) + ',')
    
    print('Done.')
        

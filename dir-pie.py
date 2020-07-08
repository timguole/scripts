#!/usr/bin/python3

import matplotlib.pyplot as plt
import subprocess

def show_dir_pie(path):
    '''
    Display the output of "du -s path/*" as a pie chart.
        '''
    # quote {path} to avoid shell injection
    cp = subprocess.run(f'du -s "{path}"*', shell=True, \
            capture_output=True)
    data = [e.split('\t') for e in \
           cp.stdout.decode(encoding='UTF-8').splitlines()]
    x = []
    labels = []
    for i in data:
        x.append(i[0])
        labels.append(i[1])
    plt.pie(x, labels=labels, autopct='%1.1f%%')
    plt.show()


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        print('Usage: {} <dir>'.format(sys.argv[0]))
        exit(1)
    show_dir_pie(sys.argv[1])

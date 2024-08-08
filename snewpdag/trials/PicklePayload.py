"""
Generate a signal from a pickle file, and pass it into dag specified by csv file

This should be a stand-alone program streaming to stdout.
"""
import sys, argparse, pickle

from snewpdag.dag.app import inject, csv_eval

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('dag_file', type=argparse.FileType('r'), help='csv file describing DAG')
    parser.add_argument('pickle_file', type=argparse.FileType('rb'), help='Pickle file containing payload')
    parser.add_argument('-i', '--inject-point', type=str, help='Node to inject payload at')
    args = parser.parse_args()

    with args.dag_file as dag_file:
        nodespecs = csv_eval(dag_file)

    with args.pickle_file as pickle_file:
        payload_obj = pickle.load(pickle_file)

    try:
        payload_obj['name'] = args.inject_point
    except AttributeError:
        pass

    inject({}, payload_obj, nodespecs)

if __name__ == '__main__':
    run()


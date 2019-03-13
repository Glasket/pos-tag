# Python 3.7.2
#
# Christian W Sigmon
# 3/12/2019 CMSC-416
#
# Problem: Tagged text must be scored based on a key file.
#
# Example: python tagger.py pos-train.txt pos-test.txt
#           Output is Accuracy and a list of expected tags with predicted counts following them.
#
# Usage: scorer.py [-h] test key
#        positional arguments:
#           test        a file containing tagged text to be compared to the key
#           key         a file containing tagged text to be used as a key
#        
#        optional arguments:
#           -h, --help  show this help message and exit
#
# Algorithm: Files are parsed, and broken into tags. Tags are compared to one another in order to build
#               the confusion matrix and tally the total correct tags. The results are then printed to STDOUT
#

import re
import argparse

def compare(test, key):
    """Compares the test tag to the key tag for correctness"""
    correct = 0
    matrix = dict()
    for index, tag in enumerate(test):
        if re.search('|', key[index]):  # Remove extra tags following |
            key[index] = key[index].split('|')[0]

        if key[index] not in matrix.keys():         # Create matrix row
            matrix[key[index]] = dict()

        if tag not in matrix[key[index]].keys():    # Create matrix column
            matrix[key[index]][tag] = 1
        else:
            matrix[key[index]][tag] += 1

        if tag == key[index]:
            correct += 1    # Total correct counter
    return (correct, matrix)

def get_tags(text):
    """Split word-tag combinations to get the tags"""
    tags = []
    for word in text:
        tags.append(re.split(r'(?<!\\)[\/]', word)[1])
    return tags

def read_file(file_name):
    """Reads in file as a blob of text"""
    with open(file_name, 'r') as file_:
        in_text = file_.read().replace(r'\n', ' ').replace('[', ' ').replace(']', ' ')
    return in_text

def main():
    """Main"""
    # Defining arguments for CLI
    parser = argparse.ArgumentParser(description='Scores a given tagged text file based on a given key file.')
    parser.add_argument('test', nargs=1, metavar='test', help='a file containing tagged text to be compared to the key')
    parser.add_argument('key', nargs=1, metavar='key', help='a file containing tagged text to be used as a key')
    args = parser.parse_args()

    # File read
    test_text = read_file(args.test[0])
    key_text = read_file(args.key[0])

    # Calculation
    results = compare(get_tags(test_text.split()), get_tags(key_text.split()))
    correct = results[0]
    matrix = results[1]

    print('Accuracy: ' + str(correct/len(test_text.split())))

    # Print 'matrix'
    for key in matrix.keys():
        print(key + ':', end=' ')
        for pred, num in matrix[key].items():
            print(pred + ':' + str(num), end=' ')
        print('\n')

if __name__ == "__main__":
    main()
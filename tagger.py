# Python 3.7.2
#
# Christian W Sigmon
# 3/12/2019 CMSC-416
#
# Note: I misread the assignment and implemented the HMM tagger before realizing it wasn't necessary.
#           I implemented both the baseline and rule-based taggers afterwards, however the HMM is still
#           the main tagger for the program.
#
# Problem: Text must be correctly assigned a Part-of-Speech based on a training set.
#
# Example: python tagger.py pos-train.txt pos-test.txt
#           Output is tagged sentences
#
# Usage: tagger.py [-h] [-b] train test
#        positional arguments:
#           train           a file containing pre-tagged text, which is used to train
#                           the tagger
#           test            a file containing untagged text to be tagged by the tagger
#
#        optional arguments:
#           -h, --help      show this help message and exit
#           -b, --baseline  makes the tagger use the most-likely-tag baseline (overrides 
#                       rule-based)
#           -r, --rules     makes the tagger use the rule-based tagger
#
# Algorithm: Files are parsed, sentences are then generated from the input text and broken into arrays.
#               The sentence arrays are then processed by the tagger. The tagger uses either a most-likely-tag (baseline),
#               rule-based, or HMM tagger to determine the proper tags. Once the tags are determined, they are joined with
#               the words of the sentence to form a tagged sentence which is printed to STDOUT.
#
# Addenda:
#   Accuracy:
#       Baseline:   77.26%
#       Rule-Based: 77.70%
#       HMM:        86.20%
#
#   Rules:
#       PRP followed by VBD is prioritized
#       TO followed by VB is prioritized
#       POS followed by either NN or NNS is prioritized
#       If IN is an option when WDT is selected, swap to IN
#

import re
import argparse
import sys

def rule_tag(sentence, freq_tables):
    s = ' '
    tagged_sentence = []
    tag = ''
    previous_tag = '<start>'
    for word in [s for s in sentence if not re.match(r'[\[\]]', s)]:
        score = 0
        regex = re.escape(word) + r'\/'     # Regex for matching word in freq table
        for tag_set in [t for t in freq_tables[0].keys() if re.search(regex, t)]:   # For every possible tag
            temp_tag = re.split(r'(?<!\\)[\/]', tag_set)[1]
            # Rules
            if previous_tag == 'PRP' and temp_tag == 'VBD':
                score = 1
                tag = temp_tag
            if previous_tag == 'TO' and temp_tag == 'VB':
                score = 1
                tag = temp_tag
            elif previous_tag == 'POS' and (temp_tag == 'NN' or temp_tag == 'NNS'):
                score = 1
                tag = temp_tag
            elif freq_tables[0][tag_set] > score:
                tag = temp_tag
                score = freq_tables[0][tag_set]
        if not tag:
            tag = 'NN' # Unknown words get tagged with NN
        if word + '/IN' in [t for t in freq_tables[0].keys() if re.search(regex, t)] and tag == 'WDT':
            tag = 'IN'
        previous_tag = tag
        tagged_sentence.append(word + '/' + tag)
    print(s.join(tagged_sentence))


def baseline_tag(sentence, freq_tables):
    """Baseline tagging algorithm"""
    s = ' '
    tagged_sentence = []
    tag = ''
    for word in [s for s in sentence if not re.match(r'[\[\]]', s)]:
        score = 0
        regex = re.escape(word) + r'\/'     # Regex for matching word in freq table
        for tag_set in [t for t in freq_tables[0].keys() if re.search(regex, t)]:   # For every possible tag
            if freq_tables[0][tag_set] > score:
                score = freq_tables[0][tag_set]
                tag = re.split(r'(?<!\\)[\/]', tag_set)[1]  # Split tag from set
        if not tag:
            tag = 'NN' # Unknown words get tagged with NN     
        tagged_sentence.append(word + '/' + tag)
    print(s.join(tagged_sentence))

def tagging(freq_tables, sentence_combos, sentence):
    """Tagging algorithm for a single sentence"""
    best = dict()   # argmax holder
    path = dict()   # Path that leads back through best tags
    for index in range(len(sentence_combos)):
        if index != 0:  # If not the first word
            for combo in sentence_combos[index]:
                tag = re.split(r'(?<!\\)[\/]', combo)[1]    # Split the tag from the word-tag combo
                key = str(index) + ' ' + tag                # Create the new key for best and path
                best[key] = 0                               # Init best to 0
                #Iterate through previous tags
                for prev_tag in [s for s in best.keys() if re.search(str(index-1), s)]:
                    prev_tag = prev_tag.split()[1]  # Split previous tag off of the prior best key
                    try:
                        score = best[str(index-1) + ' ' + prev_tag] * freq_tables[1][tag + '/' + prev_tag] * freq_tables[0][combo]
                    except:
                        # If a tag-tag combination has never happened before then replace tag-tag freq with 1/prev_freq
                        score = (1 / freq_tables[2][prev_tag]) * best[str(index-1) + ' ' + prev_tag] * freq_tables[0][combo]
                    if score > best[key]:                               # If score is greater than the current best for this tag, replace and change path
                        best[key] = score
                        path[key] = str(index-1) + ' ' + prev_tag
        else:   # If first word
            for combo in sentence_combos[index]:
                tag = re.split(r'(?<!\\)[\/]', combo)[1]
                key = str(index) + ' ' + tag
                try:
                    best[key] = freq_tables[1][tag + '/<start>'] * freq_tables[0][combo]
                except:
                    best[key] = 1 / freq_tables[2]['<start>'] * freq_tables[0][combo]
    # Begin to find the tags
    tags = ['.']
    node = path[str(len(sentence_combos)-1) + ' .'] # Start at the end
    while node.split()[0] != '0':                   # Iterate through until node is the first word
        tags.append(node.split()[1])                # Append the pathed tag to the tags list
        node = path[node]                           # Set node the next node in the path
    tags.append(node.split()[1])                    # Get the first tag
    tags.reverse()                                  # Reverse tag list so it reads 0 - i
    s = ' '
    tagged_sentence = []
    for i, word in enumerate([s for s in sentence if not re.match(r'[\[\]]', s)]):
        tagged_sentence.append(word + '/' + tags[i])    # Combine words with tags and add to sentence list
    print(s.join(tagged_sentence))                      # Print the tagged sentence

def tag_file(sentences, freq_tables):
    """Function that handles passing to the tagging algorithm"""
    for sentence in sentences:
        sentence_combos = []
        for word in sentence:
            if not re.match(r'[\[\]]', word):                   # Avoid using the [] 'words'
                regex = r'(?:^|\s)' + re.escape(word) + r'\/'   # Regex for finding words in the table word-tag table
                tag_combos = [s for s in freq_tables[0].keys() if re.search(regex, s)]
                # If the word is new, then an entry is created and the word is tagged with NN
                if not tag_combos:
                    freq_tables[0][word + '/NN'] = 1 / freq_tables[2]['NN']
                    tag_combos = [word + '/NN']
                sentence_combos.append(tag_combos)  # Sentence combos is an array of the arrays of possible word-tag combinations
        tagging(freq_tables, sentence_combos, sentence)

def generate_rel_freq_tables(tag_f, combo):
    """Changes frequency tables to relative frequency tables"""
    for k, v in combo.items():
        tag = re.split(r'(?<!\\)[\/]', k)[1] # Splitting tag for use as dict() key
        combo[k] = v / tag_f[tag]            # Conversion to relative frequency
    return combo

def generate_freq_tables(training_text):
    """Parses the training text and builds frequency tables"""

    tag_freq = dict()           # freq_tables[2]
    word_tag_freq = dict()      # freq_tables[0]
    tag_tag_freq = dict()       # freq_tables[1]

    previous_tag = '<start>'    # First tag is always a <start>
    tag_freq['<start>'] = 0

    tag_sets = training_text.split()
    for tagged_word in tag_sets:
        if not re.match(r'[\[\]]', tagged_word):
            tag_set = re.split(r'(?<!\\)[\/]', tagged_word) # Split on / (but not \/) to retrieve word and tag
            if '|' in tag_set[1]:
                tag_set[1] = tag_set[1].split('|')[0] # Remove alternative tags

            # Pure tag frequency
            if tag_set[1] in tag_freq:
                tag_freq[tag_set[1]] += 1
            else:
                tag_freq[tag_set[1]] = 1

            # Word-Tag Combination frequency
            word_tag = tag_set[0] + '/' + tag_set[1]
            if word_tag in word_tag_freq:
                word_tag_freq[word_tag] += 1
            else:
                word_tag_freq[word_tag] = 1

            # Tag followed by previous tag frequency
            tag_tag = tag_set[1] + '/' + previous_tag
            if tag_tag in tag_tag_freq:
                tag_tag_freq[tag_tag] += 1
            else:
                tag_tag_freq[tag_tag] = 1

            # Count start tags
            if previous_tag == '<start>':
                tag_freq[previous_tag] += 1

            # Setting up previous_tag for the tag_tag dict
            if re.match(r'[\.\!\?]+', tag_set[0]):
                previous_tag = '<start>'    # If the tag is a ., !, or ? then the prev tag will be set to <start>
            else:
                previous_tag = tag_set[1]

    # Convert to relative frequency
    word_tag_freq = generate_rel_freq_tables(tag_freq, word_tag_freq)
    tag_tag_freq = generate_rel_freq_tables(tag_freq, tag_tag_freq)

    return (word_tag_freq, tag_tag_freq, tag_freq)

def get_sentences(text):
    """Breaks input text into sentences"""
    sentences = []
    sentence_strings = re.findall(r'.*?(?<!\w|\d|\.)[\.\!\?](?!\d+|\.)', text) # Break sentences wherever a ., !, or ? is, except when followed by a number
    for sentence in sentence_strings:
        words = sentence.split()    # Split the sentence into words
        sentences.append(words)     # Make an array of the sentences as arrays of words
    return sentences

def read_file(file_name):
    """Reads in file as a blob of text"""
    with open(file_name, 'r') as file_:
        in_text = file_.read().replace('\n', ' ')
    return in_text

def main():
    """Main"""
    # Defining arguments for CLI
    parser = argparse.ArgumentParser(description='Tags a given test file based on training received from a given training file.')
    parser.add_argument('-b', '--baseline', action='store_true', help='makes the tagger use the most-likely-tag baseline (overrides rule-based)')
    parser.add_argument('-r', '--rules', action='store_true', help='makes the tagger use the rule-based tagger')
    parser.add_argument('train_file', nargs=1, metavar='train', help='a file containing pre-tagged text, which is used to train the tagger')
    parser.add_argument('test_file', nargs=1, metavar='test', help='a file containing untagged text to be tagged by the tagger')
    args = parser.parse_args()

    # Training
    freq_tables = generate_freq_tables(read_file(args.train_file[0]))

    # Tagging
    if args.baseline:
        # Baseline tagging using most likely tag
        for sentence in get_sentences(read_file(args.test_file[0])):
            baseline_tag(sentence, freq_tables)
    elif args.rules:
        # Rule-based tagging
        for sentence in get_sentences(read_file(args.test_file[0])):
            rule_tag(sentence, freq_tables)
    else:
        tag_file(get_sentences(read_file(args.test_file[0])), freq_tables)

if __name__ == "__main__":
    main()
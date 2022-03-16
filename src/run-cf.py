#!/usr/bin/python3

import sys
import utils
import json
import os
import random
from datetime import datetime
from pprint import pprint
from OptionRunner import OptionRunner
from OptionFuzzer import OptionFuzzer
from OptionGrammarMiner import OptionGrammarMiner
from fuzzable_binaries import all_fuzzable_binaries
import fuzzable_binaries

# "grammarv1/" or "grammar"
grammar_directory = "grammarv1/"

#Update this to true if we wish to also store the pass list.
STORE_PASS_VALUE = True

def get_fuzz_results (outstream, myfuzzer, fuzz_count, get_coverage):
    fail_list = []
    unresolved_list = []
    exception_list = []
    pass_list = []

    for i in range(fuzz_count):
        try:
            output = myfuzzer.run(fuzzit=True)
            if type(output[0].args) == list:
                args = " ".join(output[0].args)
            elif type(output[0].args) == str:
                args = output[0].args
            if output[1] == 'FAIL':
                fail_list.append([i, args, output[0].returncode])
                # uncomment the next two lines if output and error needs to be logged.
                # fail_list.append([i, " ".join(output[0].args), output[0].returncode,
                                    # (output[0].stdout + " ::: " + output[0].stderr)])

            elif output[1] == 'UNRESOLVED' and output[0].returncode >2 :
                unresolved_list.append([i, args, output[0].returncode])
                # uncomment the next two lines if output and error needs to be logged.
                # unresolved_list.append([i, output[0].returncode, " ".join(output[0].args),
                                    # (output[0].stdout + " ::: " + output[0].stderr)])
            else:
                if STORE_PASS_VALUE :
                    # only note down the parameters passed and not the output.
                    pass_list.append([i, args, output[0].returncode])
        except Exception as e:
            exception_list.append("Exception occured - {}: {}, for invocation number - {} and input - {}".format(e.__class__,
            e, i, myfuzzer.invocation))
    if get_coverage:
        coverage = myfuzzer.get_coverage()
        if coverage == utils.Coverage():
            outstream.write("Empty coverage received.\n".encode('latin1'))
            outstream.write(str(coverage).encode('latin1'))
        else:
            outstream.write(str(coverage).encode('latin1'))
        outstream.write("\n".encode('latin1'))
    outstream.write("\nEXCEPTION REPORTS - \n".encode('latin1'))
    for exception_details in exception_list:
        outstream.write(exception_details.encode('latin1'))
        outstream.write("\n".encode('latin1'))
    outstream.write("\nCRASH RESULTS - \n".encode('latin1'))
    for fail_result in fail_list:
        outstream.write(str(fail_result).encode('latin1'))
        outstream.write("\n".encode('latin1'))
    outstream.write("\nUNRESOLVED RESULTS - \n".encode('latin1'))
    for unresolved_result in unresolved_list:
        outstream.write(str(unresolved_result).encode('latin1'))
        outstream.write("\n".encode('latin1'))
    outstream.write("\n".encode('latin1'))
    if STORE_PASS_VALUE :
        outstream.write("\nPASSING RESULTS - \n".encode('latin1'))
        for passing_result in pass_list:
            outstream.write(str(passing_result).encode('latin1'))
            outstream.write("\n".encode('latin1'))
        outstream.write("\n".encode('latin1'))

# to print out the grammars (whatever can extracted) in json files.
# N.B. - The grammars are approximate, so, they have been manually verified
# and updated to be as close to the actual grammar as possible.
# Refer to "notes-on-grammars.txt" for further details about those grammars.
def generate_grammar_files():
    for binaryname in all_fuzzable_binaries:
        grammar = None
        testbin = binary_dir + binaryname
        print("Building grammar of {} now!".format(testbin))
        fout = open("grammarv1/"+ binaryname + "-gram.json", 'w')
        orig_stdout = sys.stdout
        sys.stdout = fout
        options = utils.get_options(testbin)
        if options is not None:
            miner = OptionGrammarMiner(testbin)
            grammar = miner.mine_ebnf_grammar()
        print (json.dumps(grammar, indent=4))
        sys.stdout = orig_stdout
        fout.close()

# to fuzz the tools by generating the grammars again and not using the existing
# grammar files.
# N.B. - The grammars are approximate, especially the files/other arguments
# they aren't easily autogenerated
def fuzz_from_scratch():
    for binaryname in all_fuzzable_binaries:
        random.seed(utils.RANDOM_SEED)
        testbin = binary_dir + binaryname
        invalid_options = False
        invalid_values = False
        print("Fuzzing {} now!".format(testbin))
        fout = open("outputdir/"+ binaryname + ".out", 'w')
        orig_stdout = sys.stdout
        sys.stdout = fout
        print("Fuzzing {} now!".format(testbin))
        print ("Options:\n")
        options = utils.get_options(testbin, insert_invalid_options=invalid_options)
        if options is not None:
            pprint(options)
            myrunner = OptionRunner(testbin)
            myfuzzer = OptionFuzzer(myrunner, invalid_options=invalid_options,
                                    invalid_values=invalid_values, max_nonterminals=5)
            print("\nGrammar:\n")
            print (myfuzzer.grammar)
            emptyoptionslist = ['']
            if myfuzzer.grammar['<other_option>'] == emptyoptionslist:
                # has only maybe help and version options
                print("'<other_options>' is empty, fuzzing 100 times")
                get_fuzz_results(sys.stdout, myfuzzer, 100, False)
            elif len(myfuzzer.grammar['<other_option>']) < 5: # arbitrarily chosen for now
                print("size of '<other_options>' is <5, fuzzing 500 times")
                get_fuzz_results(sys.stdout, myfuzzer, 500, False)
            elif len(myfuzzer.grammar['<other_option>']) < 12: # arbitrarily chosen for now
                print("size of '<other_options>' is <12, fuzzing 1000 times")
                get_fuzz_results(sys.stdout, myfuzzer, 1000, False)
            else :
                print("size of '<other_options>' is >12, fuzzing 3000 times")
                get_fuzz_results(sys.stdout, myfuzzer, 3000, False)
            print("\nFinished fuzzing {}!".format(testbin))
        else:
            print ("Options returned None. binary probably doesn't use getopt or any of its variants.")
            print ("Skipping fuzzing this tool.")
        sys.stdout = orig_stdout
        fout.close()

#TODO: Figure out a way to include '\x00' and other characters in the grammar
def fuzz_from_grammarfile():
    binaries = all_fuzzable_binaries
    for binaryname in binaries:
        random.seed(utils.RANDOM_SEED)
        grammar = None
        testbin = binaries[binaryname]
        print("Fuzzing {} now starting at {}!".format(testbin, datetime.now()))
        fout = open("outputdir/"+ binaryname + ".out", 'wb', buffering=0)
        fout.write("Fuzzing {} now starting at {}!\n".format(testbin, datetime.now()).encode('latin1'))
        gram_file = grammar_directory + binaryname + "-gram.json"
        # print (gram_file)
        # print (os.path.exists(gram_file))
        if os.path.exists(gram_file):
            myrunner = OptionRunner(testbin, gram_file)
            try:
                myfuzzer = OptionFuzzer(myrunner, invalid_options=False,
                                    invalid_values=False, max_nonterminals=5)
            except TypeError as e: #Raised by OptionFuzzer.init()
                print (e)
                print ("Grammar returned None. Binary probably doesn't use getopt or any of its variants.")
                print ("Skipping fuzzing this tool.")
                fout.write(e)
                fout.write("Grammar returned None. Binary probably doesn't use getopt or any of its variants.\n")
                fout.write("Skipping fuzzing this tool.")
                fout.close()
                continue

            fout.write("\nGrammar:\n".encode('latin1'))
            fout.write(json.dumps(myfuzzer.grammar).encode('latin1'))
            fout.write("\n".encode('latin1'))
            emptyoptionslist = ['']
            if len(myfuzzer.grammar['<other_option>']) < 5: # arbitrarily chosen for now
                fout.write("size of '<other_options>' is <5, fuzzing 500 times\n".encode('latin1'))
                get_fuzz_results(fout, myfuzzer, 500, False)
            elif len(myfuzzer.grammar['<other_option>']) < 12: # arbitrarily chosen for now
                fout.write("size of '<other_options>' is <12, fuzzing 2000 times\n".encode('latin1'))
                get_fuzz_results(fout, myfuzzer, 2000, False)
            else :
                fout.write("size of '<other_options>' is >12, fuzzing 3000 times\n".encode('latin1'))
                get_fuzz_results(fout, myfuzzer, 3000, False)
            fout.write("\nFinished fuzzing {} at {}!".format(testbin, datetime.now()).encode('latin1'))
        else:
            fout.write("Grammar file not found. Skipping fuzzing this tool. Timestamp:{}".format(datetime.now()).encode('latin1'))
        fout.close()

if __name__ == "__main__":
    fuzz_from_grammarfile()

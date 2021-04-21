import os
import sys
from subprocess import Popen, PIPE
import re
from pathlib import Path

def get_claim(addresses, lower_balance_bounds, upper_balance_bounds, tokens):
    lower_bound_claim = "{{?S[{address} in {token}]}}:>Int >=Int {bound}"
    lower_bound_claim = "{{?S[{address} in {token}]}}:>Int <=Int {bound}"
    component_claims = []
    for address in addresses:
        #upper bound on both tokens
        component_claims.append("((({{?S[{address} in {token0}]}}:>Int <=Int {xbound}) orBool ({{?S[{address} in {token1}]}}:>Int <Int {ybound})) andBool (({{?S[{address} in {token0}]}}:>Int <Int {xbound}) orBool ({{?S[{address} in {token1}]}}:>Int <=Int {ybound})))".format(address=address, token0=tokens[0], token1=tokens[1], xbound=upper_balance_bounds[address][tokens[0]], ybound=upper_balance_bounds[address][tokens[0]]))
        #lower bound on both tokens
        component_claims.append("((({{?S[{address} in {token0}]}}:>Int >=Int {xbound}) orBool ({{?S[{address} in {token1}]}}:>Int >Int {ybound})) andBool (({{?S[{address} in {token0}]}}:>Int >Int {xbound}) orBool ({{?S[{address} in {token1}]}}:>Int >=Int {ybound})))".format(address=address, token0=tokens[0], token1=tokens[1], xbound=lower_balance_bounds[address][tokens[0]], ybound=lower_balance_bounds[address][tokens[0]]))

    claim = " andBool ".join(component_claims)
    return claim
    

def reordering_mev(program, spec_file, outfile, acc, tokens, balances, pre_price, post_price, initial_segment):
    BLANK_SPEC = """{acc} in {token0} gets {balance0} ; 
{acc} in {token1} gets {balance1} ;
{transactions}
"""

    program = program.strip()

    addresses = set()
    all_transactions = program.split('\n')
    print(all_transactions)
    for i in range(1, len(all_transactions), 2):
        chunks = all_transactions[i].split()
        print(chunks)
        addresses.add(chunks[0])

    initialTxs = []
    for i in initialSegment:
        initialTxs.append(all_transactions[1+2*i])

    krunspec = BLANK_SPEC.format(token0 = tokens[0], token1 = tokens[1], acc = acc, balance0 = balances[0], balance1=balances[1],transactions = '\n'.join(initialTxs))
    open("temp.k". "w").write(krunspec)
    pipe = Popen("krun " + program_file, shell=True, stdout=PIPE, stderr=PIPE)
    outputspec = pipe.stdout.read()
    Popen("rm temp.k", shell=True, stdout=PIPE, stderr=PIPE)
    print(outputspec)

   raise Exception("debugging related")
 
   print(addresses)

    lower_balance_bounds = {}
    upper_balance_bounds = {}

    MAX = 99999999999999999999999999999999
    MIN = -99999999999999999999999999999999
    
    for address in addresses:
        lower_balance_bounds[address] = {tokens[0] : MAX, tokens[1] : MAX}
        upper_balance_bounds[address] = {tokens[0] : MIN, tokens[1] : MIN}

    claim = get_claim(addresses, lower_balance_bounds, upper_balance_bounds, tokens)
    print(claim)
    
    spec = BLANK_SPEC.format(acc=acc, token0=tokens[0], token1=tokens[1], balance0=balances[0], balance1=balances[1],transactions=program, claim=claim)
    output = ""
    Path(os.path.dirname(spec_file)).mkdir(parents=True, exist_ok=True)
    print("Writing spec to", spec_file)
    open(spec_file, "w").write(spec)
    print("Starting proof..." )
    sys.stdout.flush()
    pipe = Popen("kprove --default-claim-type all-path " + spec_file, shell=True, stdout=PIPE, stderr=PIPE)
    output = pipe.stdout.read() + pipe.stderr.read()
    output = str(output, "utf-8")
    print(output)
    if "#True" not in output:
        print("MEV FOUND!")
        print("Writing MEV configuration to", outfile, "...")
        open(outfile, "w").write(output)
    else:
        print("MEV NOT FOUND!")
        print("Writing MEV configuration to", outfile, "...")
        open(outfile, "w").write("MEV NOT FOUND!")

def main():
    pass

if __name__ == '__main__':
    main()

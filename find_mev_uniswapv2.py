import os,sys
from pathlib import Path
from collections import defaultdict
from uniswapv2 import UniswapV2
import itertools
import logging
import random

def all_orderings(all_transactions):
    num_transactions = len(all_transactions)
    if num_transactions < 10:
        ret = list(itertools.permutations(all_transactions))
        random.shuffle(ret)
        return ret
    else:
        ret = []
        for i in range(400000):
            ret.append(random.sample(all_transactions, num_transactions))
        return ret

def default_to_regular(d):
    if isinstance(d, defaultdict):
        d = {k: default_to_regular(v) for k, v in d.items()}
    return d


def reordering_mev(program, program_file, outfile, exchange_acc, tokens, balances, pre_price, post_price, pair_address, block, convergence):

    program = program.strip()

    transactions = program.split('\n')
    all_transactions = [transaction.strip() for transaction in transactions if not transaction.strip().startswith('//')]
    logging.info(all_transactions)

    weth = '1097077688018008265106216665536940668749033598146'
    token0 = weth
    
    if weth == tokens[0]:
        token1 = tokens[1]
    elif weth == tokens[1]:
        token1 = tokens[0]
    else:
        logging.warning("WETH not part of the pair")
        token0 = tokens[0]
        token1 = tokens[1]

    lower_bounds = defaultdict(lambda : {token0 : 99999999999999999999999999999999})
    upper_bounds = defaultdict(lambda : {token0 : -99999999999999999999999999999999})

    lower_bound_paths = defaultdict(lambda : ('', {}))
    upper_bound_paths = defaultdict(lambda: ('', {}))

    Path(os.path.dirname(program_file)).mkdir(parents=True, exist_ok=True)
    path_to_mev = {}
    
    path_num = 0
    for transaction_ordering in all_orderings(all_transactions):
        u = UniswapV2({tokens[0] : balances[0], tokens[1] : balances[1]}, exchange_acc)
        for transaction in transaction_ordering:
            u.process(transaction)
        token_balances = u.config()
        mev = 0
        for acc in token_balances:
            if acc == exchange_acc:
                continue
            balance0 =  token_balances[acc][token0]
            balance1 =  token_balances[acc][token1]
            total_balance = balance0 + (token_balances[exchange_acc][token0] * balance1) / token_balances[exchange_acc][token1]
            if total_balance < lower_bounds[acc][token0]:
                lower_bounds[acc][token0] = total_balance
                lower_bound_paths[acc] = ('\n'.join(transaction_ordering), token_balances)
            if total_balance > upper_bounds[acc][token0]:
                upper_bounds[acc][token0] = total_balance
                upper_bound_paths[acc] = ('\n'.join(transaction_ordering), token_balances)
            extortion = upper_bounds[acc][token0] - lower_bounds[acc][token0]
            #mev += extortion
            mev = max(mev, extortion)
        path_num += 1
        path_to_mev[path_num] = mev

    sorted_items = sorted(path_to_mev.items())
    #print("Writing hill climbing data to {} ...".format(program_file))
    if convergence:
        fout = open(program_file, 'w')
        fout.write('pathnum,mev\n')
        fout.write('\n'.join(["{},{}".format(path_num, mev) for path_num, mev in sorted_items]))
        
        
    mev = 0    
    for acc in lower_bounds:
        extortion = upper_bounds[acc][token0] - lower_bounds[acc][token0]
        # mev += extortion
        mev = max(mev,extortion)
    '''        
        print(acc, extortion)
        
    for acc in lower_bounds:
        print(acc)
        print(default_to_regular(upper_bound_paths[acc][1]))
        print(default_to_regular(lower_bound_paths[acc][1]))
        print(default_to_regular(upper_bound_paths[acc][0]))
        print('')
        print(default_to_regular(lower_bound_paths[acc][0]))
    '''

    print(exchange_acc, pair_address, token0, token1, block, len(all_transactions), mev, sep=',')
    
#    print(upper_bound_paths)
#    print(lower_bound_paths)

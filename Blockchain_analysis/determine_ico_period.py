from bs4 import BeautifulSoup as bs
from datetime import datetime
import math
import numpy as np
import os
import pandas as pd
import requests
from urllib.request import urlopen, Request

def check_cols(df):
    try:
        from_address = df['from'][0]
        '''
        'STARTUP Name', 'TxTime', 'blockNumber', 'timeStamp', 'hash', 'nonce',
        'blockHash', 'from', 'contractAddress', 'to', 'value', 'tokenName',
        'tokenSymbol', 'tokenDecimal', 'transactionIndex', 'gas', 'gasPrice',
        'gasUsed', 'cumulativeGasUsed', 'input', 'confirmations'
        '''
        return True
    except Exception:
        '''
        'STARTUP Name', 'Token Address', 'Transaction No', 'Crawl time',
        'TxHash', 'Age', 'From', 'To', 'Quantity'
        '''
        return False

def get_cols(df):
    try:
        from_address = df['from'][0]
        '''
        'STARTUP Name', 'TxTime', 'blockNumber', 'timeStamp', 'hash', 'nonce',
        'blockHash', 'from', 'contractAddress', 'to', 'value', 'tokenName',
        'tokenSymbol', 'tokenDecimal', 'transactionIndex', 'gas', 'gasPrice',
        'gasUsed', 'cumulativeGasUsed', 'input', 'confirmations'
        '''
        return 'from', 'to', 'contractAddress', 'value'
    except Exception:
        '''
        'STARTUP Name', 'Token Address', 'Transaction No', 'Crawl time',
        'TxHash', 'Age', 'From', 'To', 'Quantity'
        '''
        return 'From', 'To', 'Token Address', 'Quantity'

def get_total_supply(address):
    api_key = 'FFHPVZ1WA58G3ZBJZICEITPXUCCMPHR87M'
    url = f'https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress={address}&apikey={api_key}'
    r = requests.get(url)
    data = r.json()
    supply = data['result']
    return int(supply)


def guess_main_wallets(df):
    _from, _to, _contractaddress, _quantity = get_cols(df)
    name = df['STARTUP Name'][0]
    address = df[_contractaddress][0]
    print(f'{name} : {address}')
    total_supply = get_total_supply(address)
    token_decimal = df['tokenDecimal'][0]
    if pd.notnull(token_decimal):
        total_supply = total_supply * math.pow(10, -(int(token_decimal)))
    else:
        total_supply = total_supply * math.pow(10, -10)
    if total_supply <= 0:
        return [], np.nan
    wallet_received_amount = {}
    wallet_sent_amount = {}
    num_transfers = 0
    for index, row in df.iterrows():
        value = int(row[_quantity])
        if pd.notnull(token_decimal):
            value = value * math.pow(10, -(int(token_decimal)))
        else:
            value = value * math.pow(10, -10)

        sending_add = row[_from]
        receiving_add = row[_to]
        if receiving_add not in wallet_received_amount:
            wallet_received_amount[receiving_add] = 0
        if sending_add not in wallet_sent_amount:
            wallet_sent_amount[sending_add] = 0
        wallet_received_amount[receiving_add] += value
        wallet_sent_amount[sending_add] += value
        if num_transfers > 600:
            break
        num_transfers += 1

    wallet_received_amount = {key: value for key, value in wallet_received_amount.items() if value / total_supply > 0.05}
    wallet_sent_amount = {key: value for key, value in wallet_sent_amount.items() if value / total_supply > 0.05}
    main_wallets = list(wallet_received_amount.keys())
    for key in wallet_sent_amount.keys():
        main_wallets.append(key)
    return main_wallets, token_decimal

def get_transactions(address):
    api_key = 'FFHPVZ1WA58G3ZBJZICEITPXUCCMPHR87M'
    url = f'http://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}'
    r = requests.get(url)
    data = r.json()['result']
    return data

class Node:
    def __init__(self, prev_node, next_node, node_type, address):
        self.address = address
        self.prev = prev_node
        self.next = next_node
        self.type = node_type
        self.values = []
        self.transaction_ids = []
        self.timestamp = 0
        self.prev_list = []
        self.next_list = []

def oneLayerBFS(wallet):
    main_node = Node(None, None, 'crowd sale', wallet)
    if wallet == '0x0000000000000000000000000000000000000000':
        return main_node
    transactions = get_transactions(wallet)
    if not transactions:
        return main_node
    print(f'ANALYZING WALLET: {wallet}, contains {len(transactions)} transactions')
    for transaction in transactions:
        value = int(transaction['value'])
        if value == 0:
            continue
        timestamp = int(transaction['timeStamp'])
        receiving_add = transaction['to']
        sending_add = transaction['from']
        if receiving_add == wallet:
            temp_node = Node(None, None, 'influx', sending_add)
            temp_node.timestamp = timestamp
            temp_node.next = main_node
            temp_node.next_list.append(main_node)
            main_node.prev_list.append(temp_node)
        elif sending_add == wallet:
            temp_node = Node(None, None, 'outflux', receiving_add)
            temp_node.timestamp = timestamp
            temp_node.prev = main_node
            temp_node.prev_list.append(main_node)
            main_node.next_list.append(temp_node)
    return main_node

def oneLayerDFS(main_node):
    cycles = 0
    one_layer_cycles = []
    layer1_prev = main_node.prev_list
    for prev_node in layer1_prev:
        address_list = [prev_node.address]
        timestamp_prev = prev_node.timestamp
        if prev_node.next.address == main_node.address:
            address_list.append(main_node.address)
        else:
            print('something is wrong')
        for next_node in main_node.next_list:
            timestamp_next = next_node.timestamp
            if timestamp_next - timestamp_prev <= 86400:
                address_list.append(next_node.address)
            else:
                continue
            # check for cycle by checking for duplicates
            no_duplicates = set(address_list)
            if len(no_duplicates) != len(address_list) and main_node.address in address_list:
                print('CYCLE DETECTED')
                print(address_list)
                temp_list = [address for address in address_list]
                one_layer_cycles.append(temp_list)
                cycles += 1
            del address_list[-1]
    return cycles, one_layer_cycles

def twoLayerBFS(wallet):
    # Layer 1
    main_node = Node(None, None, 'crowd sale', wallet)
    if wallet == '0x0000000000000000000000000000000000000000':
        return main_node
    transactions = get_transactions(wallet)
    if not transactions:
        return main_node
    print(f'ANALYZING WALLET: {wallet}, contains {len(transactions)} transactions')
    if len(transactions) > 500:
        print('TOO MANY TRANSACTIONS IN WALLET... MOVING TO NEXT')
        return main_node
    for transaction in transactions:
        value = int(transaction['value'])
        timestamp = int(transaction['timeStamp'])
        if value == 0:
            continue
        receiving_add = transaction['to']
        sending_add = transaction['from']
        if receiving_add == wallet:
            temp_node = Node(None, None, 'influx', sending_add)
            temp_node.timestamp = timestamp
            temp_node.next = main_node
            temp_node.next_list.append(main_node)
            main_node.prev_list.append(temp_node)
        elif sending_add == wallet:
            temp_node = Node(None, None, 'outflux', receiving_add)
            temp_node.timestamp = timestamp
            temp_node.prev = main_node
            temp_node.prev_list.append(main_node)
            main_node.next_list.append(temp_node)

    # Layer 2
    for prev_node in main_node.prev_list:
        transactions = get_transactions(prev_node.address)
        if not transactions:
            continue
        for transaction in transactions:
            value = int(transaction['value'])
            timestamp = int(transaction['timeStamp'])
            if value == 0:
                continue
            receiving_add = transaction['to']
            sending_add = transaction['from']
            # layer 1 influx receiving form layer2 influx
            if receiving_add == prev_node.address:
                temp_node = Node(None, None, 'influx', sending_add)
                temp_node.timestamp = timestamp
                temp_node.next = prev_node
                prev_node.prev_list.append(temp_node)

    for next_node in main_node.next_list:
        transactions = get_transactions(next_node.address)
        if not transactions:
            continue
        for transaction in transactions:
            try:
                value = int(transaction['value'])
            except:
                continue
            if value == 0:
                continue
            receiving_add = transaction['to']
            sending_add = transaction['from']
            # layer 1 outflux sending to layer 2 outflux
            if sending_add == next_node.address:
                temp_node = Node(None, None, 'outflux', receiving_add)
                temp_node.timestamp = timestamp
                temp_node.prev = next_node
                next_node.next_list.append(temp_node)

    return main_node

def twoLayerDFS(main_node):
    cycles = 0
    two_layer_cycles = []
    layer1_prev = main_node.prev_list
    layer2_prev = []
    for prev_node in layer1_prev:
        layer2_prev.append(prev_node.prev_list)

    for layer2_list in layer2_prev:
        for layer2_influx_node in layer2_list:
            address_list = [layer2_influx_node.address]
            timestamp_layer2_influx = layer2_influx_node.timestamp # timestamp of layer2_influx to layer1_influx
            layer1_influx_node = layer2_influx_node.next
            timestamp_layer1_influx = layer1_influx_node.timestamp # timestamp of layer1_influx to main_node
            if timestamp_layer1_influx - timestamp_layer2_influx <= 86400:
                address_list.append(layer1_influx_node.address)
            else:
                continue

            if layer1_influx_node.next.address == main_node.address:
                address_list.append(main_node.address)
            else:
                print('we have a problem')
                exit()

            for layer1_outflux_node in main_node.next_list:
                timestamp_layer1_outflux = layer1_outflux_node.timestamp # timestamp of main_node to layer1_outflux
                if timestamp_layer1_outflux - timestamp_layer1_influx <= 86400:
                    address_list.append(layer1_outflux_node.address)
                else:
                    continue

                for layer2_outflux_node in layer1_outflux_node.next_list:
                    timestamp_layer2_outflux = layer2_outflux_node.timestamp # timestamp of layer1_outflux to layer2_outflux
                    if timestamp_layer2_outflux - timestamp_layer1_outflux <= 86400:
                        address_list.append(layer2_outflux_node.address)
                    else:
                        continue

                    # only going to check for a cycle of exactly length 5
                    if len(address_list) != len(set(address_list)) and main_node.address in address_list:
                        print('CYCLE DETECTED')
                        print(address_list)
                        temp_list = [address for address in address_list]
                        two_layer_cycles.append(temp_list)
                        cycles += 1
                    del address_list[-1]
                del address_list[-1]
    print(f'{main_node.address} COMPLETED\n')
    return cycles, two_layer_cycles

def analyze(main_wallets, token_decimal):
    suspicious_wallets = []
    for wallet in main_wallets:
        if wallet == '0x0000000000000000000000000000000000000000':
            continue
        print(f'Analyzing wallet: {wallet}')
        transactions = get_transactions(wallet)
        ether_in = {}
        ether_out = {}
        # wallet cannot be suspicious without a significant number of transactions
        if len(transactions) > 20:
            for transaction in transactions:
                value = int(transaction['value'])
                value = value * math.pow(10, -18)
                if value == 0:
                    # token transfer, not interested for now
                    continue
                receiving_add = transaction['to']
                sending_add = transaction['from']
                if receiving_add not in ether_in:
                    ether_in[receiving_add] = 0
                if sending_add not in ether_out:
                    ether_out[sending_add] = 0
                ether_in[receiving_add] += value
                ether_out[sending_add] += value

            if math.fabs(sum(ether_in.values()) - sum(ether_out.values())) < 0.0001:
                if len(ether_out) > 0:
                    if float(len(ether_in)) / float(len(ether_out)) > 5.0:
                        print(f'Total ether_in: {sum(ether_in.values())}')
                        print(f'Total ether_out: {sum(ether_out.values())}')
                        suspicious_wallets.append(wallet)

    if len(main_wallets) > 0:
        print(f'Percent suspicious: {float(len(suspicious_wallets)) / float(len(main_wallets))}')

def summary_file_test():
    sum_file = '/SummaryFile.csv'
    df = pd.read_csv(os.getcwd() + sum_file)
    for index, row in df.iterrows():
        distributors = []
        if str(row['DistributorAddress']) != 'nan':
            distributors.append(row['DistributorAddress'])
        if str(row['DistributorAddress2']) != 'nan':
            distributors.append(row['DistributorAddress2'])
        if distributors:
            name = row['STARTUP NAME']
            target_dir = os.getcwd() + '/results/' + name
            if os.path.isfile(target_dir + '/cycles.txt'):
                continue

            print(f'WORKING ON {name}')
            print(distributors)
            detect_cycles(name, distributors)
        else:
            continue


def detect_cycles(name, main_wallets):
    for wallet in main_wallets:
        print('SINGLE LAYER TEST')
        one_layer_cycles, one_layer_list = oneLayerDFS(oneLayerBFS(wallet))
        print('DOUBLE LAYER TEST')
        two_layer_cycles, two_layer_list = twoLayerDFS(twoLayerBFS(wallet))

        target_dir = os.getcwd() + '/results/' + name
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)

        mode = 'w'
        if os.path.isfile(target_dir + '/cycles.txt'):
            mode = 'a'

        with open(target_dir + '/cycles.txt', mode) as f:
            f.write(f'{wallet} RESULTS\n\n')
            f.write(f'SINGLE LAYER CYCLES: {one_layer_cycles}\n\n')
            for cycle in one_layer_list:
                f.write(str(cycle) + '\n')
                f.write('\n')

            f.write(f'DOUBLE LAYER CYCLES: {two_layer_cycles}\n\n')
            for cycle in two_layer_list:
                f.write(str(cycle) + '\n')
                f.write('\n')


def main():
    cwd = os.getcwd()
    data_dir = cwd + '/data/'

    os.chdir(data_dir)

    files = os.listdir(data_dir)
    from random import shuffle
    shuffle(files)

    cols = ['1 Layer Cycles Detected', '2 Layer Cycles Detected']
    for f in files:
        if f.split('.')[-1] != 'xlsx':
            continue
        df = pd.read_excel(f)
        if not check_cols(df):
            continue

        main_wallets, token_decimal = guess_main_wallets(df)
        one_layer, two_layer = detect_cycles(main_wallets)
        results = [one_layer, two_layer]
        temp_df = pd.DataFrame([results], columns=cols)
        temp_df.to_csv(cwd + '/results/' + f + '.csv', index=False)

summary_file_test()

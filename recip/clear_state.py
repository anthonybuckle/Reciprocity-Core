#!/usr/bin/env python3

from recip.util import Config
import shutil
import os

if os.path.exists(Config.getFilePath('CHAIN_DIRECTORY', 'ACCOUNTS_INDEX_DB')):
    shutil.rmtree(Config.getFilePath('CHAIN_DIRECTORY', 'ACCOUNTS_INDEX_DB'))

if os.path.exists(Config.getFilePath('CHAIN_DIRECTORY', 'BLOCKCHAIN_DB')):
    shutil.rmtree(Config.getFilePath('CHAIN_DIRECTORY', 'BLOCKCHAIN_DB'))
    
if os.path.exists(Config.getFilePath('CHAIN_DIRECTORY', 'INDEX_DB')):
    shutil.rmtree(Config.getFilePath('CHAIN_DIRECTORY', 'INDEX_DB'))
    
if os.path.exists(Config.getFilePath('CHAIN_DIRECTORY', 'STATE_DB')):
    shutil.rmtree(Config.getFilePath('CHAIN_DIRECTORY', 'STATE_DB'))
    
if os.path.exists(Config.getFilePath('CHAIN_DIRECTORY', 'STATE_INDEX_DB')):
    shutil.rmtree(Config.getFilePath('CHAIN_DIRECTORY', 'STATE_INDEX_DB'))
    
if os.path.exists(Config.getValue('PEERS_DB')):
    shutil.rmtree(Config.getValue('PEERS_DB'))
    
if os.path.exists(Config.getFilePath('CHAIN_DIRECTORY', 'PERSISTENT_DB')):
    shutil.rmtree(Config.getFilePath('CHAIN_DIRECTORY', 'PERSISTENT_DB'))

if os.path.exists(Config.getValue('CONTRACTS_DIR')):
    with open(Config.getValue('CONTRACTS_DIR'), 'w') as contracts:
        contracts.write('[]')

if os.path.exists(Config.getValue('SIDECHAINS_DIR')):
    with open(Config.getValue('SIDECHAINS_DIR'), 'w') as sidechains:
        sidechains.write('[]')
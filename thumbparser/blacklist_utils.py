import os, pickle
import numpy as np
# %%
def get_blacklist(dirpath:str, filename:str):
    '''
    Get a blacklist.
    
    :param dirpath: pkl file path of the blacklist.
    :param filename: pkl name.
    '''
    file = os.path.join(dirpath, filename)
    with open(file, "rb") as infile:
        blacklist = pickle.load(infile)
    return blacklist

def update_blacklist(dirpath:str, filename:str, new_id:dict):
    '''
    Update a blacklist with new result.
    
    :param dirpath: pkl file path of the blacklist.
    :param filename: pkl name.
    :param result: a dictionary to be appended to blacklist file.
    :param verbose: If true, print a statement everytime and update is applied.
    '''
    file = os.path.join(dirpath, filename)
    with open(file, "rb") as infile:
        blacklist = pickle.load(infile)
    assert isinstance(blacklist, list), "blacklist file is not a dict."
    if new_id not in blacklist:
        blacklist += [new_id]
        with open(file, "wb") as outfile:
            pickle.dump(blacklist, outfile)

def create_blacklist(dirpath:str, filename:str, new_id:dict):
    '''
    Creates a new blacklist file.
    
    :param dirpath: Path to the directory to be saved.
    :param filename: Name of logfile.
    :return result: A list of results.
    '''
    os.makedirs(dirpath, exist_ok=True)
    file = os.path.join(dirpath, filename)
    with open(file, "wb") as outfile:
        pickle.dump(list([new_id]), outfile)
    print("Blacklist created")

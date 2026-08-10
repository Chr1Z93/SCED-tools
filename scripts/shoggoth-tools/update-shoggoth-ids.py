import json
from pathlib import Path

english_path = Path()
german_path = Path()
name_map_path = Path()

def update_shoggoth_ids():
    # load english saved object

    # create a map of english name -> ID

    # load german shoggoth project

    # loop through cards, updating every ID based on the two maps
    # 1: german name -> english name | 2: english name -> ID
    # if no match found, change ID to "NOT-FOUND"
    # if multiple cards with the same name BUT different original ID are found, change ID to "CONFLICT" (for all cards with that name)

    # save updated file
    return


if __name__ == "__main__":
    update_shoggoth_ids()

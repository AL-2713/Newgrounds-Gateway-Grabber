# Newgrounds-Gateway-Grabber
Easily archive gateway data for a Newgrounds game, given it's app_id

Data including medals, scoreboards, scoreboard entries, save groups, and save data

You can add these strings onto the command to scrape more data:

scoreboards: scoreboard entries

savefiles: save data


# Usage
python mainGate.py [app_id] ['scoreboards','savefiles']

# Notes
All the data gets saved to a SQL .db file. A base file is included, although it would be nice to generate it if it's not in the directory

The script is also able to guess image URLs to mystery medals. It's not 100% functional though, there's rare instances where the file can't be guessed

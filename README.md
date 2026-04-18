# Newgrounds-Gateway-Grabber
Easily archive gateway data for a Newgrounds game, given it's app_id

Data including medals, scoreboards, scoreboard entries, save groups, and save data


# Usage
python mainGate.py [app_id] ['scoreboards','savefiles', 'seperateData', 'exportJson']

You can add these strings onto the command to do more actions:

scoreboards: Scrape scoreboard entries

savefiles: Scrape save data and user submissions

seperateData: Download scoreboards and save files to a seperate SQL file, if those are enabled

exportJson: Export the game medatada into a json file (exports\[app_id].json)

# Notes
All the data gets saved to a SQL .db file, which is generated if it doesn't already exist

The script is also able to guess image URLs to mystery medals. It's not 100% functional though, there's rare instances where the file can't be guessed

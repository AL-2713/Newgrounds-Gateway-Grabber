# Newgrounds-Gateway-Grabber
Archive gateway data for a Newgrounds game, given it's app_id or SWF url

Data including medals, scoreboards, scoreboard entries, save groups, and save data


# Usage
python mainGate.py [app_id | SWF url] ['scoreboards','savefiles', 'seperateData', 'exportJson']
If chosen to download with the SWF url, the script will download the url and extract the app_id and encryptionKey from the SWF. This is still in testing, so expect most games to not work with this. Inputing the app_id will still download the gateway data, just not the encryptionKey or SWF file.

You can add these strings onto the command to do more actions:

scoreboards: Scrape scoreboard entries

savefiles: Scrape save data and user submissions

seperateData: Download scoreboards and save files to a seperate SQL file, if those are enabled

downloadThumbs: Download medal and save file thumbnails

exportJson: Export the game medatada into a json file (exports\\[app_id].json)

# Notes
All metadata gets saved to a SQL .db file, which is generated if it doesn't already exist. Downloads are stored in a folder called "downloads/[app_id]"

The script is also able to guess image URLs to mystery medals. It's not 100% functional though, there's rare instances where the file can't be guessed

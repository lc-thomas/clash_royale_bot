# clash_royale_bot

## How does it work ?

The script looks for Bluestacks.exe in the list of running processes.
Then, regularly (every minute now, but this is easily configurable), it checks for there are chests to open, or to start unlock.


## Requirements

### System

- Windows
- Python3
- Bluestacks and clash royale running

### Libraries

- cv2
- pywinauto
- numpy
- psutil

## TODO

- Connect back to clash royale when connection is interrupted (when connecting to clash with another device)
- Read the time above chest so the program connects to the account only to open chests
- Unlock little chests first, so the player have more time to connect back
- Unlock daily gifts

## Notes

- Images in this repository are for the french version of the game, you'll have to replace them with images of the game in your own language for this to work (or put the game in french in bluestacks). If you do screenshot your images, please make a pull request so I add them to the repository

- Size matters. The comparison algorithm doesn't like it when objects aren't of the same size. The size of the bluestacks window must be the same when you did your screenshots than when the program runs
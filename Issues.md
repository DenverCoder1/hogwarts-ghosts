## Bugfixes
- Issue to fix - Insufficient perms should give a specific "No perms error code" (movechannel, createchannel?)
- ~movechannel gives you success AND error when the bot has insufficient perms to do it
- On archive server/archivechannel/wherever else the message size is dependant on a certain size of discord character limit... Learn how to split embeds into multople different embeds of <2K side


## Improvements

- has_any_role should be an array
- Sheet management : reordering
- Better README to repro
- ~archivechannel should name channel for search reasons.
- ~archive command does not exist. Did you mean "Archivechannel"
- Help : arrow keys for navigation?
- Allow minimal bot to run without .env file

## Features

- Write tests
- ~renamechannel channel1 newchannel
- admin verifiedrole @Verified Puzzler
- Category management : ~clonecategory etc
- Role assign : ~assignrole @rolename @user1 @user2 @user3
- Simple lookup for all major encodings - ~lookupsheet morse/pigpen etc
- setindex 4 on sheetcommands for "How many other tabs exist"
- changenick
- botsay

- BBN - sight read... music?
- BBN - Morse code by audio
- BBN - ~ cipher race for perfect pitch recognition

## QQQ Features

- QQQ: ~housepoints 2021 and ~housecup 2021
- QQQ - Command where you can go "~newassignment [Link] [Date]"
- QQQ - And command where you go "~allassignments" to display them all in a single embed

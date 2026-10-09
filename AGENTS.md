# Beginner to-do cli/tui app

## Project goals

- A CLI/TUI to-do app for personal use.
- Being able to navigate different categories and edit/remove todos
- Being able to track weekly tasks and simply marking them as done

## Project

- Language: Python, uv
- Library for building the TUI: Textual
- Storage: json in data directory
- utils directory contains function for editing json

## Important for Agents

- You cannot edit, remove or change in any way anything in any directory besides textual-tui/ without permission or if asked specifically
- You're job is to help me build the tui part, the user interface part for me

## What tui should look like / be able to do

- Vertical layout
- Top part horizontally buttons labelled with the categories and numbered, when user presses a number associated with the category it should switch to that, the selected button should be highlighted
- Below buttons is the to-dos part, numbered.
- There are different modes just like vim.
    - In normal mode you can only switch between categories
    = In select mode you are able to select a to-do
    - In select mode you can press a shortcut to delete, edit, rearrange or view to-do details in a modal/pop-up.
    - Every action needs to be in a modal/pop-up
    - In the delete pop up there is only a confirmation like "are you sure you want to delete this"
    - Edit gives you prefilled fields and you can edit those then save changes with a shortcut
    - In rearrange you can give a number so you can choose which order that one to-do will appear
    - You can add to-dos in the current category selected and in insert mode
    - I have most of the function ready found in utils you can only use those nothing else, you cannot change those if you cannot do what I ask using those you have to tell me why, not solve it unless specifically asked to do it for me and give permission
    - view to do gives you a full version of the note
    - every modal/pop-up can be cancelled
    - need bindings to be easily editable by me
    - need tui to be resposible and have a nice border to the to-dos nothing else (so two colours)
    - for testing we're working with to-do-test.json
    - the main data for to-dos is data/to-do.json
    - able to add categories and remove them
- new weekly tasks feature to be implemented by AI
    - data in data/ called weekly-tasks.json
    - shortcut to enter is 0 and reserved for weekly tasks
    - when weekly tasks is entered the content shows up where list of to-dos show up in the same way and fashion
    - top part has a date displayed like 5 Oct - 11 Oct and I am able to edit this in insert mode and can select start and end date
    - the date part in json should be stored as a date but the year should not be displayed in the top part
    - from what I can see textual does not have a built in datepicker so it's up to you to figure out a keyboard-oriented way to edit the dates, no mouse should be used for anything anywhere
    - Can add different items that has a name and can be marked "done" or "not done" and if done it should be marked by something like a checkbox, that is all it can do, toggle done and not done.
    - when date changes the status of the items (done or not done) does not change
    - can also remove items
    - the functions are not yet implemented. It is to be by you for that you have permission to go into utils and create neccessary function in a folder called weekly-tasks/
    - when quit it goes back to to-dos (can quit same way as with to-dos by escape key)
    - does not show up as a button like to-do categories, just in the footer or bottom part as a possible shortcut
    - same normal/insert mode and editing style applies as in to-dos
    - in normal mode you should not be able to select the items
    - should be able to rearrange the items the same way as in to-dos

## Others

- Prefer built-in libraries
- DO NOT install anything without permission

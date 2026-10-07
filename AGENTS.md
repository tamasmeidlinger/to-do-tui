# Beginner to-do cli/tui app

## Project goals

- A CLI/TUI to-do app for personal use.
- Being able to navigate different categories and edit/remove todos

## Project

- Language: Python, uv
- Storage: json in data directory
- utils directory contains function for editing json

## Important for Agents

- You cannot edit, remove or change in any way anything in any directory beside tui/
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
    - I have most of the function ready found in utils you can only use those nothing else, you cannot change those if you cannot do what I ask using those you have to tell me why, not solve it
    - view to do gives you a full version of the note
    - every modal/pop-up can be cancelled
    - need bindings to be easily editable by me
    - need tui to be resposible and have a nice border to the to-dos nothing else (so two colours)
    - for testing we're working with to-do-test.json
    - Forgot the modal for adding to-do in the current category we're in


## Others

- Prefer built-in libraries
- DO NOT install anything without permission

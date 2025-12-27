# BlockBot
## Overview

- Voice channel intros
  - Customizable intro sound clips
  - Plays once someone joins a voice channel

- Polls
  - Create polls to get opinions from members

- Controlling a Minecraft server
  - Users can start and stop a server hosted on the same machine as the bot
  
- Points system
  - Betting with adjustable odds
  - Spending points on sound clips to play in voice channels
  - Gain points by spending time in voice channel
  - Lose points by spending time in AFK channel
  
- Rolling dice system
  - Simulates a rolling dice
  - This allows you to choose how many dice, how many faces, and modifiers


- Anyone can change nicknames (if the bot is a higher role than target)

## Use Case

Having the bot control the Minecraft server was the original purpose, and it definitely serves it. Anyone is able to start the server and close it when they are finished, so the server does not need to be running 24/7.

The intros are a great success in my experience, as it as a personal touch to every user.

## Setup

The file structure can be found in the docs folder, along with any important info regarding using the bot.

Python >= 3.10 is required for Py-Cord >= v2.7.0.

## Notes
This bot is not without fault. The server portion is mostly reliable, however it is possible to cause data-loss/corruption to the Minecraft server rarely. It is recommended to make regular backups of any World files you have

This project is mainly used for myself, so it can change frequently and without warning. Feel free to contribute regardless.

# DocWatcher

A tool that detects stale documentation by watching git diffs.

## Installation

Install using pip:

    pip install docwatcher

## validate_token

The validate_token function checks if a given token is valid.
It takes a token string and returns True if valid, False otherwise.

## AuthService

The AuthService class handles all authentication logic.
Use the login method to authenticate a user with username and password.

## get_changed_files

The get_changed_files function scans a git repository and returns
a list of all files that have been modified since the last commit.
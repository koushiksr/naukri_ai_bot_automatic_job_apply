#!/usr/bin/env python3
"""
Naukri Automated Job Application Bot
Main entry point - Run this to start the bot
"""

import sys
import os

# Add src to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import main as bot_main

if __name__ == "__main__":
    bot_main.main()

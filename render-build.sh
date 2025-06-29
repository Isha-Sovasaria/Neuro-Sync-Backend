#!/usr/bin/env bash

# Install ffmpeg for audio processing
apt-get update && apt-get install -y ffmpeg

# Then install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
# mp3-manager

A terminal tool for managing a personal MP3 library. It runs as a simple
numbered menu that walks you through importing, tagging, organizing and
syncing your music.

## Features

- **Import downloads** – strip download-site prefixes from filenames and
  rename tracks to `Title - Artist` from their ID3 tags.
- **Genre prefixes** – tag filenames with a one-letter genre code (defined in
  your config) so they sort by category.
- **Edit metadata** – view and change title / artist / album / track number,
  or rename a file directly.
- **Album import** – search your downloaded albums and pick which tracks to
  pull into your library.
- **Album covers** – extract and re-embed cover art with ffmpeg.
- **Sync** – copy tracks between your working folders and a USB drive.

## Requirements

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/) installed and on your `PATH` (used for cover art)
- Python packages:

```bash
pip install -r requirements.txt
```

## Setup

The tool reads your folder locations from a `config.json` file. Copy the
example and fill in your own paths

- **all_dir** contains all of your mp3 songs
- **current_dir** has the songs you want to move to usb
- **temp_dir** is where you put newly downloaded songs
- **usb_dir** is the path to your USB (ex: "D:\")
- **albums_dir** is where albums are stored

## Usage

```bash
python mp3_manager.py
```

Then follow the numbered menu.

## License

MIT

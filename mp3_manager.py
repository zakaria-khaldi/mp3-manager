"""Music Editor - a terminal menu for organizing an MP3 library."""
from mutagen.easyid3 import EasyID3
import subprocess
import pyperclip
import shutil
import json
import os

def print_title():
    print("""
    __  ___           _         ______    ___ __            
   /  |/  /_  _______(_)____   / ____/___/ (_) /_____  _____
  / /|_/ / / / / ___/ / ___/  / __/ / __  / / __/ __ \/ ___/
 / /  / / /_/ (__  ) / /__   / /___/ /_/ / / /_/ /_/ / /    
/_/  /_/\__,_/____/_/\___/  /_____/\__,_/_/\__/\____/_/     
                                                             
""")
    
def clear_output():
    os.system("cls" if os.name == "nt" else "clear")
    print_title()

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "config.json"), "r") as g:
    cfg = json.load(g)


### VARS ###
all_dir     = cfg["all_dir"]
current_dir = cfg["current_dir"]
temp_dir    = cfg["temp_dir"]
usb_dir     = cfg["usb_dir"]
albums_dir  = cfg["albums_dir"]
prefixes_dict = cfg["prefixes"]




# Remove the "SpotiDownloader.com - " prefix from a downloaded file.
def remove_watermark(file):
    filepath = os.path.join(temp_dir, file)
    prefixes = ["SpotiDownloader.com - "]
    for prefix in prefixes:
        if os.path.basename(file)[:len(prefix)] in prefixes:
            new_filename = os.path.basename(file)[len(prefix):]
            new_filepath = os.path.join(temp_dir, new_filename)
            os.rename(filepath, new_filepath)
            print("Removed prefix for:", new_filename)


# Extract an MP3's album cover with ffmpeg, then re-embed it.
def extract_resize_covers(directory, file):
    file = os.path.basename(file)
    if file.lower().endswith(".mp3"):

        fullpath = os.path.join(directory, file)
        name = os.path.splitext(file)[0]
        cover_path = os.path.join(directory, f"{name}.jpg")
        temp_output = os.path.join(directory, f"{name}_temp.mp3")

        try:
            # 1. Try extracting cover
            extract = subprocess.run(
                ["ffmpeg", "-y", "-i", fullpath, "-an", "-vcodec", "copy", cover_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # If extraction failed → skip
            if extract.returncode != 0 or not os.path.exists(cover_path):
                print(f"[SKIP] {file} -> no cover or extraction failed")
                return

            # 2. Re-embed cover into temp file
            embed = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", fullpath,
                    "-i", cover_path,
                    "-map", "0:a",
                    "-map", "1",
                    "-c", "copy",
                    "-id3v2_version", "3",
                    "-metadata:s:v", "title=Album cover",
                    "-metadata:s:v", "comment=Cover (front)",
                    temp_output
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if embed.returncode != 0:
                print(f"[ERROR] {file} -> embed failed")
                return

            # 3. Replace original
            os.replace(temp_output, fullpath)

            # 4. Clean temp cover
            os.remove(cover_path)

            print(f"Resized cover for: {file}")
        except Exception as e:
            print(f"[ERROR] {file} -> {e}")



# Add a genre letter prefix (from the config list) to a filename.
def letter_prefix(directory= None, file= None, prefix= None):
    clear_output()
    if not os.path.exists(file):
        filepath = os.path.join(directory, file)
    else:
        filepath = file
    
    filename = os.path.basename(file)
    
    if os.path.isfile(filepath):
        if prefix == None:
            for i in prefixes_dict:
                print(i)
            prefix = input(f"\nPrefix for {filename}: ")
        if prefix == "":
            new_filename = filename[2:]
            return new_filename
        if prefix == "ya":
            prefix = "Я"
        
        if filename[1] == "-":
            new_filename = prefix + filename[1:]
        else:
            new_filename = f"{prefix}-{filename}"
        
        new_filepath = os.path.join(directory, new_filename)
        os.rename(filepath, new_filepath)
        print(f"{filename} has been renamed to {new_filename}\n")
    
    return new_filepath



# Copy every file and subfolder from one folder into another.
def copy_folder_contents(source_folder, destination_folder):
    
    os.makedirs(destination_folder, exist_ok=True)
    source_contents = os.listdir(source_folder)
    
    for item in source_contents:
        item_path = os.path.join(source_folder, item)
    
        if os.path.isdir(item_path):
            destination_item_folder = os.path.join(destination_folder, item)
            os.makedirs(destination_item_folder, exist_ok=True)
            shutil.copytree(item_path, destination_item_folder, dirs_exist_ok=True)

        elif os.path.isfile(item_path):
            shutil.copy(item_path, destination_folder)
    print(f"Files in {source_folder} have been moved to {destination_folder}")



# Read an MP3's ID3 tags and return them as a dict.
def give_metadata(filepath):
    audio = EasyID3(filepath)
    song_metadata = {
        "title": audio.get("title", [None])[0],
        "artist": audio.get("artist", [None])[0],
        "album": audio.get("album", [None])[0],
        "tracknumber": audio.get("tracknumber", [None])[0]
        }
    return audio, song_metadata



# Rename a song. "mode" picks how: free text, title-artist, live, or album.
def rename_song(filepath, data = None, mode=["free", "title-artist", "live", "album"]):       #data = prefix for mode = "album"
    extension = os.path.splitext(filepath)[1].lower()
    directory = "\\".join(filepath.split("\\")[:-1])
    
    if mode == "free":
        clear_output()
        new_filename = input("Enter new filename: ")
    
    if mode == "title-artist":
        if data["title"] == None or data["artist"] == None:
            return None
        new_filename = f"{list(data.values())[0]} - {list(data.values())[1].split('/')[0]}"

    if mode == "live":          #data = audio
        clear_output()
        artist = input("Enter the artist's name: ")
        data["artist"] = artist
        city = input("Enter the city: ")
        year = input("Enter the year: ")
        new_title = f"{artist} {city} Live {year}"
        data["title"] = [new_title]
        data["artist"] = [artist]
        data["album"] = ["Live Concert"]
        data.save()
        new_filepath = os.path.join(directory, ("L-" + new_title + extension))

    if mode == "album":
        shortalbumname = ""
        for word in filepath.split("\\")[-2].split(" "):
            shortalbumname = shortalbumname + word[0]
        
        _, song_metadata = give_metadata(filepath)
        
        new_filename = f'{data}-{shortalbumname} {song_metadata["tracknumber"].split("/")[0]} {song_metadata["title"]}{extension}'          #data = prefix
        new_filepath =  os.path.join(current_dir, new_filename)
        return new_filepath

    new_filepath = f"{os.path.join(directory, new_filename)}{extension}"
    os.rename(filepath, new_filepath)
    return new_filepath



main_actions = ["New Files", "Copy to All & Current", "Copy to USB", "Edit Metadata", "Add songs from Downloaded Albums", "Correct all covers"]

# Show the main menu and run the chosen action in a loop.
def main():
    while True:
        
        pyperclip.copy(temp_dir)
        clear_output()
        print("\nWhat do you want to do ?\n")
        
        for index, i in enumerate(main_actions, start=1):
            print(f"{index}. {i}")

        action = None
        main_action_choice = int(input("\nEnter your choice: "))
        main_action_choice = main_action_choice - 1
        action = main_actions[main_action_choice]
        prefix = None

        while True:

            if action == "New Files":
                clear_output()

                title_artist_choice = input('Send "y" to rename songs as "title - artist": ')
                for file in os.scandir(temp_dir):
                    filepath = os.path.join(temp_dir, os.path.basename(file))
                    remove_watermark(file)
                    #extract_resize_covers(temp_dir, file)
                    audio, song_metadata = give_metadata(filepath)
                    try:
                        new_filepath = rename_song(filepath, data=song_metadata, mode="title-artist")
                    except Exception as e:
                        print(e)

                clear_output()

                if input('Send "y" to choose the same prefix for all files in folder: ') == "y":
                    clear_output()
                    for i in prefixes_dict:
                        print(i)
                    prefix = input("\nEnter global prefix letter: ")
                for file in os.scandir(temp_dir):
                    letter_prefix(temp_dir, file, prefix)
                break


            if action == "Copy to All & Current":
                clear_output()
                copy_folder_contents(temp_dir, current_dir)
                copy_folder_contents(temp_dir, all_dir)
                for file in os.scandir(temp_dir):
                    if file.is_file():
                        os.remove(file)
                print("All files have been moved")
                return


            if action == "Copy to USB":
                clear_output()
                if input("Do you want to clear USB ? (yes / Enter) ") == "yes":
                    for file in os.scandir(usb_dir):
                        filepath = os.path.join(usb_dir, file)
                        if filepath.endswith("mp3"):
                            os.remove(filepath)

                clear_output()
                print("Copying files from Current folder to USB folder")
                copy_folder_contents(current_dir, usb_dir)
                return

            if action == "Edit Metadata":
                clear_output()
                print("1. all_dir")
                print("2. temp_dir")
                directory = int(input("\nChoose directory: "))

                if directory == 1:
                    directory = all_dir
                
                if directory == 2:
                    directory = temp_dir

                while True:
                        files = []  
                        for file in os.scandir(dir):
                            files.append(os.path.join(directory, os.path.basename(file)))
                        
                        clear_output()
                        for index, file in enumerate(files, start=1):
                            print(f"{index}. {os.path.basename(file)}")
                        print(f"{index + 1}. Previous Menu")
                        filechoice = int(input("\nEnter your choice: "))
                        if filechoice == index + 1:
                            break
                        filechoice = files[filechoice - 1]
                        filechoice = os.path.basename(filechoice)
                        filepath = os.path.join(directory, filechoice)
                        
                        while True:

                            clear_output()
                            audio, song_metadata = give_metadata(filepath)
                            print("What metadata do you want to edit ?\n")
                            for index, (field, value) in enumerate(song_metadata.items(), start=1):
                                print(f"{index}. {field}: {value}")
                            print(f"{index + 1}. filename: {os.path.basename(filepath)}")
                            print(f"\n{index + 2}.", "Add prefix")
                            print(f"{index + 3}.", "Rename file as: {title} - {artist}")
                            print(f"{index + 4}.", "Rename file as: live concert")
                            print(f"9.", "Previous Menu")
                            
                            metadata_choice = int(input("\n\rEnter your choice: "))

                            if metadata_choice == index + 2:
                                filepath = letter_prefix(directory, filepath)
                            
                            if metadata_choice == index + 1 or metadata_choice == index + 3:
                                extension = os.path.splitext(filepath)[1].lower()
                                
                                if metadata_choice == index + 1:
                                    clear_output()
                                    new_filename = input("Enter new filename: ")
                                if metadata_choice == index + 3:
                                    new_filename = f"{list(song_metadata.values())[0]} - {list(song_metadata.values())[1].split('/')[0]}"
                                
                                new_filepath = os.path.join(directory, new_filename) + extension
                                os.rename(filepath, new_filepath)
                                filepath = new_filepath

                            if metadata_choice == index + 4:
                                clear_output()
                                extension = os.path.splitext(filepath)[1].lower()
                                artist = input("Enter the artist's name: ")
                                audio["artist"] = artist
                                city = input("Enter the city: ")
                                year = input("Enter the year: ")
                                new_title = f"{artist} {city} Live {year}"
                                audio["title"] = [new_title]
                                audio["artist"] = [artist]
                                audio["album"] = ["Live Concert"]
                                audio.save()
                                new_filepath = os.path.join(directory, ("L-" + new_title + extension))
                                os.rename(filepath, new_filepath)
                                filepath = new_filepath
                                
                            
                            if metadata_choice == 9:
                                break

                            if metadata_choice <= index:
                                clear_output()
                                metadata_key = list(song_metadata.keys())[metadata_choice - 1]
                                metadata = list(song_metadata.values())[metadata_choice - 1]
                                pyperclip.copy(metadata)
                                print(f"Current {metadata_key}: {metadata}")
                                new_metadata = input(f"New {metadata_key}: ")
                                audio[metadata_key] = [new_metadata]
                                audio.save()


            if action == "Add songs from Downloaded Albums":
                clear_output()
                while True:

                    albums = []
                    for album in os.scandir(albums_dir):
                        albums.append(album)
                    
                    searched_albums = []

                    clear_output()
                    search = input("Search for your album: ")
                    clear_output()
                    if search == "":
                        searched_albums = albums
                    else:
                        for album in albums:
                            if search.lower() in album.name.lower():
                                searched_albums.append(album)

                    for index, album in enumerate(searched_albums, start = 1):
                        print(f"{index}.", album.name)
                    print(f"{index + 1}. Previous Menu")

                    album = int(input("\nEnter your choice: "))
                    if album == index + 1:
                        break
                    album = searched_albums[album - 1]
                    
                    album_path = os.path.join(albums_dir, album)
                    songs = {}
                    clear_output()
                    
                    for song in os.scandir(album_path):
                        song_path = os.path.join(album_path, song)
                        audio, song_metadata = give_metadata(song_path)
                        songs[int(song_metadata.get("tracknumber").split("/")[0])] = song.name
                        
                    songs = dict(sorted(songs.items()))
                    
                    print("0. All songs")
                    for tracknumber, song in songs.items():
                        print(f"{tracknumber}. {song[:-4]}")
                    print(f"{tracknumber + 1}. Previous Menu")
                    
                    songs_to_move = list(map(int, input("\nEnter tracknumbers of songs you want to move: ").split()))
                    if tracknumber + 1 in songs_to_move:
                        break
                    prefix = "X" + input("Enter the desired album prefix: ")

                    if songs_to_move[0] == 0:
                        songs_to_move = []
                        for i in range(1, len(songs)):
                            songs_to_move.append(i)

                    for tracknumber in songs_to_move:
                        filepath = os.path.join(album_path, songs.get(tracknumber))
                        new_filepath = rename_song(filepath=filepath, data=prefix, mode = "album")
                        shutil.copy2(filepath, new_filepath)
        

            if action == "Correct all covers":
                for file in os.scandir(current_dir):
                    extract_resize_covers(current_dir, file)
                return

main()
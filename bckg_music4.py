#Project | Background music player | Soszka Maria, Kowalski Jakub, Sowiński Rafał | 12.06.2024
#Based on achudnova's player: github.com/achudnova/projects-yt/tree/main/MusicPlayer
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.ttk import Progressbar
import customtkinter as ctk
from mutagen.mp3 import MP3
import threading
import getpass
import pygame
import time
import os
import paho.mqtt.client as mqtt
import queue

# Initialize pygame mixer
pygame.mixer.init()

# Store the current position, song duration, and some booleans of the music
current_position = 0
song_duration = 0.00
song_change = False
paused = False
selected_folder_path = "" # Store the selected folder path
message_queue = queue.Queue()

#broker and topic for mqtt
broker = 'localhost'
topic = 'mp3/pilot'

#mqtt connection and message handlers
def on_connect(client, userdata, flags, rc):
	print("Connected with result code " + str(rc))
	client.subscribe(topic)
	
def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print(f"Received message: {message}")
    message_queue.put(message)

#mqtt client thread
def start_mqtt_loop():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, 1884, 60)
    client.loop_forever()
    
#queue for controlling main process with messages from mqtt
def process_queue():
    while not message_queue.empty():
        message = message_queue.get()
        if message == 'resume':
            play_music()
        elif message == 'pause':
            pause_music()
        elif message == 'next':
            next_song()
        elif message == 'prev':
            previous_song()
        elif message == 'load':
            find_sound_files()
    window.after(100, process_queue)

#progress bar update
def update_progress():
    global current_position
    while True:
        if pygame.mixer.music.get_busy() and not paused:
            current_position = pygame.mixer.music.get_pos() / 1000
            pbar["value"] = current_position
            # Check if the current song has reached its maximum duration
            if current_position >= pbar["maximum"]:
                stop_music() # Stop the music playback
                next_song()
                pbar["value"] = 0 # Reset the pbar
            
            window.update()
        time.sleep(0.1)

#song length and time passed counters
def update_song_len():
    global song_duration, song_change, current_position
    curr_s_dur_sec = 0
    curr_s_dur_min = 0
    while True:
        if pygame.mixer.music.get_busy() and not paused:
            
            s_dur_min = song_duration//60
            s_dur_sec = song_duration - 60*s_dur_min
            song_len_text.set(f"{int(s_dur_min)}"+":"+f"{int(s_dur_sec):02}")
            window.update()
            curr_s_dur_sec += 1
            curr_s_dur_min = current_position//60
            curr_s_dur_sec = current_position - 60*curr_s_dur_min
            curr_song_len_text.set(f"{int(curr_s_dur_min)}"+":"+f"{int(curr_s_dur_sec):02}")
        time.sleep(1)
        

# Create a thread to update the progress bar
pt = threading.Thread(target=update_progress)
pt.daemon = True
pt.start()

# Create a thread to update song length timers
song_len_thread = threading.Thread(target=update_song_len)
song_len_thread.daemon = True
song_len_thread.start()
    
# Find all usb paths
def find_all_folders(path):
    folders = []
    all_dirs = os.listdir(path)
    for folder_name in all_dirs:
        if os.path.isdir:
            folders.append(os.path.join(path, folder_name))
    return folders

# Find every mp3 file across all usb paths
def find_sound_files():
    global full_paths
    full_paths = []
    lbox.delete(0, tk.END)
    media_path = "/media/" + getpass.getuser()
    usb_paths = find_all_folders(media_path)
    for path in usb_paths:
        usb_files = os.listdir(path)
        for file_name in usb_files:
            if file_name.endswith('.mp3'):
                full_paths.append(os.path.join(path, file_name))
                lbox.insert(tk.END, file_name)
    lbox.selection_set(0)
    lbox.see(0)
    play_selected_song()
    return 0

def previous_song():
    global song_change
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        song_change = True
        if current_index > 0:
            lbox.selection_clear(0, tk.END)
            lbox.selection_set(current_index - 1)
            play_selected_song()
        else:
            lbox.selection_clear(0, tk.END)
            lbox.selection_set(lbox.size() - 1)
            play_selected_song()

def next_song():
    global song_change
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        song_change = True
        if current_index < lbox.size() - 1:
            lbox.selection_clear(0, tk.END)
            lbox.selection_set(current_index + 1)
            play_selected_song()
        else:
            lbox.selection_clear(0, tk.END)
            lbox.selection_set(0)
            play_selected_song()

def play_music():
    global paused
    if paused:
        # If the music is paused, unpause it
        pygame.mixer.music.unpause()
        paused = False
    else:
        # If the music is not paused, play the selected song
        play_selected_song()

def play_selected_song():
    global current_position, paused, song_change, song_duration
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        selected_song = lbox.get(current_index)
        full_path = full_paths[current_index] #Change full path to currently selected song's
        pygame.mixer.music.load(full_path) # Load the selected song
        if song_change:
            pygame.mixer.music.play(start=0) # Play the song from the beginning
        else:
            pygame.mixer.music.play(start=current_position) # Play the song from the current position
        paused = False
        audio = MP3(full_path)
        song_duration = audio.info.length
        pbar["maximum"] = song_duration # Set the maximum value of the pbar  to the song duration

def pause_music():
    global paused
    # Pause the currently playing music
    pygame.mixer.music.pause()
    paused = True

def stop_music():
    global paused
    # Stop the currently playing music and reset the progress bar
    pygame.mixer.music.stop()
    paused = False
    
#create a mqtt client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, 1884, 60)

#Create a thread to receive mqtt messages
mqtt_thread = threading.Thread(target=client.loop_forever)
mqtt_thread.daemon = True
mqtt_thread.start()

# Create the main window
window = tk.Tk()
window.title("Music Player App")
window.geometry("800x600")
window.attributes('-fullscreen', True)

# Create variables storing time counters
song_len_text = tk.StringVar()
song_len_text.set(f"{int(0)}"+":"+f"{int(0):02}")

curr_song_len_text = tk.StringVar()
curr_song_len_text.set("0:00")

# Create a label for the music player title
l_music_player = tk.Label(window, text="Music Player", font=("TkDefaultFont", 30, "bold"))
l_music_player.pack(pady=10)

# Create a listbox to display the available songs
lbox = tk.Listbox(window, width=50, font=("TkDefaultFont", 16))
lbox.pack(pady=10)

# Create a button to load all music files
btn_load_music_files = ctk.CTkButton(window, text="Load Music Files", command=find_sound_files, font=("TkDefaultFont", 18))
btn_load_music_files.pack(pady=20)

# Create a frame to hold the control buttons
btn_frame = tk.Frame(window)
btn_frame.pack(pady=20)

# Create a button to go to the previous song
btn_previous = ctk.CTkButton(btn_frame, text="<", command=previous_song,
                            width=50, font=("TkDefaultFont", 18))
btn_previous.pack(side=tk.LEFT, padx=5)

# Create a button to play the music
btn_play = ctk.CTkButton(btn_frame, text="▶️", command=play_music, width=50,
                         font=("TkDefaultFont", 18))
btn_play.pack(side=tk.LEFT, padx=5)

# Create a button to pause the music
btn_pause = ctk.CTkButton(btn_frame, text="||", command=pause_music, width=50,
                          font=("TkDefaultFont", 18))
btn_pause.pack(side=tk.LEFT, padx=5)

# Create a button to go to the next song
btn_next = ctk.CTkButton(btn_frame, text=">", command=next_song, width=50,
                         font=("TkDefaultFont", 18))
btn_next.pack(side=tk.LEFT, padx=5)

#Create a frame containing progress bar and counters
pbar_frame = tk.Frame(window)
pbar_frame.pack(pady = 10)

#Current time counter
curr_song_len = tk.Label(pbar_frame, textvariable=curr_song_len_text, font=("TkDefaultFont", 12))
curr_song_len.pack(side=tk.LEFT, padx = 5)

# Create a progress bar to indicate the current song's progress
pbar = Progressbar(pbar_frame, length=300, mode="determinate")
pbar.pack(side=tk.LEFT, padx=5)

#Song length counter
song_len = tk.Label(pbar_frame, textvariable=song_len_text, font=("TkDefaultFont", 12))
song_len.pack(side=tk.LEFT, padx = 5)

# Queue processing 
window.after(100, process_queue)

window.mainloop()

# Background Music Player

Background music player project made for a uni course.

## About & features

- Searches for all .mp3 files in all usb drive paths (UNIX systems)
- GUI includes:
  1. Progress bar
  2. Current track time and entire track duration time
  3. Navigation panel
  4. Navigation on-screen buttons
- Remote control via MQTT (requires a broker)
- Based on github.com/achudnova/projects-yt/tree/main/MusicPlayer

## Technologies

- Python
- MQTT
- Raspberry Pi

## Installation

1. Clone the repo
  ```bash
   git clone https://github.com/arthel37/bckg_music_player
   ```
2. Set up the MQTT broker or comment out line 210
3. Enjoy

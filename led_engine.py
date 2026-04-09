import time
import threading
from colorsys import hsv_to_rgb
import serial
import numpy as np
from mss import mss


class LEDEngine:                                                                            # Engine manages LED data, audio input, and  comms with the ESP32
    def __init__(self):
        self.current_preset = {}                                                            # Holds settings like color, mode, etc
        self.running = False                                                                # Whether or not the engine is running / updating LEDs
        self.animation_step = 0                                                             # Used for animations (starts at time/frame 0 by default)
        self.zone_output = []                                                               # Color data per ZONE (average color)
        self.led_output = []                                                                # List with one color per LED, final list of colors sent to strip

        self.left_count = 22                                                                # Number of LED's on the left side of my monitor
        self.top_count = 47                                                                 # Number of LED's on the top side of my monitor
        self.right_count = 19                                                               # Number of LED's on the right side of my monitor
        self.bottom_count = 45                                                              # Number of LED's on the bottom side of my monitor

        self.total_leds = (                                                                 # Total LED number calculated from above values
            self.left_count +
            self.top_count +
            self.right_count +
            self.bottom_count
        )

        self.serial_port = None                                                             # Holds connection object (serial port lets program talk to ESP32) for example serial_port.write()
        self.port_name = "COM3"                                                             # Where ESP32 is plugged in
        self.baud_rate = 115200                                                             # How fast data is sent over connection, 115200 is a standard serial communication speed of 115200 bits per second

        self.audio_level = 0.0                                                              # How loud is the audio at x moment?
        self.smoothed_audio_level = 0.0                                                     # If you used audio level directly, it would flicker like crazy so we have to smooth it

        self.loopback_mic = None                                                            # Captures PC audio
        self.audio_thread = None                                                            # Runs audio processing separately (going to be really shitty if don't use threading)
        self.audio_running = True                                                           # Controls whether audio loop keeps running
        self.audio_started = False                                                          # Prevents starting it twice
        self.sc = None                                                                      # Soundcard interface library handler

        self.connect_serial()                                                               # Opens connection to ESP32

    def connect_serial(self):                                                               # Opens serial connection from Python app to ESP32 so Python can send the LED data to it
        try:
            self.serial_port = serial.Serial(self.port_name, self.baud_rate, timeout=1)     # Creates serial connection object and stores in self.serial_port with port "COM3", baud rate of 115200
                                                                                            # (CONT.) and waits up to 1 second for serial reads before giving up
                                                                                            # (CONT 2.) Once it is a serial connection object you can do serial_port.write, .read, .close, etc.
            time.sleep(2)                                                                   # Pauses program for 2 seconds after opening serial connection to be safe in case ESP32 needs a moment
            print("Connected to serial:", self.port_name)                                   # Success message for connection
        except Exception as e:                                                              # If anything fails like COM3 doesn't exist or other error
            self.serial_port = None                                                       
            print("Could not connect to serial:", e)                                        # Fail message

    def start_system_audio(self):                                                           
        if self.audio_started:                                                              # If audio already started do nothing
            return

        try:
            import soundcard as sc                                                          # Souncard library gives access to speakers, microphones, loopback capture devices
            self.sc = sc                                                                    # Stores library in the object so don't need to re-import across methods

            default_speaker = self.sc.default_speaker()                                     # Asks system which speaker is the default one
            print("Default speaker:", default_speaker.name)                                 # Message that prints current defualt speaker

            self.loopback_mic = self.sc.get_microphone(                                     # Basically says give me a microphone-like object that captures whatever is being played through the default speaker
                                                                                            # (CONT.) It's called get_micrphone because the library uses same interface for capture devices even when source is loopback audio
                                                                                            # (CONT 2.) Loopback captures internal system audio like Youtube, Spotify, etc. while normal microphone captures external audio like your voice
                default_speaker.name,
                include_loopback=True
            )

            print("Loopback device:", self.loopback_mic.name)                                # Message that prints current loopback device

            self.audio_thread = threading.Thread(target=self.audio_loop)                     # Creates new thread object to deal with audio loop
            self.audio_thread.daemon = True                                                  # Marks thread as daemon thread which means it automatically stops when program exits
            self.audio_thread.start()                                                        # Start new thread

            self.audio_started = True                                                        # Now that thread is active, mark audio as active
            print("System audio loopback started")                                           # Success message that setup worked and audio process is running

        except Exception as e:                                                               # If anything fails go here
            self.loopback_mic = None                                                         # Set loopback device to none
            print("Could not start system audio loopback:", e)                               # Error message that loopback couldn't be started

    def audio_loop(self):                                                                    # Function that repeatedly records tiny chunks of system audio and converts them into a single loudness number
                                                                                             # (CONT.) and stores number in self.audio_level
        if self.loopback_mic is None:                                                        # Checks if valid loopback device was found
            return

        try:
            with self.loopback_mic.recorder(samplerate=48000) as recorder:                   # Creates an object that can read audio samples from loopback device
                                                                                             # (CONT.) When you use "with" you don't need to close/release the recorder when it's done
                                                                                             # (CONT. 2) 48,000 samples per second, 48,000 kHz is very common standard
                while self.audio_running:                                                    # Keep processing audio while audio_running = True
                    data = recorder.record(numframes=1024)                                   # Asks recorder for 1024 frames of audio and store them in data
                                                                                             # (CONT.) 1024 is common chunk size (about 21 milliseconds of audio per chunk)

                    if data is None or len(data) == 0:                                       # Checks whether recording got any usable audio data
                        continue                                                             # "Continue" skips the rest of the loop and goes to next iteration to try again

                    if len(data.shape) > 1:                                                  # If audio has more than one dimension, it probably has multiple channels
                                                                                             # (CONT.) data is a NumPy array and .shape tells its dimensions
                                                                                             # (CONT. 2) A mono audio data.shape might look like (1024, ) which means one dimension with 1024 audio values
                                                                                             # (CONT. 3) A stereo data.shape might look like (1024, 2) with 1024 frames and 2 channels per frame (left and right)
                        samples = np.mean(data, axis=1)                                      # If stereo, it averages the channels together for each frame (axis = 1 is the channel number dimension)
                    else:
                        samples = data                                                       # If mono, no conversion needed because it's already a single channel

                    volume = np.sqrt(np.mean(samples ** 2))                                  # Does something called a root-mean-square which is a standard way to measure the strength of an audio signal
                                                                                             # (CONT.) RMS is useful for this project because it gives a stable, meaningful loudness value from a chunk of audio
                                                                                             # (CONT. 2) which is useful for things like brightness scaling
                    self.audio_level = float(volume)                                         # Stores computed loudness in the engine                   

        except Exception as e:                                                               # If any errors go here
            print("System audio capture error:", e)                                          # Audio capture error message

    def update_preset(self, preset_data):                                                    # Stores new settings for LED effect (updates current effect settings used by engine)
        self.current_preset = preset_data

    def start(self):                                                                         # Prevents engine starting twice
        if self.running:                                                                     # If already running, ignore rest
            return

        self.running = True                                                                  # Set engine to running
        print("Engine started")                                                              # Engine start success message

        self.thread = threading.Thread(target=self.run_loop)                                 # Starts new thread that handles run_loop method
        self.thread.daemon = True                                                            # Marks thread as daemon thread which means it automatically stops when program exits
        self.thread.start()                                                                  # Start new thread

    def stop(self):                                                                          # Stops loop by setting running to false
        self.running = False                                                                 # Set running state to false
        print("Engine stopped")                                                              # Engine stopped success message

    def run_loop(self):                                                                      # Loop for the main update cycle
        while self.running:                                                                  
            self.render_frame()                                                              # Call function that actually makes LED's change
            time.sleep(0.05)                                                                 # Pause 0.05 seconds between frames (~ 20 times per second)

    def render_frame(self):                                                                  # Function builds one complete LED frame based on selected preset
        if not self.current_preset:                                                          # Don't render if no preset exists
            return

        mode = self.current_preset.get("mode", "Solid")                                      # .get is saying if "mode" exists in self.current_preset, use that value, otherwise use "Solid"
        brightness = self.current_preset.get("brightness", 128)                              # .get is saying if "brightness" exists in self.current_preset, use that value, otherwise use "128"
        speed = self.current_preset.get("speed", 50)                                         # .get is saying if "speed" exists in self.current_preset, use that value, otherwise use "50"
        smoothing = self.current_preset.get("smoothing", 50)                                 # .get is saying if "smoothing" exists in self.current_preset, use that value, otherwise use "50"
        zone_count = self.current_preset.get("zone_count", 8)                                # .get is saying if "zone_count" exists in self.current_preset, use that value, otherwise use "8"

        primary_hex = self.current_preset.get("primary_color", "#ffffff")                  # .get is saying if "primary_hex" exists in self.current_preset, use that value, otherwise use "#ffffff"
        secondary_hex = self.current_preset.get("secondary_color", "#000000")              # .get is saying if "secondary_color" exists in self.current_preset, use that value, otherwise use "#000000"

        if mode == "Audio Reactive" and not self.audio_started:                              # If the mode is audio-reactive and audio system hasn't been started then start it
            self.start_system_audio()

        zone_colors = []                                                                     # List for generated colors for each zone for this frame

        if mode == "Solid":                                                                  # Checks if mode is "Solid"
            base_color = self.hex_to_rgb(primary_hex)                                        # Converts primary hex color into RGB tuple which is assigned to every zone

            for i in range(zone_count):                                                      # Loops through all zones
                zone_colors.append(base_color)                                               # Changes zone_color to base_color

        elif mode == "Rainbow":                                                              # Checks if mode is "Rainbow"
            self.animation_step += max(1, speed * 0.1)                                       # Moves animation forward every frame, ensures it advances by at least 1 even if speed is very low
                                                                                             # (CONT.) max(1, speed * 0.1) means use whichever is bigger, 1, or (speed * .1)

            color1 = self.hex_to_rgb(primary_hex)                                            # Converts the two preset colors into RGB tuples
            color2 = self.hex_to_rgb(secondary_hex)

            for i in range(zone_count):                                                     
                t = ((self.animation_step + i * 20) % 360) / 360.0                          # for each zone, compute a blend amount between 0.0 and 1.0 (t is interpolation factor to mix between the two colors)
                                                                                            # (CONT.) i * 20 offsets each zone 20 units of the 360 unit animation cycle so neighboring zones are at different points in the gradient, without this all zones would have same color
                                                                                            # (CONT. 2) % 360 wraps the value around so it cycles continuously
                                                                                            # (CONT 3.) / 360 normalizes the result into a fraction from 0.0 to 1.0, so t becomes a blend percentage
                                                                                            # (CONT. 4) the i * 20 just means that each zone is slightly ahead in the color cycle compared to the previous one
                r = int(color1[0] + (color2[0] - color1[0]) * t)                            
                g = int(color1[1] + (color2[1] - color1[1]) * t)                            # Linearly blends from color1 to color2
                b = int(color1[2] + (color2[2] - color1[2]) * t)                            # (CONT.) if color1 = (255, 0, 0) and color2 = (0, 0, 255) and t = 0.5
                                                                                            # (CONT 2.) then r becomes halfway from 255 to 0 = 127, g stays 0, and b becomes halfway from 0 to 255 = 127
                                                                                            # (CONT 3.) which results in (127, 0, 127)

                zone_colors.append((r, g, b))                                               # Add this zone color to output list

        elif mode == "Audio Reactive":                                                      # Checks if mode is audio reactive
            primary_color = self.hex_to_rgb(primary_hex)                                    # Convert preset colors to RGB
            secondary_color = self.hex_to_rgb(secondary_hex)

            target_audio = min(1.0, self.audio_level * 20)                                  # Takes measured audio level and scales it up, caps it at 1.0
                                                                                            # (CONT.) Multiplied by 20 because raw RMS audio values are usually small decimals
                                                                                            # (CONT. 2) min(1.0) prevents it from exceeding intended 0 - 1 range

            self.smoothed_audio_level = (                                                   # Smooths audio level so effect doesn't jitter with every little fluctuation
                self.smoothed_audio_level * 0.7 +                                           # Keep 70% of the old smoothed value
                target_audio * 0.3                                                          # Add 30% of the new target
            )

            self.animation_step += max(1, speed * 0.1)                                      # Moves animation forward every frame, ensures it advances by at least 1 even if speed is very low
                                                                                            # (CONT.) max(1, speed * 0.1) means use whichever is bigger, 1, or (speed * .1)
            pulse_center = (self.animation_step * 0.08) % zone_count                        # Moves a pulse around ring of zones, the  * .08 slows the movement down
                                                                                            # (CONT.) % zone_count wraps pulse position so it loops around the zones continuously
                                                                                            # (CONT 2.) so pulse_center is current center location of moving pulse
            pulse_width = 1.0 + self.smoothed_audio_level * max(2, zone_count / 3)          # Determines how wide the pulse is, starts at 1.0
                                                                                            # (CONT.) Louder audio increases the width, max(2, zone_count / 3) prevents wideth factor from being too tiny on small zone counts

            for i in range(zone_count):                                                     # Measures how far each zone is from pulse center
                distance = abs(i - pulse_center)                                            # Find how far zone is from pulse center
                                                                                            # (CONT.) i = current zone index, so abs(i - location of pulse) gives distance

                if distance > zone_count / 2:                                               # Needed for the wrap around, since the last zone and first zone are neighbors so it can wrap around back to start
                    distance = zone_count - distance                                        # (CONT.) Example is there's 8 zones, the pulse center is at 0.2, so for zone 7 distance = (7 - 0.2) = 6.8
                                                                                            # (CONT 2.) But this is misleading because zone 7 is actually right next to zone 0 around the loop
                                                                                            # (CONT 3.) So the actual distance is 8 - 6.8 = 1.2
                                                                                            # (CONT 4.) So the code says if the direct distance is more than halfway around the loop, use wrapped around distance instead
                                                                                            # (CONT 5.) In other words if the distance is greater than half the circle, then going the other way around the loop is shorter

                strength = max(0.0, 1.0 - (distance / pulse_width))                         # Distance / pulse width tells how far the zone is realtive to pulse size
                                                                                            # (CONT.) 1.0 - (...)  inverts it so that close zones get high strength and far zones get low strength which means they're less bright
                                                                                            # (CONT. 2) Basically it's less bright and closer to the background color the farther away from the pulse center
                strength *= self.smoothed_audio_level                                       # Multiplies the pulse strength by how strong the audio is 
                                                                                            # (CONT.) Without this, the pulse would move around but it would always be equally bright no matter what the audio is doing

                r = int(secondary_color[0] + (primary_color[0] - secondary_color[0]) * strength)    # Color interpolation that blends between the two colors
                g = int(secondary_color[1] + (primary_color[1] - secondary_color[1]) * strength)    # (CONT.) Performs the same blend separately for red, green, blue
                b = int(secondary_color[2] + (primary_color[2] - secondary_color[2]) * strength)    # (CONT 2.) it chooses a color somewhere between
                                                                                                    # (CONT 3.) Secondary color when strength is low and primary_color when strength is high
                                                                                                    # (CONT 4.) If strength was .25, you would get a color .25% of the way from secondary to primary

                zone_colors.append((r, g, b))                                               # Save this zone's computed color

        elif mode == "Screen Reactive":                                                     # Checks if mode is "Screen Reactive"
            zone_colors = self.get_screen_zone_colors(zone_count)                           # Call screen reactive function

        else:                                                                               # If mode not recognized
            base_color = self.hex_to_rgb(primary_hex)                                       # (CONT.) Just set to primary color

            for i in range(zone_count):
                zone_colors.append(base_color)

        brightness_scale = brightness / 255.0                                               # Turns brightness from 0 - 255 into 0.0 - 1.0
        zone_colors = [                                                                     # Apply brightness to every zone color
            (
                int(r * brightness_scale),                                                  # Multiplying all of them by the same brightness scale just outputs the same color but darker
                int(g * brightness_scale),                                                  # (CONT.) As long as the ratio is preserved between them it's the same color but darker
                int(b * brightness_scale)
            )
            for (r, g, b) in zone_colors                                                    # For all values r, g, and b in zone_colors list
        ]

        if len(self.zone_output) != zone_count:                                             # If user changes the number of zones or changes preset which has different number of zones, 
            self.zone_output = [(0, 0, 0)] * zone_count                                     # (CONT.) Reset stored zone output to correct size and fill it with black
                                                                                            # (CONT. 2) to start from nothing so indexing doesn't break

        new_output = []                                                                     # New smoothed output list

        for i in range(zone_count):                                                         # Smooth each zone from old color to new target
            current = self.zone_output[i]                                                   # Current is what zone was showing last frame
            target = zone_colors[i]                                                         # Target is what zone should show this frame
            smoothed = self.apply_smoothing(current, target, smoothing)                     # Blend between them (function definition for apply_smoothing at bottom)
                                                                                            # (CONT.) smoothed_audio_level smooths the loudness signal
                                                                                            # (CONT 2.) apply_smoothing smooths the visible output between frames
            new_output.append(smoothed)                                                     # Add smoothed output to new_output list
                                                                                            # LOOP: This loop runs the code once for each zone, it says "what color was this zone last frame?"
                                                                                            # (CONT.) then it says "what color should this zone be now?"
                                                                                            # (CONT 2.) then it says move a little bit from current -> target (not jump instantly)
                                                                                            # (CONT 3.) then save the smoothed color for this zone
                                                                                            # (CONT 4.) zone_output is what we are CURRENTLY showing after smoothing
                                                                                            # (CONT 5.) zone_colors is what we WANT this frame

        self.zone_output = new_output                                                       # Make smoothed output the new current zone state, next frame this becomes current and new target gets compared against it again
        self.led_output = self.map_zones_to_perimeter(self.zone_output)                     # Takes the smaller zone list and converts it into a full list of LED colors
                                                                                            # (CONT.) zone_output might have 8, 12, or whatever values, and led_output must have 133 values for my strip because I have 133 led's total
                                                                                            # (CONT. 2) So the zones have to become physical LED's
        self.send_leds()                                                                    # Transmits output to ESP32

    def get_screen_zone_colors(self, zone_count):                                           # Function that takes screenshot of monitor, looks at outer edges, splits them into zone_count chunks,
                                                                                            # (CONT.) finds the average color for each chunk, and returns them
        try:
            with mss() as sct:                                                              # mss is the screeenshot library, it opens a screenshot session so it can capture display
                if len(sct.monitors) < 2:                                                   # in mss monitor index 0 covers ALL monitors combined, index 1 and above represent individual monitors
                                                                                            # (CONT.) Checking if len(sct.monitors < 2) is just making sure at least one real monitor exists
                    return [(0, 0, 0)] * zone_count                                         # (CONT. 2) if one doesn't, return black for every zone

                monitor = sct.monitors[1]                                                   # Saves first real monitor as "monitor"
                shot = sct.grab(monitor)                                                    # Take a screenshot of the first real monitor and save raw screenshot as "shot"

            frame = np.array(shot)                                                          # Turns screenshot into NumPy array so it can be sliced/averaged easily
            frame = frame[:, :, :3]                                                         # (CONT.) Turns screenshot into 3D grid of numbers
                                                                                            # (CONT. 2) frame[height][width][channels] OR frame[row][column][color]
                                                                                            # (CONT. 3) for [:, :, :3], the first : says take all rows
                                                                                            # (CONT 4.) The second : says take all columns
                                                                                            # (CONT 5.) and the :3 says take channels from index 0 up to (but not including) 3
                                                                                            # (CONT. 6) For mss, the library returns the pixel data (the channels) in format [B, G, R, A]
                                                                                            # (CONT. 7) these are B = Blue, G = Green, R = Red, and A = Alpha (Transparency)
                                                                                            # (CONT. 8) We DON'T need Alpha (Transparency), so we don't include channel 3
                                                                                            # (CONT. 9) So before, frame.shape = (1080, 1920, 4) with each pixel [B,G,R,A]
                                                                                            # (CONT. 10) but now, frame.shape = (1080, 1920, 3) with each pixel [B,G,R]
            height, width, _ = frame.shape                                                  # Get screen size, unpack frame dimensions into height and width while ignoring channel count with _ as a placeholder

            left_zones = max(1, round(zone_count * self.left_count / self.total_leds))      # This is the code that decides how many zones each side gets
            top_zones = max(1, round(zone_count * self.top_count / self.total_leds))        # (CONT.) max(1,...) ensures each side gets at least one zone
            right_zones = max(1, round(zone_count * self.right_count / self.total_leds))
            bottom_zones = zone_count - left_zones - top_zones - right_zones

            if bottom_zones < 1:
                bottom_zones = 1

            while left_zones + top_zones + right_zones + bottom_zones > zone_count:         # Because of rounding, you can for example get a total of 9 zones if you only want 8, like left = 1, top = 3, right = 1, and bottom = 4
                                                                                            # (CONT.) This code will subtract zones until the total matches
                                                                                            # (CONT. 2) The priority order for which loses a zone is pretty arbitrary, but I've ordered it from most LED's -> least LED's
                                                                                            # (CONT. 3) This is just because sides with more LED's can "afford" to lose a zone

                if top_zones > 1:
                    top_zones -= 1
                elif bottom_zones > 1:
                    bottom_zones -= 1
                elif left_zones > 1:
                    left_zones -= 1
                elif right_zones > 1:
                    right_zones -= 1

            while left_zones + top_zones + right_zones + bottom_zones < zone_count:         # (CONT. 4) This handles the opposite case where the total zones comes out to less than you want
                top_zones += 1

            zone_colors = []                                                                # Starts an empty list that will hold final average color for each zone, at the end should contain zone_count colors

            for i in range(left_zones):                                                     # Divides left side of screen into vertical slices
                y1 = int(height - ((i + 1) / left_zones) * height)                          # (CONT.) y1 and y2 are top and bottom pixel boundaries of that slice
                y2 = int(height - (i / left_zones) * height)                                # (CONT 2.) 0:max(1, width // 20) means use only a thin strip on far left (grabs thin vert rectangle and finds avg color)
                region = frame[max(0, y1):min(height, y2), 0:max(1, width // 20)]           # (CONT 3.) frame[rows, columns] -> frame[y1:y2, x1:x2], y2 is always below y1
                zone_colors.append(self.average_region_color(region))                       # (CONT. 4) max(0, y1) says use y1 but never go below 0 (would be above the screen), min(height, y2) says use y2, but never go past the bottom of the screen (height)
                                                                                            # (CONT 5.) width // 20 means use use 1/20 of screen width (about 96 pixels on a 1920 pixel wide monitor)

            for i in range(top_zones):                                                      # Similar to above, x1 and x2 define horizontal bounadries
                x1 = int((i / top_zones) * width)                                           # 0:max(1, height // 20) means only use a thin strip at very top
                x2 = int(((i + 1) / top_zones) * width)
                region = frame[0:max(1, height // 20), max(0, x1):min(width, x2)]
                zone_colors.append(self.average_region_color(region))

            for i in range(right_zones):
                y1 = int((i / right_zones) * height)
                y2 = int(((i + 1) / right_zones) * height)
                region = frame[max(0, y1):min(height, y2), max(0, width - width // 20):width]   # width - width // 20 means only use thin strip at the far right
                zone_colors.append(self.average_region_color(region))

            for i in range(bottom_zones):
                x1 = int(width - ((i + 1) / bottom_zones) * width)
                x2 = int(width - (i / bottom_zones) * width)
                region = frame[max(0, height - height // 20):height, max(0, x1):min(width, x2)] # height - height // 20 means only use thin strip at very bottom
                zone_colors.append(self.average_region_color(region))

            return zone_colors                                                              # Returns list of colors (one per zone)

        except Exception as e:                                                              # If any errors, go here
            print("Screen capture error:", e)                                               # Error message
            return [(0, 0, 0)] * zone_count                                                 # Set all lights to black default

    def average_region_color(self, region):                                                 # Takes rectangular chunk of pixels in screenshot and turns into one color
        if region.size == 0:                                                                # Checks whether has any pixels at all, if not, nothing to average so return black
            return (0, 0, 0)

        avg = region.mean(axis=(0, 1))                                                      # region is 3D array with (region_height, region_width, 3) 
                                                                                            # (CONT.) height is rows of pixels, width is columns of pixels, 3 is three color channels BGR
                                                                                            # (CONT. 2) mean(axis=(0,1)) means average across rows and columns, keep color channels separate
                                                                                            # (CONT. 3) axis = 0 is rows, axis = 1 is columns
                                                                                            # (CONT. 4) instead of averaging everything into one number, average all blue together, all red together, all green together
                                                                                            # (CONT. 5) add averages to avg[] arrayu
        b = int(avg[0])                                                                     
        g = int(avg[1])                                                                     # Convert BGR averages to integers (LEDs need integer channel values)
        r = int(avg[2])

        return (r, g, b)                                                                    # Return them

    def send_leds(self):                                                                    # Takes finished per LED colors in self.led_output turns them into something it can send to ESP32
        if self.serial_port is None:                                                        # If no serial connection, exit
            return

        try:
            parts = []                                                                      # Will hold string for each individual LED (so a list of something like 255, 0, 0)

            for r, g, b in self.led_output:                                                 # Loops through every LED color in final output
                parts.append(f"{r},{g},{b}")                                                # Turns LED tuple into text string

            message = ";".join(parts) + "\n"                                                # Combines all strings into one long message separated by semicolons
                                                                                            # (CONT.) commas separate values within one LED, semicolons separate different LEDs
                                                                                            # (CONT. 2) once frame string is done, add new line as end of message marker
            self.serial_port.write(message.encode("utf-8"))                                 # Serial write expects bytes, not string, so have to encode to bytes

        except Exception as e:                                                              # If any error, go here
            print("Serial send error:", e)                                                  # Error message

    def map_zones_to_perimeter(self, zone_colors):                                          # Takes zone colors and turns them into LED colors
        led_colors = []                                                                     # Make list for led_colors, one RGB tuple each (for me it will be 133)

        left_zones = max(1, round(len(zone_colors) * self.left_count / self.total_leds))    # Decide how many zones belong to each side
        top_zones = max(1, round(len(zone_colors) * self.top_count / self.total_leds))      
        right_zones = max(1, round(len(zone_colors) * self.right_count / self.total_leds))

        bottom_zones = len(zone_colors) - left_zones - top_zones - right_zones

        if bottom_zones < 1:
            bottom_zones = 1

        while left_zones + top_zones + right_zones + bottom_zones > len(zone_colors):
            if top_zones > 1:
                top_zones -= 1
            elif bottom_zones > 1:                                                          # All the same logic as in get_screen_zone_colors ~line 301
                bottom_zones -= 1
            elif left_zones > 1:
                left_zones -= 1
            elif right_zones > 1:
                right_zones -= 1

        while left_zones + top_zones + right_zones + bottom_zones < len(zone_colors):
            top_zones += 1

        index = 0                                                                           # index for zone_colors list

        left_zone_colors = zone_colors[index:index + left_zones]                            # Grabs x amount of left_zone colors/tuples (x = how many zones on left)
        index += left_zones                                                                 # Increase index by how many left_zones there are to continue to top_zone colors

        top_zone_colors = zone_colors[index:index + top_zones]                              # Grabs x amount of top_zone colors/tuples (x = how many zones on top)
        index += top_zones                                                                  # Increase index by how many top_zones there are to continue to right_zone colors

        right_zone_colors = zone_colors[index:index + right_zones]                          # Grabs x amount of right_zone colors/tuples (x = how many zones on right)
        index += right_zones                                                                # Increase index by how many right_zones there are to continue to bottom_zone colors

        bottom_zone_colors = zone_colors[index:index + bottom_zones]                        # Grabs x amount of bottom_zone colors/tuples (x = how many zones on bottom)

        led_colors.extend(self.expand_side(left_zone_colors, self.left_count))              # Takes the side zone colors and LED count for that side and maps the correct colors to LEDs
        led_colors.extend(self.expand_side(top_zone_colors, self.top_count))
        led_colors.extend(self.expand_side(right_zone_colors, self.right_count))
        led_colors.extend(self.expand_side(bottom_zone_colors, self.bottom_count))

        return led_colors

    def expand_side(self, side_zone_colors, led_count):                                     # Takes the side zone colors and LED count for that side and maps the correct colors to LEDs
        side_leds = []                                                                      # List for this side's LEDs

        zone_count = len(side_zone_colors)                                                  # Grab side_zone_colors received from map_zones_to_perimeter

        if zone_count == 0:                                                                 # If side has no zones, return black LEDs on that side
            return [(0, 0, 0)] * led_count

        for led_index in range(led_count):                                                  # Go through each LED on this side one at a time
            zone_index = int((led_index / led_count) * zone_count)                          # (CONT.) Maps each LED to one of the available zones, gives LED's position as a fraction along the side
                                                                                            # (CONT. 2)For example if LED count = 10, LED 0 is 0 /10 = 0.0, LED 5 is 5/10 = 0.5, LED 9 is 9/10 = 0.9
                                                                                            # (CONT. 3) Convert fractional position into zone position
                                                                                            # (CONT. 4) For example, if 3 zones, 0.0 * 3 = 0.0, 0.5 * 3 = 1.5, 0.9 * 3 = 2.7
                                                                                            # (CONT. 5) Then, you do int() to floor them to integers, so 0.0 -> 0, 1.5 -> 1, 2.7 -> 2, which gives you zone index

            if zone_index >= zone_count:                                                    # Shouldn't happen, but safety guard if zone_index is greater than zone_count, subtract one from zone_count
                zone_index = zone_count - 1

            side_leds.append(side_zone_colors[zone_index])                                  # Add chosen zone's color for this LED, copies color of its assigned zone

        return side_leds                                                                    # Return full LED list for this side

    def hex_to_rgb(self, hex_color):                                                        # Converts hex color into RGB tuple
        hex_color = hex_color.lstrip("#")                                                   # Remove the #
        return (
            int(hex_color[0:2], 16),                                                        # First 2 characters are red, "ff8800" -> "ff"
            int(hex_color[2:4], 16),                                                        # Next 2 characters are green, "ff8800" -> "88"
            int(hex_color[4:6], 16)                                                         # Last 2 characters are blue, "ff8800" -> "00"
                                                                                            # The "16" is to convert from hexadecimal base-16 into decimal
        )

    def apply_smoothing(self, current_color, target_color, smoothing):                      # Moves current color partway toward target color instead of instantly jumping
        blend = max(0.01, min(1.0, (100 - smoothing) / 100.0))                              # Converts smoothing slider into blend fraction
                                                                                            # (CONT.) If smoothing is high, blend becomes small, and vice versa
                                                                                            # (CONT. 1) low smoothing -> fast transition, if high smoothing -> slow transition
                                                                                            # (CONT. 2) min(1.0, ...) prevents blend from ever going above 1.0
                                                                                            # (CONT. 3) max(0.01, ...) prevents blend from becoming 0 because it wouldn't move at al

        r = int(current_color[0] + (target_color[0] - current_color[0]) * blend)            # Take color channel and move it some fraction of way toward target color value
        g = int(current_color[1] + (target_color[1] - current_color[1]) * blend)            # EXAMPLE: if current_color = (100, 50, 0) and target color = (200, 150, 100) and blend = 0.25
        b = int(current_color[2] + (target_color[2] - current_color[2]) * blend)            # (CONT.) Then for red, 100 + (200 - 100) * .25 = 100 + 25 = 125
                                                                                            # (CONT. 2) For green, 50 + (150 - 50) * .25 = 50 + 25 = 75
                                                                                            # (CONT. 3) and for blue, 0 + (100 - 0) * .25 = 25
                                                                                            # (CONT. 4) Final color is (125, 75, 25) and new color is 25% of way toward target, then repeat process

        return (r, g, b)                                                                    # Return RGB
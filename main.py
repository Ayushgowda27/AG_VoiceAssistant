import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading
import queue
import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import pywhatkit
import webbrowser
import os

# Suppress macOS Tk warning
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
speech_lock = threading.Lock()

# Globals
update_queue = queue.Queue()
is_listening = False
stop_listening_flag = False

# --- Functions ---

# Text-to-speech (thread-safe)
def speak(text):
    def run():
        with speech_lock:
            engine.say(text)
            engine.runAndWait()
    threading.Thread(target=run).start()

# Display + Speak
def respond(text):
    speak(text)
    show_in_chat("AG Bot", text)

# Add text to chat GUI safely
def show_in_chat(role, text):
    update_queue.put(f"{role}: {text}")

# Periodically update GUI from thread queue
def process_gui_queue():
    try:
        while True:
            text = update_queue.get_nowait()
            chat_area.config(state='normal')
            chat_area.insert(tk.END, text + "\n")
            chat_area.see(tk.END)
            chat_area.config(state='disabled')
    except queue.Empty:
        pass
    window.after(100, process_gui_queue)

# Listen for voice command
def listen():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            respond("Listening...")
            print("[DEBUG] Listening from mic...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            try:
                command = recognizer.recognize_google(audio)
                command = command.lower()
                print("[COMMAND]", command)
                show_in_chat("You", command)
                return command
            except sr.UnknownValueError:
                print("[DEBUG] Could not understand")
                respond("Sorry, I didn't catch that.")
                return ""
            except sr.RequestError:
                respond("Speech service is down.")
                return ""
    except Exception as e:
        print("[ERROR] Mic error:", e)
        respond("Microphone is not working.")
        return ""

# Respond to recognized commands
def handle_command(command):
    print("[COMMAND RECEIVED]", command)

    if "time" in command:
        print("[DEBUG] Time command detected")
        time = datetime.datetime.now().strftime('%I:%M %p')
        respond(f"The time is {time}")

    elif "who is" in command:
        print("[DEBUG] Who is command detected")
        person = command.split("who is")[-1].strip()
        if not person:
            respond("Who exactly do you want to know about?")
            return
        try:
            info = wikipedia.summary(person, sentences=1)
            print("[DEBUG] Wikipedia result:", info)
            respond(info)
        except wikipedia.exceptions.DisambiguationError as e:
            print("[DEBUG] Disambiguation error:", e.options)
            respond(f"There are many results for {person}. Please be more specific.")
        except wikipedia.exceptions.PageError:
            respond(f"I couldn't find any info on {person}.")
        except Exception as e:
            print("[DEBUG] Unknown Wikipedia error:", e)
            respond("Sorry, I couldn't find that.")

    elif "play" in command:
        song = command.replace("play", "").strip()
        respond(f"Playing {song} on YouTube")
        pywhatkit.playonyt(song)

    elif "search" in command:
        query = command.replace("search", "").strip()
        respond(f"Searching for {query}")
        pywhatkit.search(query)

    elif "open google" in command:
        respond("Opening Google")
        webbrowser.open("https://www.google.com")

    elif "stop" in command or "exit" in command:
        respond("Goodbye!")
        window.quit()

    elif command != "":
        respond("Sorry, I can't do that yet.")

# Listening loop
def listen_and_respond():
    global is_listening
    command = listen()
    if command:
        handle_command(command)
    if stop_listening_flag:
        is_listening = False
        listen_btn.config(text="🎤 Start Listening")

# Toggle listening on button press
def start_listening():
    global is_listening, stop_listening_flag
    print("[DEBUG] Start/Stop Button Clicked")

    if not is_listening:
        print("[DEBUG] Starting listener...")
        is_listening = True
        stop_listening_flag = False
        listen_btn.config(text="🛑 Stop Listening")
        threading.Thread(target=continuous_listen, daemon=True).start()
    else:
        print("[DEBUG] Stopping listener...")
        stop_listening_flag = True
        is_listening = False
        listen_btn.config(text="🎤 Start Listening")
        respond("Stopped listening.")

# Looping voice response
def continuous_listen():
    while not stop_listening_flag:
        listen_and_respond()

# --- GUI Setup ---

window = tk.Tk()
window.title("AG Voice Assistant")
window.geometry("500x600")
window.config(bg="#222222")

chat_area = ScrolledText(window, wrap=tk.WORD, font=("Arial", 12))
chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
chat_area.config(state='disabled', bg="#1e1e1e", fg="white", insertbackground="white")

listen_btn = tk.Button(window, text="🎤 Start Listening", font=("Arial", 14),
                       bg="#333", fg="white", command=start_listening)
listen_btn.pack(pady=10)

# --- Launch App ---

respond("AG Voice Assistant is ready. Click 'Start Listening' and speak a command.")
process_gui_queue()
window.mainloop()

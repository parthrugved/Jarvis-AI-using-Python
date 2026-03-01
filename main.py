import speech_recognition as sr
import os
from pathlib import Path
import sys
import webbrowser 
import datetime
import subprocess
import requests

def ask_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

def say(text):
    os.system(f"say {text}")

def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 0.6
        audio = r.listen(source)
        try:
            print("Recognizing...")
            query = r.recognize_google(audio, language="en-in")
            print(f"User said : {query}")
            return query
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return ""

if __name__ == '__main__':
    # Ensure SpeechRecognition finds our project-local FLAC converter, and that it
    # runs under this venv's Python (so it can import `soundfile`).
    tools_dir = Path(__file__).resolve().parent / "tools"
    venv_bin = str(Path(sys.executable).parent)
    os.environ["PATH"] = f"{venv_bin}{os.pathsep}{tools_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    print("J.A.R.V.I.S")
    say("Jarvis A.I")
    while True:
        print("Listening...")
        query = takeCommand()
        # adding webiste feature
        sites = [["youtube","https://www.youtube.com"],["saree","https://sareekraft.in"],["GitHub","https://github.com"],["answers","https://maharashtraboardsolutions.in/maharashtra-state-board-class-7-textbook-solutions/"],["chat GPT","https://chatgpt.com"]]
        for site in sites:
            if f"Open {site[0]}".lower() in query.lower():
                say(f"opening {site[0]} ")
                webbrowser.open(site[1])
            # add time feature
        if "the time".lower() in query.lower():
            strfTime = datetime.datetime.now().strftime("%H:%M:%S")
            say(f"The current Time is {strfTime}")
        
        # Opening apps
        if "Open facetime".lower() in query.lower():
            say("Opening Facetime")
            os.system(f"open /System/Applications/FaceTime.app")

        apps = [["Vs code", "/Applications/Visual Studio Code.app"],["Terminal","/System/Applications/Utilities/Terminal.app"],["Google","/Applications/Google Chrome.app"],["Calculator","/System/Applications/Calculator.app"],["System Settings","/System/Applications/System Settings.app"],["App Store","/System/Applications/App Store.app"]]
        for app in apps:
            if f"open {app[0]}".lower() in query.lower():
                print(f"Opening {app[0]}")
                subprocess.run(["open", app[1]])

        if "Introduce yourself".lower() in query.lower():
            introduction = """
            My project, JARVIS (Just A Rather Very Intelligent System), is a voice-controlled AI assistant built using Python. It is inspired by the intelligent assistant from the Iron Man movies. The purpose of this project is to create a smart system that can understand human voice commands and perform tasks automatically.

            JARVIS can listen to the user through the microphone, recognize speech using artificial intelligence, and respond using voice output. It can open websites, launch applications, tell the current time, and execute different computer commands, making interaction with the computer faster and hands-free.

            This project demonstrates how programming, artificial intelligence, and automation can be combined to build a real-life virtual assistant. It also helped me learn about speech recognition, system control, and user interaction. In the future, I plan to add more advanced features like mobile control, smart responses, and a graphical interface to make JARVIS even more powerful.
            """
            say(introduction)

            # stop feature
        if "stop".lower() in query.lower():
            break

        # ollama feature
        if "answer".lower() in query.lower():
            question = query.replace("answer", "")
            reply = ask_ollama(question)
            say(reply)
            print(f"Answer: {reply}")
 
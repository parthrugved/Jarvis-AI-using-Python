# 🤖 J.A.R.V.I.S — Offline AI Voice Assistant

**J.A.R.V.I.S (Just A Rather Very Intelligent System)** is a voice-controlled AI assistant built using Python.
It can listen to voice commands, perform system tasks, open apps/websites, and answer questions using a **fully local AI model (Llama 3.1 via Ollama)** — no paid APIs required.

> ⚡ Inspired by the assistant from the Iron Man movies.

---

## 🚀 Features

🎤 **Voice recognition** using microphone  
🧠 **Offline AI responses** powered by Ollama + Llama 3.1  
🔊 **Text-to-speech** using macOS built-in voice  
🌐 **Open websites** via voice commands  
🖥 **Launch system applications**  
⏰ **Tell current time** and date  
🤖 **Introduce itself**  
🛑 **Stop command** to exit  
🖼 **Modern GUI** (Tkinter) with continuous listening and text input  
🔒 **Works offline** — private and unlimited  

---

## 🧠 AI Integration

This project uses:

* **Ollama** for running local LLMs
* **Llama 3.1 (8B)** model
* No internet required for AI responses
* No API costs

JARVIS sends your spoken question to the local model and speaks the answer back.

---

## 🛠 Technologies Used

* Python
* SpeechRecognition
* PyAudio
* requests
* tkinter
* macOS `say` command
* Ollama
* Llama 3.1

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/parthrugved/Jarvis-AI-using-Python.git
cd Jarvis
```

### 2️⃣ Install dependencies

```bash
pip install SpeechRecognition pyaudio requests
```

### 3️⃣ Install Ollama

Download from:

👉 https://ollama.com

Then install the model:

```bash
ollama pull llama3.1
```

---

## ▶️ Running JARVIS

### GUI (recommended)

Start Ollama (if you want AI answers), then run:

```bash
python app.py
```

Grant **microphone** access when prompted. JARVIS listens continuously; use the **LISTEN** button or type in the text bar. Say **"Stop"** to exit.

### CLI (terminal only)

```bash
python main.py
```

Same voice commands, no window. Say **"Stop"** to exit.

---

## 💡 Example Commands

| Command              | Action                |
| -------------------- | --------------------- |
| Open YouTube         | Opens in browser      |
| Open VS Code         | Launches app          |
| What is the time     | Speaks current time   |
| Answer &lt;question&gt; | Asks local AI (Ollama) |
| Introduce yourself   | JARVIS introduction   |
| Say &lt;anything&gt;     | Repeats it back       |
| Stop                 | Exit program          |

---

## 🔥 Why This Project Is Special

✔ Fully offline AI assistant  
✔ No API keys  
✔ No usage limits  
✔ Private  
✔ Modern GUI + CLI  
✔ Built by a student developer  

---

## 🚧 Future Improvements

* Wake word detection ("Jarvis")
* Conversation memory
* Mobile integration
* Smart home control

---

## 🧑‍💻 Author

Built with ❤️ by **Parth**  
Student • Developer • Builder

---

## ⭐ If you like this project

Give it a star on GitHub ⭐

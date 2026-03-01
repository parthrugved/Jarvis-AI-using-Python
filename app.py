"""
J.A.R.V.I.S GUI  —  Just A Rather Very Intelligent System

Beautiful, modern Tkinter interface that wraps the same ideas as `main.py`
without modifying it.  Requires:

    pip install SpeechRecognition

On macOS, voice output uses the built‑in `say` command.
"""

import os
import sys
import math
import threading
import datetime
import webbrowser
import subprocess
from pathlib import Path

import requests
import tkinter as tk
import speech_recognition as sr


# ── Ollama ─────────────────────────────────────────────────────────────────────
def ask_ollama(prompt: str) -> str | None:
    """Call local Ollama (llama3.1). Returns response text or None on error."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1",
                "prompt": prompt.strip(),
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception:
        return None


# ── Global state ────────────────────────────────────────────────────────────────
# Tracks when macOS TTS is actively speaking so we can avoid listening to our
# own voice and creating feedback loops.
SPEAKING = False


# ── Colours ─────────────────────────────────────────────────────────────────────
BG      = "#050d1a"
PANEL   = "#0a1628"
ACCENT  = "#00d4ff"
ACCENT2 = "#0077ff"
DIM     = "#003a55"
TEXT    = "#c8f0ff"
SUB     = "#4a8fa8"
WARN    = "#ff6b35"
OK      = "#00ff9f"
BORDER  = "#0d2d44"
MID     = "#0e2236"


# ── TTS ─────────────────────────────────────────────────────────────────────────
def say(text: str) -> None:
    """Speak text asynchronously using macOS `say` at a smooth, slower rate.

    While speaking, a global flag is set so the recogniser does not listen to
    our own TTS output.
    """
    global SPEAKING
    t = text.replace('"', "'")
    cmd = f'say -r 150 "{t}"'

    def _run():
        global SPEAKING
        SPEAKING = True
        try:
            os.system(cmd)
        finally:
            SPEAKING = False

    threading.Thread(target=_run, daemon=True).start()


# ── Voice engine ────────────────────────────────────────────────────────────────
class VoiceEngine:
    def __init__(self) -> None:
        self._r = sr.Recognizer()
        self._r.pause_threshold = 0.6
        # Slightly lower starting threshold so normal voice volume is enough.
        self._r.energy_threshold = 200
        self._r.dynamic_energy_threshold = True
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def calibrate(self, cb):
        """Background mic calibration; calls cb(ok: bool, level: int)."""

        def work():
            try:
                with sr.Microphone() as s:
                    self._r.adjust_for_ambient_noise(s, duration=2.5)
                cb(True, int(self._r.energy_threshold))
            except Exception:
                cb(False, 0)

        threading.Thread(target=work, daemon=True).start()

    def listen(self, cb):
        """Start listening in the background; cb(text, error)."""
        if self._busy:
            return
        self._busy = True
        threading.Thread(target=self._work, args=(cb,), daemon=True).start()

    def _work(self, cb):
        try:
            with sr.Microphone() as s:
                audio = self._r.listen(s, timeout=8, phrase_time_limit=10)
            text = self._r.recognize_google(audio, language="en-in")
            cb(text, None)
        except sr.WaitTimeoutError:
            cb(None, "timeout")
        except sr.UnknownValueError:
            cb(None, "unclear")
        except Exception as e:  # noqa: BLE001
            cb(None, str(e))
        finally:
            self._busy = False


# ── Main app ────────────────────────────────────────────────────────────────────
class JarvisApp:
    # Match behaviour of `main.py` but in a nicer GUI.
    SITES = [
        ("YouTube", "https://www.youtube.com"),
        ("Saree", "https://sareekraft.in"),
        ("GitHub", "https://github.com"),
        (
            "Answers",
            "https://maharashtraboardsolutions.in/"
            "maharashtra-state-board-class-7-textbook-solutions/",
        ),
        ("ChatGPT", "https://chatgpt.com"),
    ]

    APPS = [
        ("VS Code", "/Applications/Visual Studio Code.app"),
        ("Terminal", "/System/Applications/Utilities/Terminal.app"),
        ("Google Chrome", "/Applications/Google Chrome.app"),
        ("Calculator", "/System/Applications/Calculator.app"),
        ("System Settings", "/System/Applications/System Settings.app"),
        ("App Store", "/System/Applications/App Store.app"),
        ("FaceTime", "/System/Applications/FaceTime.app"),
    ]

    def __init__(self) -> None:
        self._voice = VoiceEngine()
        self._angle = 0.0
        self._pulse = 0.0
        self._listening = False
        self._stopping = False  # set to True once user says stop/shutdown
        # Simple debounce so we don't keep repeating time/date on background noise.
        self._last_time_ts: datetime.datetime | None = None
        self._last_date_ts: datetime.datetime | None = None

        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.configure(bg=BG)
        self.root.geometry("980x680")
        self.root.minsize(760, 540)
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

        self._build()
        self.root.after(600, self._init_audio)

    # ── Build UI ────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        r = self.root

        # Title
        tf = tk.Frame(r, bg=BG)
        tf.pack(fill="x", padx=18, pady=(14, 0))
        tk.Label(
            tf,
            text="J.A.R.V.I.S",
            bg=BG,
            fg=ACCENT,
            font=("Courier", 20, "bold"),
        ).pack(side="left")
        tk.Label(
            tf,
            text="  Just A Rather Very Intelligent System",
            bg=BG,
            fg=SUB,
            font=("Courier", 10),
        ).pack(side="left")
        tk.Frame(r, bg=BORDER, height=1).pack(fill="x", padx=14, pady=6)

        body = tk.Frame(r, bg=BG)
        body.pack(fill="both", expand=True, padx=14)

        # LEFT column
        left = tk.Frame(body, bg=BG, width=220)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        # Animated ring
        self._ring = tk.Canvas(left, bg=BG, highlightthickness=0)
        self._ring.configure(width=200, height=200)
        self._ring.pack(pady=(8, 4))

        self._status_lbl = tk.Label(
            left,
            text="STARTING…",
            bg=BG,
            fg=SUB,
            font=("Courier", 10, "bold"),
        )
        self._status_lbl.pack()

        # Volume bar
        self._vbar = tk.Canvas(left, bg=PANEL, highlightthickness=0)
        self._vbar.configure(width=190, height=13)
        self._vbar.pack(pady=(7, 1))
        tk.Label(
            left,
            text="MICROPHONE LEVEL",
            bg=BG,
            fg=SUB,
            font=("Courier", 7),
        ).pack()

        # Listen button
        self._btn = tk.Button(
            left,
            text="⬤  LISTEN",
            command=self._on_listen,
            bg=DIM,
            fg=ACCENT,
            activebackground=ACCENT,
            activeforeground=BG,
            relief="flat",
            bd=0,
            font=("Courier", 12, "bold"),
            cursor="hand2",
            padx=16,
            pady=9,
            width=17,
        )
        self._btn.pack(pady=10)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=4)

        # Scrollable sidebar with shortcuts
        sc = tk.Canvas(left, bg=BG, highlightthickness=0)
        ssb = tk.Scrollbar(
            left,
            orient="vertical",
            command=sc.yview,
            bg=BG,
            troughcolor=BG,
        )
        sc.configure(yscrollcommand=ssb.set)
        ssb.pack(side="right", fill="y")
        sc.pack(fill="both", expand=True)
        inner = tk.Frame(sc, bg=BG)
        sc.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>",
            lambda e: sc.configure(scrollregion=sc.bbox("all")),
        )

        def sbtn(parent, label, cmd):
            b = tk.Button(
                parent,
                text=label,
                command=cmd,
                bg=PANEL,
                fg=TEXT,
                activebackground=DIM,
                activeforeground=ACCENT,
                relief="flat",
                bd=0,
                font=("Courier", 9),
                cursor="hand2",
                padx=10,
                pady=5,
                anchor="w",
            )
            b.bind("<Enter>", lambda _: b.configure(fg=ACCENT, bg=DIM))
            b.bind("<Leave>", lambda _: b.configure(fg=TEXT, bg=PANEL))
            b.pack(fill="x", pady=1)

        tk.Label(
            inner,
            text="WEBSITES",
            bg=BG,
            fg=SUB,
            font=("Courier", 7, "bold"),
        ).pack(anchor="w", padx=4, pady=(4, 1))
        for n, u in self.SITES:
            sbtn(
                inner,
                f"↗  {n}",
                lambda u=u, n=n: self._open_site(n, u),
            )

        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=5)

        tk.Label(
            inner,
            text="APPLICATIONS",
            bg=BG,
            fg=SUB,
            font=("Courier", 7, "bold"),
        ).pack(anchor="w", padx=4, pady=(0, 1))
        for n, p in self.APPS:
            sbtn(
                inner,
                f"▶  {n}",
                lambda p=p, n=n: self._open_app(n, p),
            )

        # RIGHT column
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # Log header
        lh = tk.Frame(right, bg=MID)
        lh.pack(fill="x")
        tk.Label(
            lh,
            text="  ▌ SYSTEM LOG",
            bg=MID,
            fg=ACCENT,
            font=("Courier", 10, "bold"),
            pady=5,
        ).pack(side="left")
        tk.Button(
            lh,
            text="CLR",
            command=self._clear_log,
            bg=MID,
            fg=SUB,
            activebackground=DIM,
            activeforeground=ACCENT,
            relief="flat",
            bd=0,
            font=("Courier", 8),
            cursor="hand2",
            padx=8,
        ).pack(side="right", padx=4)

        # Log text
        self._log_txt = tk.Text(
            right,
            bg=PANEL,
            fg=TEXT,
            font=("Courier", 11),
            insertbackground=ACCENT,
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
            selectbackground=DIM,
        )
        lsb = tk.Scrollbar(
            right,
            orient="vertical",
            command=self._log_txt.yview,
            bg=PANEL,
            troughcolor=PANEL,
            activebackground=ACCENT,
        )
        self._log_txt.configure(yscrollcommand=lsb.set)
        lsb.pack(side="right", fill="y")
        self._log_txt.pack(fill="both", expand=True, padx=6, pady=6)

        self._log_txt.tag_config(
            "ts",
            foreground="#27485a",
            font=("Courier", 9),
        )
        self._log_txt.tag_config(
            "user",
            foreground=ACCENT,
            font=("Courier", 11, "bold"),
        )
        self._log_txt.tag_config(
            "jarvis",
            foreground=OK,
            font=("Courier", 11, "bold"),
        )
        self._log_txt.tag_config(
            "system",
            foreground=SUB,
            font=("Courier", 10),
        )
        self._log_txt.tag_config(
            "error",
            foreground=WARN,
            font=("Courier", 10),
        )

        # Input bar
        inp = tk.Frame(right, bg=BORDER)
        inp.pack(fill="x", pady=(6, 0))
        tk.Label(
            inp,
            text=" ›",
            bg=BORDER,
            fg=ACCENT,
            font=("Courier", 15, "bold"),
        ).pack(side="left", padx=4)
        self._entry = tk.Entry(
            inp,
            bg=MID,
            fg=TEXT,
            insertbackground=ACCENT,
            font=("Courier", 12),
            relief="flat",
            bd=0,
        )
        self._entry.pack(side="left", fill="both", expand=True, ipady=9)
        self._entry.bind("<Return>", lambda _: self._text_cmd())
        tk.Button(
            inp,
            text="SEND",
            command=self._text_cmd,
            bg=ACCENT2,
            fg="white",
            activebackground=ACCENT,
            activeforeground=BG,
            relief="flat",
            bd=0,
            font=("Courier", 10, "bold"),
            cursor="hand2",
            padx=14,
            pady=9,
        ).pack(side="right")

        # Status bar
        self._sb = tk.Frame(r, bg=BORDER)
        self._sb.pack(fill="x", side="bottom")
        self._sb_dot = tk.Label(
            self._sb,
            text="●",
            bg=BORDER,
            fg=SUB,
            font=("Courier", 10),
        )
        self._sb_dot.pack(side="left", padx=8, pady=3)
        self._sb_lbl = tk.Label(
            self._sb,
            text="STANDBY",
            bg=BORDER,
            fg=SUB,
            font=("Courier", 10, "bold"),
        )
        self._sb_lbl.pack(side="left")
        self._sb_clk = tk.Label(
            self._sb,
            bg=BORDER,
            fg=SUB,
            font=("Courier", 10),
        )
        self._sb_clk.pack(side="right", padx=10)

        # Start animations
        self.root.after(250, self._tick_ring)
        self.root.after(250, self._tick_vbar)
        self.root.after(0, self._tick_clock)

    # ── Animations ──────────────────────────────────────────────────────────────
    def _tick_ring(self) -> None:
        c = self._ring
        cx = cy = 100
        # Slightly slower animation for a smoother feel.
        self._angle = (self._angle + 1.0) % 360
        self._pulse += 0.06
        a = self._angle
        p = self._pulse

        c.delete("all")

        def arc(rad, start, extent, color, w=2):
            c.create_arc(
                cx - rad,
                cy - rad,
                cx + rad,
                cy + rad,
                start=start,
                extent=extent,
                outline=color,
                width=w,
                style="arc",
            )

        arc(96, 0, 359, DIM, 1)
        col = ACCENT if self._listening else ACCENT2
        arc(96, a, 200, col, 2)
        arc(96, a + 210, 60, col, 1)
        arc(80, -a * 1.4, 130, DIM, 1)
        arc(80, -a * 1.4 + 150, 80, ACCENT2, 2)

        glow = 1 + 4 * math.sin(p) + (
            3 * abs(math.sin(p * 1.7)) if self._listening else 0
        )
        arc(
            58 + glow,
            0,
            359,
            ACCENT if self._listening else DIM,
            max(1, int(glow)),
        )

        if self._listening:
            for i, bh in enumerate([0.3, 0.6, 1.0, 0.6, 0.3]):
                h = int(20 * bh * (0.5 + 0.5 * math.sin(p * 2 + i)))
                bx = cx - 16 + i * 8
                c.create_rectangle(
                    bx,
                    cy - h,
                    bx + 6,
                    cy + h,
                    fill=OK,
                    outline="",
                )
        else:
            c.create_text(
                cx,
                cy,
                text="J",
                fill=ACCENT,
                font=("Courier", 30, "bold"),
            )

        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            c.create_line(
                cx + 90 * math.cos(rad),
                cy - 90 * math.sin(rad),
                cx + 98 * math.cos(rad),
                cy - 98 * math.sin(rad),
                fill=SUB,
                width=1,
            )

        self.root.after(30, self._tick_ring)

    def _tick_vbar(self) -> None:
        v = self._vbar
        p = self._pulse
        W, H = 190, 13
        if self._listening:
            lvl = 30 + 55 * abs(math.sin(p * 2.0))
        else:
            lvl = 8 + 6 * abs(math.sin(p * 0.35))

        v.delete("all")
        v.create_rectangle(0, 0, W, H, fill=DIM, outline="")
        fw = int(W * lvl / 100)
        if fw > 0:
            col = OK if lvl < 40 else ACCENT if lvl < 70 else WARN
            v.create_rectangle(0, 0, fw, H, fill=col, outline="")
        label = "LISTENING…" if self._listening else "STANDBY"
        v.create_text(
            W // 2,
            H // 2,
            text=label,
            fill=TEXT,
            font=("Courier", 7),
        )
        self.root.after(50, self._tick_vbar)

    def _tick_clock(self) -> None:
        self._sb_clk.configure(
            text=datetime.datetime.now().strftime("%a %d %b   %H:%M:%S"),
        )
        self.root.after(1000, self._tick_clock)

    # ── Audio init ──────────────────────────────────────────────────────────────
    def _init_audio(self) -> None:
        self._log("Calibrating microphone…", "system")
        self._voice.calibrate(self._on_cal)

    def _on_cal(self, ok: bool, level: int) -> None:
        self.root.after(0, self._post_cal, ok, level)

    def _post_cal(self, ok: bool, level: int) -> None:
        if ok:
            self._log(
                f"Mic ready — noise threshold {level}.",
                "system",
            )
            self._log(
                "JARVIS online. Listening continuously — say 'stop' to exit.",
                "jarvis",
            )
            self._set_status("LISTENING…", ACCENT)
            say("Jarvis A.I.")
            # Start the continuous listening loop.
            self.root.after(300, self._on_listen)
        else:
            self._log(
                "Mic calibration failed — check System Settings → "
                "Privacy → Microphone.",
                "error",
            )
            self._set_status("MIC ERROR", WARN)

    # ── Status & logging ────────────────────────────────────────────────────────
    def _set_status(self, text: str, color: str = SUB, reset_ms: int = 0) -> None:
        self._status_lbl.configure(text=text, fg=color)
        self._sb_dot.configure(fg=color)
        self._sb_lbl.configure(text=text, fg=color)
        if reset_ms:
            self.root.after(
                reset_ms,
                lambda: self._set_status("STANDBY", SUB),
            )

    _PFX = {
        "user": "YOU  ›› ",
        "jarvis": "JRVS ›› ",
        "system": "SYS  ·· ",
        "error": "ERR  !! ",
    }

    def _log(self, text: str, kind: str = "jarvis") -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        pfx = self._PFX.get(kind, "     ›› ")
        self._log_txt.configure(state="normal")
        self._log_txt.insert("end", f"[{ts}] ", "ts")
        self._log_txt.insert("end", pfx + text + "\n", kind)
        self._log_txt.see("end")
        self._log_txt.configure(state="disabled")

    def _clear_log(self) -> None:
        self._log_txt.configure(state="normal")
        self._log_txt.delete("1.0", "end")
        self._log_txt.configure(state="disabled")

    # ── Voice + text flows ─────────────────────────────────────────────────────
    def _on_listen(self) -> None:
        # If we're in the middle of speaking or shutting down, delay listening
        # to avoid picking up our own TTS or running while exiting.
        if self._stopping:
            return
        if SPEAKING or self._voice.busy:
            self.root.after(500, self._on_listen)
            return
        self._listening = True
        self._set_status("LISTENING…", ACCENT)
        self._btn.configure(
            text="◉  LISTENING",
            bg=ACCENT,
            fg=BG,
            state="disabled",
        )
        self._log("Listening… speak your command.", "system")
        self._voice.listen(self._on_result)

    def _on_result(self, text: str | None, error: str | None) -> None:
        self.root.after(0, self._post_result, text, error)

    def _post_result(self, text: str | None, error: str | None) -> None:
        self._listening = False
        # Reset button visual, but keep it enabled for manual use.
        self._btn.configure(text="⬤  LISTEN", bg=DIM, fg=ACCENT, state="normal")
        if text:
            self._log(text, "user")
            self._handle(text)
        elif error == "timeout":
            self._log("No speech detected (timeout).", "error")
            self._set_status("STANDBY", SUB)
        elif error == "unclear":
            self._log(
                "Could not understand speech — please try again.",
                "error",
            )
            self._set_status("STANDBY", SUB)
        else:
            self._log(f"Recognition error: {error}", "error")
            self._set_status("STANDBY", SUB)

        # Re‑enter listening loop with a small pause for a smoother cadence,
        # unless a shutdown sequence is in progress.
        if not self._stopping:
            self.root.after(700, self._on_listen)

    def _text_cmd(self) -> None:
        q = self._entry.get().strip()
        if not q:
            return
        self._entry.delete(0, "end")
        self._log(q, "user")
        self._handle(q)

    # ── Command dispatcher ─────────────────────────────────────────────────────
    def _handle(self, query: str) -> None:
        q = query.lower()
        handled = False

        # Websites
        for name, url in self.SITES:
            if f"open {name.lower()}" in q:
                self._open_site(name, url)
                handled = True

        # Apps
        for name, path in self.APPS:
            if f"open {name.lower()}" in q or f"launch {name.lower()}" in q:
                self._open_app(name, path)
                handled = True

        # Time (debounced)
        if any(k in q for k in ("the time", "what time", "current time")):
            now = datetime.datetime.now()
            if not self._last_time_ts or (now - self._last_time_ts).total_seconds() > 10:
                self._last_time_ts = now
                msg = "The current time is " + now.strftime("%H:%M:%S") + "."
                self._log(msg, "jarvis")
                self._set_status("SPEAKING", OK, 2500)
                say(msg)
                handled = True

        # Date / day (debounced, stricter phrases so random "today" doesn't trigger)
        if any(
            k in q
            for k in (
                "what is the date",
                "what's the date",
                "tell me the date",
                "what day is it",
                "which day is it",
            )
        ):
            now = datetime.datetime.now()
            if not self._last_date_ts or (now - self._last_date_ts).total_seconds() > 10:
                self._last_date_ts = now
                msg = "Today is " + now.strftime("%A, %d %B %Y") + "."
                self._log(msg, "jarvis")
                self._set_status("SPEAKING", OK, 2500)
                say(msg)
                handled = True

        # Explicit "say ..." — repeat back the sentence the user speaks.
        if q.startswith("say "):
            phrase = query[4:].strip()
            if phrase:
                msg = f'You said: "{phrase}"'
                self._log(msg, "jarvis")
                self._set_status("SPEAKING", OK, 2500)
                say(phrase)
                handled = True

        # Ollama "answer <question>" — run in thread so GUI stays responsive
        if "answer" in q:
            question = query.replace("answer", "").replace("Answer", "").strip()
            if question:
                handled = True
                self._set_status("ASKING OLLAMA…", ACCENT)
                self._log(f"Asking Ollama: {question}", "system")

                def work():
                    reply = ask_ollama(question)
                    self.root.after(0, self._on_ollama_done, reply, question)

                threading.Thread(target=work, daemon=True).start()
            else:
                self._log(
                    "Answer what? Say 'answer' followed by your question.",
                    "error",
                )
                handled = True

        # Intro (adapted from main.py)
        if any(k in q for k in ("introduce yourself", "who are you")):
            introduction = (
                "My project, JARVIS — Just A Rather Very Intelligent System — "
                "is a voice-controlled AI assistant built using Python. "
                "I can listen to your voice, open websites, launch "
                "applications, tell the current time, and execute different "
                "computer commands, making your interaction with the computer "
                "faster and hands‑free."
            )
            self._log(introduction, "jarvis")
            self._set_status("SPEAKING", OK, 6500)
            say(introduction)
            handled = True

        # Greetings
        if any(k in q for k in ("hello", "hi jarvis", "hey jarvis")):
            msg = "Hello! How can I assist you today?"
            self._log(msg, "jarvis")
            self._set_status("SPEAKING", OK, 2000)
            say(msg)
            handled = True

        # Shutdown
        if any(k in q for k in ("stop", "shutdown", "quit", "exit")):
            self._stopping = True
            self._log("Shutting down. Goodbye.", "system")
            say("Goodbye.")
            self.root.after(1800, self._shutdown)
            handled = True

        if not handled:
            # For unknown commands, just log what was heard; only explicit
            # "say ..." commands are spoken back.
            msg = f'Unrecognised command. I heard: "{query}"'
            print(msg)
            self._log(msg, "error")
            self._set_status("STANDBY", SUB)

    def _on_ollama_done(self, reply: str | None, question: str) -> None:
        """Called on main thread after Ollama request finishes."""
        if reply is None:
            self._log(
                "Ollama unavailable. Is it running on localhost:11434?",
                "error",
            )
            self._set_status("STANDBY", SUB)
            say("Could not reach Ollama. Make sure it is running.")
        else:
            self._log(reply, "jarvis")
            self._set_status("SPEAKING", OK, 4000)
            say(reply)

    # ── Site / app helpers ─────────────────────────────────────────────────────
    def _open_site(self, name: str, url: str) -> None:
        self._log(f"Opening {name} in browser…", "jarvis")
        self._set_status(f"OPENING {name.upper()}", ACCENT, 2500)
        say(f"Opening {name}")
        webbrowser.open(url)

    def _open_app(self, name: str, path: str) -> None:
        self._log(f"Launching {name}…", "jarvis")
        self._set_status(f"LAUNCHING {name.upper()}", ACCENT, 2500)
        say(f"Launching {name}")
        subprocess.Popen(["open", path])

    # ── Shutdown & run loop ────────────────────────────────────────────────────
    def _shutdown(self) -> None:
        self.root.destroy()

    def run(self) -> None:
        # macOS‑style menu bar (best‑effort)
        try:
            self.root.createcommand(
                "::tk::mac::ReopenApplication",
                lambda: self.root.lift(),
            )
            mb = tk.Menu(self.root)
            apple = tk.Menu(mb, name="apple", tearoff=False)
            mb.add_cascade(menu=apple)
            apple.add_command(label="About JARVIS", command=lambda: None)
            apple.add_separator()
            apple.add_command(
                label="Quit JARVIS",
                command=self._shutdown,
                accelerator="Cmd+Q",
            )
            self.root.bind_all("<Command-q>", lambda _: self._shutdown())
            win = tk.Menu(mb, name="window", tearoff=False)
            mb.add_cascade(label="Window", menu=win)
            self.root.configure(menu=mb)
        except Exception:
            # Safe to ignore if Tk on this platform does not support mac menus.
            pass

        self.root.mainloop()


if __name__ == "__main__":
    # Ensure SpeechRecognition finds the project‑local FLAC converter and that it
    # runs under this venv's Python (so it can import `soundfile`), mirroring
    # the behaviour in `main.py`.
    tools_dir = Path(__file__).resolve().parent / "tools"
    venv_bin = str(Path(sys.executable).parent)
    os.environ["PATH"] = (
        f"{venv_bin}{os.pathsep}{tools_dir}{os.pathsep}"
        f"{os.environ.get('PATH', '')}"
    )

    JarvisApp().run()


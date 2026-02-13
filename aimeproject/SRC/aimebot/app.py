"""
AimeBot - Complete Android Voice Assistant
Built with BeeWare/Toga for Android APK
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import requests
import json
import os
from datetime import datetime
import threading

# Android specific imports
from android.content import Intent
from android.speech import RecognizerIntent
from android.speech.tts import TextToSpeech

class AimeBot(toga.App):
    def startup(self):
        """Initialize the app UI"""
        
        # Main window setup
        self.main_window = toga.MainWindow(title="AimeBot")
        
        # Initialize Android TTS
        self.tts = None
        self.init_tts()
        
        # App commands database
        self.app_commands = {
            "youtube": "com.google.android.youtube",
            "facebook": "com.facebook.katana",
            "whatsapp": "com.whatsapp",
            "chrome": "com.android.chrome",
            "camera": "com.android.camera",
            "settings": "com.android.settings",
            "gallery": "com.android.gallery3d",
            "calculator": "com.android.calculator2",
            "maps": "com.google.android.apps.maps",
            "gmail": "com.google.android.gm",
            "phone": "com.android.dialer",
            "messages": "com.android.mms",
            "clock": "com.android.deskclock",
            "contacts": "com.android.contacts",
            "spotify": "com.spotify.music",
            "instagram": "com.instagram.android",
            "twitter": "com.twitter.android",
            "tiktok": "com.zhiliaoapp.musically",
            "telegram": "org.telegram.messenger"
        }
        
        # AI Configuration
        self.openai_model = "gpt-4o-mini"
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Memory for conversations
        self.last_question = ""
        self.last_answer = ""
        
        # Create UI
        self.create_ui()
        
        # Initial greeting
        if self.openai_api_key:
            self.speak("Hello! I'm AimeBot. Tap the microphone and speak.")
        else:
            self.status_label.text = "⚠️ Set OpenAI API key in GitHub Secrets"
    
    def init_tts(self):
        """Initialize Android TextToSpeech"""
        try:
            self.tts = TextToSpeech(self.main_window._impl.native, 
                                   TextToSpeech.OnInitListener())
        except:
            print("TTS initialization failed")
    
    def create_ui(self):
        """Build the user interface"""
        
        # Status indicator
        self.status_label = toga.Label(
            "Ready",
            style=Pack(padding=(20, 10), font_size=16)
        )
        
        # Mic button
        self.mic_button = toga.Button(
            "🎤 TAP TO SPEAK",
            on_press=self.start_listening,
            style=Pack(
                padding=20,
                font_size=20,
                background_color="#2196F3",
                color="white",
                width=250,
                height=80
            )
        )
        
        # Quick action buttons
        quick_box = toga.Box(style=Pack(direction=ROW, padding=10))
        
        time_btn = toga.Button(
            "🕐 Time",
            on_press=lambda x: self.process_command("what time is it"),
            style=Pack(padding=5, flex=1)
        )
        
        date_btn = toga.Button(
            "📅 Date",
            on_press=lambda x: self.process_command("what is today's date"),
            style=Pack(padding=5, flex=1)
        )
        
        help_btn = toga.Button(
            "❓ Help",
            on_press=lambda x: self.show_help(),
            style=Pack(padding=5, flex=1)
        )
        
        quick_box.add(time_btn, date_btn, help_btn)
        
        # Conversation display
        self.conversation = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1, padding=10, font_size=14)
        )
        self.conversation.value = "🤖 AimeBot ready!\n"
        
        # Main layout
        main_box = toga.Box(
            children=[
                self.status_label,
                self.mic_button,
                quick_box,
                self.conversation
            ],
            style=Pack(direction=COLUMN, padding=10)
        )
        
        self.main_window.content = main_box
        self.main_window.show()
    
    def speak(self, text):
        """Speak text using Android TTS"""
        if not text:
            return
        
        # Display in conversation
        self.conversation.value += f"\n🤖 AimeBot: {text}\n"
        
        # Scroll to bottom
        if hasattr(self.conversation, 'scroll_to_bottom'):
            self.conversation.scroll_to_bottom()
        
        # Speak
        try:
            if self.tts:
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None)
        except:
            pass
    
    def start_listening(self, widget):
        """Start voice recognition"""
        try:
            self.status_label.text = "🎤 Listening..."
            self.mic_button.enabled = False
            
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                           RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak now...")
            
            self.main_window._impl.native.startActivityForResult(intent, 1001)
            self._impl.on_activity_result = self.on_activity_result
            
        except Exception as e:
            self.status_label.text = "❌ Error"
            self.mic_button.enabled = True
    
    def on_activity_result(self, request_code, result_code, data):
        """Handle speech recognition result"""
        self.mic_button.enabled = True
        
        if request_code == 1001 and result_code == -1:
            results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
            if results and results.size() > 0:
                command = results.get(0)
                self.status_label.text = "✅ Processing..."
                self.conversation.value += f"\n👤 You: {command}\n"
                self.process_command(command)
            else:
                self.status_label.text = "❌ No speech detected"
        else:
            self.status_label.text = "❌ Cancelled"
    
    def process_command(self, command):
        """Process voice command"""
        cmd_lower = command.lower()
        
        # Open apps
        for app_name in self.app_commands:
            if app_name in cmd_lower and "open" in cmd_lower:
                self.open_app(app_name)
                return
        
        # Time and date
        if "time" in cmd_lower:
            time_str = datetime.now().strftime('%I:%M %p')
            self.speak(f"The time is {time_str}")
            return
        
        if "date" in cmd_lower:
            date_str = datetime.now().strftime('%A, %B %d, %Y')
            self.speak(f"Today is {date_str}")
            return
        
        # Help
        if "help" in cmd_lower:
            self.show_help()
            return
        
        # Exit
        if any(x in cmd_lower for x in ["exit", "quit", "bye"]):
            self.speak("Goodbye!")
            return
        
        # AI response
        if self.openai_api_key:
            thread = threading.Thread(target=self.get_ai_response, args=(command,))
            thread.start()
        else:
            self.speak("Please set your OpenAI API key in GitHub repository secrets")
    
    def open_app(self, app_name):
        """Open Android app"""
        try:
            package = self.app_commands[app_name]
            intent = Intent(Intent.ACTION_MAIN)
            intent.setPackage(package)
            intent.addCategory(Intent.CATEGORY_LAUNCHER)
            self.main_window._impl.native.startActivity(intent)
            self.speak(f"Opening {app_name}")
        except:
            self.speak(f"Could not open {app_name}")
    
    def show_help(self):
        """Show help message"""
        help_text = (
            "I can:\n"
            "• Open apps: 'open YouTube'\n"
            "• Tell time & date\n"
            "• Answer questions with AI\n"
            "• Explain topics in detail"
        )
        self.speak(help_text)
    
    def get_ai_response(self, query):
        """Get response from OpenAI"""
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        # Determine if detailed explanation needed
        is_detailed = any(k in query.lower() for k in 
                         ["explain", "details", "why", "how", "more"])
        
        data = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query}
            ],
            "temperature": 0.7 if is_detailed else 0.3,
            "max_tokens": 300 if is_detailed else 100
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"]
                self.main_window._impl.app.loop.call_soon_threadsafe(
                    lambda: self.speak(answer)
                )
            else:
                self.main_window._impl.app.loop.call_soon_threadsafe(
                    lambda: self.speak(f"API Error: {response.status_code}")
                )
        except Exception as e:
            self.main_window._impl.app.loop.call_soon_threadsafe(
                lambda: self.speak("Network error. Check your connection.")
            )
        
        self.main_window._impl.app.loop.call_soon_threadsafe(
            lambda: setattr(self.status_label, 'text', "Ready")
        )
    
    def shutdown(self):
        """Cleanup"""
        if self.tts:
            self.tts.shutdown()

def main():
    return AimeBot()

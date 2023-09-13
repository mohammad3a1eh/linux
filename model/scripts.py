from playsound import playsound
import subprocess
from model.config import *
import random
from os import system
from pyttsx3 import init

roles = {
    "ok" : [
        ""
    ],
    "error" : [
        
    ],
    "start" : [
        
    ],
    "oh" : [
        
    ]
}


def play(text):
    e = init()
    voices = e.getProperty('voices')
    e.setProperty("rate", 200) 
    e.setProperty("voice", voices[12].id)  # set english
    e.say(text)
    e.runAndWait()
    
def play_role(role):
    text = random.choice(roles[role])
    e = init()
    voices = e.getProperty('voices')
    e.setProperty("rate", 200) 
    e.setProperty("voice", voices[12].id)  # set english
    e.say(text)
    e.runAndWait()
    
def log(text):
    if SHOW_RESULT:
        print(text)
        
def sudo_env(command):
    system(f"echo {SYSTEM_PASSWORD} | sudo -S {command}")
from playsound import playsound
import subprocess
from model.config import *
import random
from os import system, path
from pyttsx3 import init
from pygame import mixer
from colorama import init, Fore, Back

init()

def say(text):
    e = init()
    voices = e.getProperty('voices')
    e.setProperty("rate", 200) 
    e.setProperty("voice", voices[12].id)  # set english
    e.say(text)
    e.runAndWait()
    
def sui(file):
    system(f"cvlc --play-and-exit ./model/sounds/{file}.mp3 ")
    
def log(text):
    if SHOW_RESULT:
        print(Back.WHITE + Fore.BLACK + text + Back.RESET + Fore.RESET)
        
def sudo_env(command):
    system(f"echo {SYSTEM_PASSWORD} | sudo -S {command}")
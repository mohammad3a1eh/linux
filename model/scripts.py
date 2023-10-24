from playsound import playsound
from model.config import *
from os import system, path
import pyttsx3
from colorama import init, Fore, Style

init()

def say(text):
    e = pyttsx3.init()

    e.setProperty("rate", 130) 
    e.setProperty('volume', 1)
    e.setProperty("voice", 'english+f3')  # set english
    e.say(text)
    e.runAndWait()
    
def sui(file):
    system(f"cvlc --no-repeat --play-and-exit ./model/sounds/{file}.mp3")
    
def log(text):
    if SHOW_RESULT:
        print("[" + Style.BRIGHT + Fore.LIGHTBLUE_EX + "LOG" + Style.RESET_ALL + Fore.RESET + "]" + f" {text}")
        
def sudo_env(command):
    system(f"echo {SYSTEM_PASSWORD} | sudo -S {command}")
    
def notif_send(title, message):
    print(f"{PATH}/resources/icon.png")
    system(f'notify-send "{title}" "{message}"')
    
def alaram(sleep):
    system("sleep 15s && cvlc --no-repeat --play-and-exit ./model/resources/alaram.mp3")

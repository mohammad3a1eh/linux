from pyautogui import typewrite
from webbrowser import open_new_tab
from pyautogui import keyDown, keyUp, press
from os import system
from model.scripts import sudo_env,say
import requests



def check_connection():
    try:
        _ = requests.head('https://www.google.com/', timeout=5)
        say("i think you are connected")
    except requests.ConnectionError:
        say("i think you are not connected")

def systemctl(value):
    if "blue" in value:
        if "start" in value:
            sudo_env("systemctl start bluetooth")
        elif "stop" in value:
            sudo_env("systemctl stop bluetooth")
            
    elif "air" in value and "mon" in value:
        if "stop" in value:
            sudo_env("airmon-ng stop wlan0mon")
        elif "start" in value:
            sudo_env("airmon-ng stop wlan0mon")


def luncher(value):
    # run terminal

    if "terminal" in value:
        keyDown("ctrl")
        keyDown("alt")
        press("t")
        keyUp("ctrl")
        keyUp("alt")

    # run browser

    elif "browser" in value:
        keyDown("ctrl")
        keyDown("alt")
        press("w")
        keyUp("ctrl")
        keyUp("alt")

def show_(value):
    if "desktop" in value:
            keyDown("win")
            press("d")
            keyUp("win")

    # function for voice type

def typer(value):
    text = value[4:]
    l = len(value.split(" "))
    if l >= 2:
        typewrite(text)
    else:
        pass
    
    # function for voice search
    
def s_google(value):
    text = value[13:]
    l = len(value.split(" "))
    if l > 3:
        open_new_tab(f"https://www.google.com/search?q={text}")
    elif l == 3:
        open_new_tab(f"https://www.google.com/search?q={text}")
    else:
        pass
    
def where_is(value):
    text = value[8:]
    l = len(value.split(" "))
    if l > 3:
        open_new_tab(f"https://www.google.com/maps/place/{text}")
    elif l == 3:
        open_new_tab(f"https://www.google.com/maps/place/{text}")
    else:
        pass
    
def s_youtube(value):
    text = value[14:]
    l = len(value.split(" "))
    if l > 3:
        open_new_tab(f"https://www.youtube.com/results?search_query={text}")
    elif l == 3:
        open_new_tab(f"https://www.youtube.com/results?search_query={text}")
    else:
        pass
    

    
    
def mv_windows(value):
    if "up" in value:
        keyDown("alt")
        keyDown("ctrl")
        press("up")
        keyUp("alt")
        keyUp("ctrl")
    elif "down" in value:
        keyDown("alt")
        keyDown("ctrl")
        press("down")
        keyUp("alt")
        keyUp("ctrl")
    elif "right" in value:
        keyDown("alt")
        keyDown("ctrl")
        press("right")
        keyUp("alt")
        keyUp("ctrl")  
    elif "left" in value:
        keyDown("alt")
        keyDown("ctrl")
        press("left")
        keyUp("alt")
        keyUp("ctrl")
    

from pyautogui import typewrite
from webbrowser import open_new_tab
from pyautogui import keyDown, keyUp, press
from os import system
from model.scripts import sudo_env


def systemctl(value):
    pass


def airmong_stop():
    sudo_env("airmon-ng stop wlan0mon")

def airmong_start():
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
    text = value.split(" ")[1:]
    typewrite(text)
    
    # function for voice search
    
def s_google(value):
    text = value.split(" ")[2:]
    open_new_tab(f"https://www.google.com/search?q={' '.format(text)}")
    
    

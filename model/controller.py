import time
from model.config import SLEEP_TIME
from model.scripts import log
from model.actions import *
from pyautogui import press
from threading import Thread as thread

keys = ['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
'8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
'browserback', 'browserfavorites', 'browserforward', 'browserhome',
'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
'command', 'option', 'optionleft', 'optionright']


def controller(value, start_time):
    log(f"[LOG] {value}")
    if (time.time() - start_time) > SLEEP_TIME:
        return False
    elif "sleep" in value and "now" in value:
        return False   
    
    elif "system" in value[:6]:
        _ = thread(target=systemctl, args=(value,))
        _.start()
    
    # show desktop
    
    elif "show" in value:
        _ = thread(target=show_, args=(value,))
        _.start()
        
    elif "check" in value and "internet" in value or "internet" in value and "connection" in value:
        _ = thread(target=check_connection)
        _.start()

    # move and go to workspace
    
    elif "window" in value or "go to" in value:
        _ = thread(target=mv_windows, args=(value,))
        _.start()    
       
    # take a screenshoot
    
    elif "screen" in value and "shot" in value:
        _ = thread(target=press, args=("prtscr",))
        _.start()
    
    
    elif "open" in value or "run" in value or "launch" in value:
        _ = thread(target=luncher, args=(value,))
        _.start()

            
    # type with voice 
    
    elif "type" in value[:4]:
        _ = thread(target=typer, args=(value,))   
        _.start()

        
    # search with voice
    
    elif "search google" in value[:13]:
        _ = thread(target=s_google, args=(value,))
        _.start()
        
    elif "where is" in value:
        _ = thread(target=where_is, args=(value,))
        _.start()
        
    elif "search youtube" in value[:14]:
        _ = thread(target=s_youtube, args=(value,))
        _.start()
import time
from model.config import SLEEP_TIME
from model.scripts import log
from model.actions import *
from pyautogui import press
from threading import Thread as thread
from random import choice




def controller(value, start_time):
    log(value)
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
        
    elif "where is" in value or "there is":
        _ = thread(target=where_is, args=(value,))
        _.start()
        
    elif "search youtube" in value[:14]:
        _ = thread(target=s_youtube, args=(value,))
        _.start()
        
    elif "what" in value and ( "date" in value or "time" in value ):
        _ = thread(target=date)
        _.start()
        


from playsound import playsound
import subprocess
from model.config import *
import random

types = {
"end" : ["box sound"],
"yes" : ["yes siree"],
"oh" : ['oow nice'],
"accept" : ["oow okay" ,"that's okay" , "oow yeah can do" ,"oow yes, yes man"],
"success" : ["all done"],
"unsuccess" : ['oowhh', "come on"],    
}

def play_text(text):
    subprocess.run(['flite','-t', text, '--setf', f'duration_stretch={DURATION_STRETCH}'])

def play(type):
    audio = random.choice(types[type])
    file_path = f"{PATH_RESOURCE}/{audio}.wav"
    playsound(file_path)
    
def log(text):
    if SHOW_RESULT:
        print(text)
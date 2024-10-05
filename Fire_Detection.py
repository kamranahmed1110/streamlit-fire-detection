import streamlit as st
import cv2
import numpy as np 
import torch
import tempfile
from PIL import Image
import pygame
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import sqlite3
import re
import pandas as pd

# Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT)''')
    conn.commit()
    conn.close()

# Function to authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user


# Function to validate email format
def validate_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email)

def add_user(username, password, email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Combined validation logic
    if any(char.isdigit() for char in username):
        st.error("Username should not contain numbers.")
    elif len(password) < 6:
        st.error("Password should be at least 6 characters.")
    elif not validate_email(email):
        st.error("Invalid email format.")
    else:
        # Check for duplicate email
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = c.fetchone()
        if existing_user:
            st.error("Email already exists.")
        else:
            # Check if username already exists
            c.execute("SELECT * FROM users WHERE username=?", (username,))
            existing_username = c.fetchone()
            if existing_username:
                st.error("Username already exists.")
            else:
                # If all validations pass, add the user
                c.execute('''INSERT INTO users (username, password, email) VALUES (?, ?, ?)''', (username, password, email))
                conn.commit()
                st.success(f'User {username} added successfully!')

    conn.close()

# Function to delete a user from the database
def delete_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

# Function to fetch all users from the database, including passwords
def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, password, email FROM users")
    users = c.fetchall()
    conn.close()
    return users

# Display all users in a table with delete options
def display_users():
    st.subheader("All Users")
    users = get_all_users()
    for user in users:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.write(user[0])  # Username
        col2.write(user[1])  # Password
        col3.write(user[2])  # Email

        if col5.button("Delete", key=f"delete_{user[0]}"):
            delete_user(user[0])
            st.success(f"User {user[0]} deleted successfully!")
            st.experimental_rerun()

# Global variable to keep track of the last email sent time
fire_detected_time = None

def send_email_alert():
    from_address = "mkmuzammil191@gmail.com"
    to_address = "kakakhailkamran321@gmail.com"
    subject = "Fire Alert"
    body = "A fire has been detected in a basement side hurryy do someting!"

    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    global fire_detected_time
    current_time = datetime.now()

    if fire_detected_time is None or current_time - fire_detected_time >= timedelta(minutes=3):
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_address, "uyueuacdlvsagsnf")
            server.send_message(msg)
            server.quit()
            fire_detected_time = current_time
            st.write("Email sent successfully!")
        except Exception as e:
            st.write(f"Failed to send email: {e}")
    else:
        st.write("Email already sent within the last 3 minutes.")

# Initialize pygame for sound
pygame.mixer.init()
alarm_sound = 'alarm.mp3'
pygame.mixer.music.load(alarm_sound)

@st.cache_resource
def load_model():
    model = torch.hub.load('ultralytics/yolov5', 'custom', path="weights/best.pt", force_reload=True)
    return model

def detect_fire_in_image(image):
    model = load_model()
    results = model(image)
    length = len(results.xyxy[0])
    output = np.squeeze(results.render())

    if length > 0:
        pygame.mixer.music.play()
        send_email_alert()

    return output, length

demo_img = "fire.9.png"
demo_video = "Fire_Video.mp4"

# Initialize database
init_db()

# Login functionality
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    login_button = st.button("Login")

    if login_button:
        user = authenticate_user(username, password)
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login()
else:
    st.write("You are logged in!") 
    
st.title('Fire Detection')
st.sidebar.title('App Mode')

app_mode = st.sidebar.selectbox('Choose the App Mode', 
                                ['About App', 'Run on Image', 'Run on Video', 'Run on WebCam', 'User Management'])

if app_mode == 'About App':
    st.subheader("ZAIBTEN OIL REFINERY")
    st.markdown("<h5>This is the Fire Detection App created for Zaibten, an oil company, using custom trained models with YoloV5</h5>", unsafe_allow_html=True)
    st.markdown("<h5>Select the App Mode in the SideBar</h5>", unsafe_allow_html=True)
    st.image("Images/1.gif", use_column_width=True)
    st.markdown("<h5>Upload an image to detect fires</h5>", unsafe_allow_html=True)
    st.image("Images/2.gif", use_column_width=True)
    st.markdown("<h5>Upload a video to detect fires</h5>", unsafe_allow_html=True)
    st.image("Images/3.gif", use_column_width=True)
    st.markdown("<h5>Start the camera for live fire detection</h5>", unsafe_allow_html=True)
    st.image("Images/4.gif", use_column_width=True)
    st.markdown("""
                ## Features
                - Detect on Image
                - Detect on Videos
                - Live Detection
                ## Used Modules
                - Python
                - PyTorch
                - Python CV
                - Streamlit
                - Yolo
                ## python -m streamlit run Fire_Detection.py
                """)

elif app_mode == 'Run on Image':
    st.subheader("Detected Fire:")
    text = st.markdown("")

    st.sidebar.markdown("---")
    img_file = st.sidebar.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
    if img_file:
        image = np.array(Image.open(img_file))
    else:
        image = np.array(Image.open(demo_img))

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Original Image**")
    st.sidebar.image(image)

    output, length = detect_fire_in_image(image)
    text.write(f"<h1 style='text-align: center; color:red;'>{length}</h1>", unsafe_allow_html=True)
    st.subheader("Output Image")
    st.image(output, use_column_width=True)

elif app_mode == 'Run on Video':
    st.subheader("Detected Fire:")
    text = st.markdown("")

    st.sidebar.markdown("---")
    st.subheader("Output")
    stframe = st.empty()

    video_file = st.sidebar.file_uploader("Upload a Video", type=['mp4', 'mov', 'avi', 'asf', 'm4v'])
    st.sidebar.markdown("---")
    tffile = tempfile.NamedTemporaryFile(delete=False)

    if not video_file:
        vid = cv2.VideoCapture(demo_video)
        tffile.name = demo_video
    else:
        tffile.write(video_file.read())
        vid = cv2.VideoCapture(tffile.name)

    st.sidebar.markdown("**Input Video**")
    st.sidebar.video(tffile.name)

    while vid.isOpened():
        ret, frame = vid.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output, length = detect_fire_in_image(frame)
        text.write(f"<h1 style='text-align: center; color:red;'>{length}</h1>", unsafe_allow_html=True)
        stframe.image(output)

elif app_mode == 'Run on WebCam':
    st.subheader("Detected Fire:")
    text = st.markdown("")

    st.sidebar.markdown("---")
    st.subheader("Output")
    stframe = st.empty()

    run = st.sidebar.button("Start")
    stop = st.sidebar.button("Stop")
    st.sidebar.markdown("---")

    cam = cv2.VideoCapture(0)
    if run:
        while True:
            if stop:
                break
            ret, frame = cam.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            output, length = detect_fire_in_image(frame)
            text.write(f"<h1 style='text-align: center; color:red;'>{length}</h1>", unsafe_allow_html=True)
            stframe.image(output)

# Modify the user management section to include the display_users function
elif app_mode == 'User Management':
    st.subheader("User Management")
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    email = st.text_input('Email')
    submit = st.button('Submit')

    if submit:
        if username and password and email:
            try:
                add_user(username, password, email)
            except sqlite3.IntegrityError:
                st.error(f'User {username} already exists!')
        else:
            st.error('Please fill out all fields')

    display_users()  # Call the display_users function to show the user table with delete options
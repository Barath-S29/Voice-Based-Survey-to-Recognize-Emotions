import os
import wave
import numpy as np
import parselmouth
import pyaudio
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from flask import Flask, render_template, request
import threading
import emotion_gui
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio


app = Flask(__name__)

# Function to record real-time audio from the microphone
def record_audio():
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    fs = 44100
    seconds = 3

    p = pyaudio.PyAudio()
    print("Recording...")

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []

    for i in range(0, int(fs / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Generate a unique filename for the recorded audio
    unique_filename = str(uuid.uuid4()) + ".wav"
    audio_file_path = os.path.join("recordings", unique_filename)

    # Save the recorded audio as a WAV file
    os.makedirs("recordings", exist_ok=True)  # Create the 'recordings' directory if it doesn't exist
    wf = wave.open(audio_file_path, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()

    return audio_file_path

def send_email(predicted_emotion, name, audio_file_path):
    # Email configuration
    smtp_server = "smtp.gmail.com"  # Replace with your SMTP server address
    smtp_port = 587  # Replace with your SMTP server port
    sender_email = "sender_mail"  # Replace with your sender email address
    sender_password = "sender_app_password"  #Refer https://www.getmailbird.com/gmail-app-password/   # Replace with your sender email password
    receiver_email = "receiver_mail"  # Replace with the receiver email address

    # Create the email message
    subject = f"Emotion Prediction for {name}"
    body = f"Patient {name},\n\nResult. The predicted emotion is: {predicted_emotion}.\n\nBest regards,\nYour Emotion Survey Team"
    
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Attach the audio file to the email
    with open(audio_file_path, 'rb') as f:
        audio_part = MIMEAudio(f.read(), name=os.path.basename(audio_file_path))
        msg.attach(audio_part)

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print("Failed to send email.")
        print(e)

def play_recorded_audio(audio_file_path):
    chunk = 1024
    wf = wave.open(audio_file_path, 'rb')
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(chunk)

    print("The recorded audio : ")
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()

# Function to process the recorded audio and extract prosody features
def process_recorded_audio(audio_file_path):
    features = extract_prosody_features(audio_file_path)
    return features

# Function to extract prosody features from an audio file
def extract_prosody_features(audio_file):
    # Load the audio file using parselmouth
    snd = parselmouth.Sound(audio_file)

    # Extract prosody features using the Praat pitch and intensity objects
    pitch = snd.to_pitch()
    intensity = snd.to_intensity()

    # Calculate mean and standard deviation of pitch
    pitch_values = pitch.selected_array['frequency']
    pitch_mean = np.mean(pitch_values)
    pitch_std = np.std(pitch_values)

    # Calculate mean and standard deviation of intensity
    intensity_values = intensity.values[0]
    intensity_mean = np.mean(intensity_values)
    intensity_std = np.std(intensity_values)

    # You can add more prosody features as needed (e.g., formants, jitter, shimmer)

    # Return the extracted features as a numpy array
    return np.array([pitch_mean, pitch_std, intensity_mean, intensity_std])

# Load the dataset and extract prosody features
def load_dataset(data_dir):
    X = []  # List to store the extracted features
    y = []  # List to store the corresponding emotion labels

    for emotion in os.listdir(data_dir):
        emotion_dir = os.path.join(data_dir, emotion)
        if os.path.isdir(emotion_dir):
            for audio_file in os.listdir(emotion_dir):
                audio_path = os.path.join(emotion_dir, audio_file)
                features = extract_prosody_features(audio_path)
                X.append(features)
                y.append(emotion)

    return np.array(X), np.array(y)

def train_svm_model(X_train, y_train):
    svm_classifier = SVC(kernel='linear', C=1.0)
    svm_classifier.fit(X_train, y_train)
    return svm_classifier

# Route to display the survey form
@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        survey_responses = []
        for i in range(len(survey_questions)):
            response_index = int(request.form[f'q{i}'])
            survey_responses.append(survey_questions[i]['choices'][response_index])

        # Record and process real-time audio
        audio_file_path = record_audio()
        if audio_file_path:
            features = process_recorded_audio(audio_file_path)
            predicted_emotion = svm_model.predict([features])[0]
            print("Predicted Emotion:", predicted_emotion)

            # Get the name input from the survey form
            name = request.form.get('name')  # Replace 'name' with the actual name input field name

            # Display the predicted emotion in the GUI
            threading.Thread(target=emotion_gui.show_emotion_gui, args=(predicted_emotion, name)).start()

            # Send the predicted emotion details as an email
            threading.Thread(target=send_email, args=(predicted_emotion, name, audio_file_path)).start()

        # You can save the survey_responses and predicted_emotion to a database here
        # For this example, we'll just print them
        print("Survey Responses:", survey_responses)

        # Return a thank-you message after form submission
        return render_template('thank_you.html', predicted_emotion=predicted_emotion)

    # Render the survey form template with the survey_questions data
    return render_template('survey_form.html', survey_questions=survey_questions)

if __name__ == "__main__":
    data_directory = r"Folder_containing_emotions_dataset"  # Replace with the folder containing the EmoReact audio files

    # Load the dataset and extract prosody features
    X, y = load_dataset(data_directory)

    if len(X) == 0:
        print("No audio files found in the dataset folder.")
    else:
        # Split the dataset into training and testing sets
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the SVM model
        svm_model = train_svm_model(X_train, y_train)

    # Survey questions
    survey_questions = [
        {
            'question': 'Tell me about yourself?',
            'choices': ['Yes', 'No']
        },
        {
            'question': 'Do you feel stressed about your work?',
            'choices': ['Yes', 'No']
        },
        {
            'question': 'Do you feel overwhelmed by your work?',
            'choices': ['Yes', 'No']
        }
        # Add more questions here
    ]

    # Run the Flask app
    app.run(debug=True)

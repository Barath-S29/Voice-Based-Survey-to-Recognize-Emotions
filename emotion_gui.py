import tkinter as tk

# Function to display the predicted emotion and name in a GUI window
def show_emotion_gui(predicted_emotion, name):
    root = tk.Tk()
    root.title("Predicted Emotion")

    # Define the GUI layout
    root.geometry("400x300")
    label_name = tk.Label(root, text=f"Name: {name}", font=("Arial", 16))
    label_name.pack()# Set the size of the window

    # Function to close the GUI window
    def close_window():
        root.destroy()

    # Map emotions to corresponding emojis
    emoji_mapping = {
        "Happiness": "😄",
        "Sad": "😢",
        "Angry": "😠",
        "Fear": "😨",
        "Neutral": "😐"
    }

    # Frame to hold the emoji and emotion label
    frame = tk.Frame(root)
    frame.pack(pady=20)

    # Display the emoji for the predicted emotion
    emoji = emoji_mapping.get(predicted_emotion, "😶")
    emoji_label = tk.Label(frame, text=emoji, font=("Arial", 60))
    emoji_label.grid(row=0, column=0, padx=20)

    # Display the predicted emotion text
    emotion_label = tk.Label(frame, text=predicted_emotion, font=("Arial", 30))
    emotion_label.grid(row=0, column=1)

    # Frame to hold the close button
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)

    # Close button
    close_button = tk.Button(button_frame, text="Close", command=close_window, font=("Arial", 16))
    close_button.pack()

    # Run the GUI event loop
    root.mainloop()

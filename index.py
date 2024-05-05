import cv2
import face_recognition
import os
import glob
import numpy as np
import tkinter as tk
import pywhatkit
from PIL import Image, ImageTk
from tkinter import messagebox


class SimpleFacerec:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.frame_resizing = 0.5

    def load_encoding_images(self, images_path):
        # Corrected path pattern to ensure it loads image files
        images_path = glob.glob(os.path.join(images_path, "*.*"))  
        print(f"{len(images_path)} encoding images found.")

        for img_path in images_path:
            img = face_recognition.load_image_file(img_path)
            img_encoding = face_recognition.face_encodings(img)[0]

            basename = os.path.basename(img_path)
            filename, _ = os.path.splitext(basename)
            self.known_face_encodings.append(img_encoding)
            self.known_face_names.append(filename)
        print("Encoding images loaded")

    def detect_known_faces(self, frame):
        # Resizing and converting to RGB
        small_frame = cv2.resize(frame, (0, 0), fx=self.frame_resizing, fy=self.frame_resizing)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detecting face locations and encodings
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
            face_names.append(name)

        # Re-scale the locations to the original frame size
        face_locations = np.array(face_locations) / self.frame_resizing
        return face_locations.astype(int), face_names


class App:
    def __init__(self, root):
        self.root = root
        self.sfr = SimpleFacerec()  # Initialize SimpleFacerec
        self.video_capture = None
        self.canvas = None
        self.start_button = None
        self.capture_button = None
        self.stop_button = None

        self.sfr.load_encoding_images(r"C:\Users\shalini\Documents\SIM\new code\images")  # Corrected path pattern

        self.setup_ui()

    def setup_ui(self):
        self.root.title("Face Recognition")
        self.root.geometry("800x600")

        self.canvas = tk.Canvas(self.root, width=640, height=480)
        self.canvas.pack()

        self.start_button = tk.Button(self.root, text="Start", command=self.start_video)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.capture_button = tk.Button(self.root, text="Capture", command=self.capture_image)
        self.capture_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_video)
        self.stop_button.pack(side=tk.LEFT, padx=10)

    def start_video(self):
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            print("Failed to open video capture device")
            return

        self.show_frame()

    def show_frame(self):
        ret, frame = self.video_capture.read()

        if not ret:
            return

        # Detect known faces
        face_locations, face_names = self.sfr.detect_known_faces(frame)
        for face_loc, name in zip(face_locations, face_names):
            y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]

            # Add text and rectangle to recognized faces
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

            if name != "Unknown":
                self.capture_and_send_message(frame)

        # Convert to PIL image for Tkinter
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image)
        self.canvas.image = image

        self.root.after(15, self.show_frame)  # Schedule next frame update

    def capture_and_send_message(self, frame):
        # Capture image
        cv2.imwrite("captured_image.png", frame)
        print("Image captured.")

        # Send WhatsApp message
        try:
            pywhatkit.sendwhatmsg_instantly("+911234567890", "Face detected!")
            print("WhatsApp message sent.")
        except Exception as e:
            print(f"Failed to send WhatsApp message: {e}")

    def capture_image(self):
        if self.video_capture:
            ret, frame = self.video_capture.read()
            if ret:
                # Detect and mark faces
                face_locations, face_names = self.sfr.detect_known_faces(frame)
                for face_loc, name in zip(face_locations, face_names):
                    y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], x1
                    cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

                cv2.imwrite("captured_image.png", frame)  # Save image
                messagebox.showinfo("Image Captured", "Image saved as captured_image.png")

    def stop_video(self):
        if self.video_capture:
            self.video_capture.release()  # Release the video capture
            self.video_capture = None


# Running the app
if __name__ == "__main__":
    root = tk.Tk()  # Initialize Tkinter
    app = App(root)  # Instantiate the App class
    root.mainloop()  # Start the Tkinter event loop

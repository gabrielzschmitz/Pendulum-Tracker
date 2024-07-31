"""
Live Video Stream with Object Detection and Centroid Display

This Python script captures video from the default camera using OpenCV, applies
color filtering based on HSV values, detects the largest contour within the
specified color range, and displays the centroid of the detected object.
The script is designed to be used with Flask for creating a web-based live
video stream.

Requirements:
- OpenCV (cv2) library must be installed.
- Flask library must be installed.

Usage:
1. Run the script.
2. Access the live video stream by navigating to the provided URL
(usually http://127.0.0.1:5000/) in a web browser.
3. The webcam feed, along with the color-filtered mask and centroid display,
will be shown.
4. Use 'quit' in the command submission to exit the application.

Note: The script assumes the use of a camera with Video4Linux2 (V4L2) interface.
"""

# Import necessary libraries
from flask import Flask, render_template, Response, request, redirect, url_for, jsonify
import numpy as np
import signal
import time
import cv2
import os


# Initialize the Flask application
flask_app = Flask(__name__)

# Open the default camera using Video4Linux2 (V4L2) interface
# if os.environ.get("WERKZEUG_RUN_MAIN") or Flask.debug is False:
#    camera = cv2.VideoCapture(2, cv2.CAP_V4L2)
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

# Initialize variables to store centroid position and other flags
pendulum = [0.0, 0.0, (0.0, 0.0), (0.0, 0.0)]
x_medium, y_medium = 0, 0
quit_flag = False
camera_flag = "frame"
tracking_flag = False
countdown_flag = False
selected_color = "base"
hMin, hMax, sMin, sMax, vMin, vMax = 0, 179, 0, 255, 0, 255
hMin_green, hMax_green, sMin_green, sMax_green, vMin_green, vMax_green = (
    37,
    90,
    34,
    115,
    33,
    189,
)
hMin_yellow, hMax_yellow, sMin_yellow, sMax_yellow, vMin_yellow, vMax_yellow = (
    18,
    26,
    116,
    229,
    90,
    246,
)
hMin_magenta, hMax_magenta, sMin_magenta, sMax_magenta, vMin_magenta, vMax_magenta = (
    107,
    125,
    43,
    113,
    76,
    113,
)

last_detection_time = time.time()
path_points = [(0.0, 0.0)]
countdown_time = 6


@flask_app.route("/update_selected_color", methods=["POST"])
def update_selected_color():
    color = request.form.get("selectedColor")
    global selected_color
    selected_color = color
    return "Color updated successfully"


# Route to update the color range
@flask_app.route("/update_color_range", methods=["GET"])
def update_color_range():
    global hMin, hMax, sMin, sMax, vMin, vMax, x_medium, y_medium, hMin_green, hMax_green, sMin_green, sMax_green, vMin_green, vMax_green, hMin_yellow, hMax_yellow, sMin_yellow, sMax_yellow, vMin_yellow, vMax_yellow, hMin_magenta, hMax_magenta, sMin_magenta, sMax_magenta, vMin_magenta, vMax_magenta
    color_range = request.args.get("colorRange", "base")

    if color_range == "green":
        hMin_green, hMax_green, sMin_green, sMax_green, vMin_green, vMax_green = (
            37,
            90,
            34,
            115,
            33,
            189,
        )
    elif color_range == "yellow":
        hMin_yellow, hMax_yellow, sMin_yellow, sMax_yellow, vMin_yellow, vMax_yellow = (
            18,
            26,
            116,
            229,
            90,
            246,
        )
    elif color_range == "magenta":
        (
            hMin_magenta,
            hMax_magenta,
            sMin_magenta,
            sMax_magenta,
            vMin_magenta,
            vMax_magenta,
        ) = (
            107,
            125,
            43,
            113,
            76,
            113,
        )
    else:  # Default to base color range
        hMin, hMax, sMin, sMax, vMin, vMax = 0, 179, 0, 255, 0, 255

    return "OK"


# Function to load HSV values from a file
def load_hsv_values():
    global hMin, hMax, sMin, sMax, vMin, vMax, x_medium, y_medium, hMin_green, hMax_green, sMin_green, sMax_green, vMin_green, vMax_green, hMin_yellow, hMax_yellow, sMin_yellow, sMax_yellow, vMin_yellow, vMax_yellow, hMin_magenta, hMax_magenta, sMin_magenta, sMax_magenta, vMin_magenta, vMax_magenta

    try:
        with open("hsv_values.txt", "r") as file:
            lines = file.readlines()

        # Extract HSV values from the file
        hsv_values = {
            line.split(":")[0].strip(): int(line.split(":")[1].strip())
            for line in lines
        }

        # Update the HSV variables
        hMin = hsv_values.get("hMin", hMin)
        hMax = hsv_values.get("hMax", hMax)
        sMin = hsv_values.get("sMin", sMin)
        sMax = hsv_values.get("sMax", sMax)
        vMin = hsv_values.get("vMin", vMin)
        vMax = hsv_values.get("vMax", vMax)
        hMin_green = hsv_values.get("hMin_green", hMin_green)
        hMax_green = hsv_values.get("hMax_green", hMax_green)
        sMin_green = hsv_values.get("sMin_green", sMin_green)
        sMax_green = hsv_values.get("sMax_green", sMax_green)
        vMin_green = hsv_values.get("vMin_green", vMin_green)
        vMax_green = hsv_values.get("vMax_green", vMax_green)
        hMin_yellow = hsv_values.get("hMin_yellow", hMin_yellow)
        hMax_yellow = hsv_values.get("hMax_yellow", hMax_yellow)
        sMin_yellow = hsv_values.get("sMin_yellow", sMin_yellow)
        sMax_yellow = hsv_values.get("sMax_yellow", sMax_yellow)
        vMin_yellow = hsv_values.get("vMin_yellow", vMin_yellow)
        vMax_yellow = hsv_values.get("vMax_yellow", vMax_yellow)
        hMin_magenta = hsv_values.get("hMin_magenta", hMin_magenta)
        hMax_magenta = hsv_values.get("hMax_magenta", hMax_magenta)
        sMin_magenta = hsv_values.get("sMin_magenta", sMin_magenta)
        sMax_magenta = hsv_values.get("sMax_magenta", sMax_magenta)
        vMin_magenta = hsv_values.get("vMin_magenta", vMin_magenta)
        vMax_magenta = hsv_values.get("vMax_magenta", vMax_magenta)

    except FileNotFoundError:
        pass  # File not found, use default values


# Load HSV values when the script starts
load_hsv_values()


def generate_frames(select):
    """
    Generate video frames from the camera stream.

    Yields:
        bytes: JPEG-encoded frame bytes.
    """
    global x_medium, y_medium, quit_flag

    while not quit_flag:
        # Read a frame from the camera
        success, frame = camera.read()

        if not success:
            break

        # Process the frame based on the selected option
        frame = process_frame(frame, select)

        # Encode the frame as JPEG
        _, jpeg = cv2.imencode(".jpg", frame)
        frame_bytes = jpeg.tobytes()

        # Yield the frame bytes for video streaming
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


def euclidian(p1, p2):
    """p1 and p2 in format (x1,y1) and (x2,y2) tuples"""
    distance = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
    return distance


def process_frame(frame, select):
    """
    Process a single frame from the camera stream.

    Args:
        frame (numpy.ndarray): Input frame.

    Returns:
        numpy.ndarray: Processed frame.
    """
    global last_detection_time, path_points, quit_flag, hMin, hMax, sMin, sMax, vMin, vMax, x_medium, y_medium, pendulum, hMin_green, hMax_green, sMin_green, sMax_green, vMin_green, vMax_green, hMin_yellow, hMax_yellow, sMin_yellow, sMax_yellow, vMin_yellow, vMax_yellow, hMin_magenta, hMax_magenta, sMin_magenta, sMax_magenta, vMin_magenta, vMax_magenta

    x_medium_green = 0.0
    y_medium_green = 0.0
    x_medium_yellow = 0.0
    y_medium_yellow = 0.0
    x_medium_magenta = 0.0
    y_medium_magenta = 0.0

    # Flip the webcam
    frame = cv2.flip(frame, 1)
    frame_green = frame.copy()
    frame_yellow = frame.copy()
    frame_magenta = frame.copy()

    # Define the lower and upper bounds of the color mask based on HSV values
    low_green_mask = np.array([hMin_green, sMin_green, vMin_green])
    high_green_mask = np.array([hMax_green, sMax_green, vMax_green])
    low_yellow_mask = np.array([hMin_yellow, sMin_yellow, vMin_yellow])
    high_yellow_mask = np.array([hMax_yellow, sMax_yellow, vMax_yellow])
    low_magenta_mask = np.array([hMin_magenta, sMin_magenta, vMin_magenta])
    high_magenta_mask = np.array([hMax_magenta, sMax_magenta, vMax_magenta])
    low_mask = np.array([hMin, sMin, vMin])
    high_mask = np.array([hMax, sMax, vMax])

    # Convert the frame to the HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv_frame_green = cv2.cvtColor(frame_green, cv2.COLOR_BGR2HSV)
    hsv_frame_yellow = cv2.cvtColor(frame_yellow, cv2.COLOR_BGR2HSV)
    hsv_frame_magenta = cv2.cvtColor(frame_magenta, cv2.COLOR_BGR2HSV)
    if select == "hsv":
        return hsv_frame

    # Create a binary mask based on the HSV values
    mask = cv2.inRange(hsv_frame, low_mask, high_mask)
    mask_green = cv2.inRange(hsv_frame_green, low_green_mask, high_green_mask)
    mask_yellow = cv2.inRange(hsv_frame_yellow, low_yellow_mask, high_yellow_mask)
    mask_magenta = cv2.inRange(hsv_frame_magenta, low_magenta_mask, high_magenta_mask)
    if select == "mask":
        if selected_color == "green":
            return mask_green
        elif selected_color == "yellow":
            return mask_yellow
        elif selected_color == "magenta":
            return mask_magenta
        else:
            return mask

    # Apply the color mask to the original frame
    preview_mask = cv2.bitwise_and(frame, frame, mask=mask)
    preview_mask_green = cv2.bitwise_and(frame_green, frame_green, mask=mask_green)
    preview_mask_yellow = cv2.bitwise_and(frame_yellow, frame_yellow, mask=mask_yellow)
    preview_mask_magenta = cv2.bitwise_and(
        frame_magenta, frame_magenta, mask=mask_magenta
    )
    if select == "preview":
        if selected_color == "green":
            return preview_mask_green
        elif selected_color == "yellow":
            return preview_mask_yellow
        elif selected_color == "magenta":
            return preview_mask_magenta
        else:
            return preview_mask

    # Find contours in the binary mask
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

    contours_green, _ = cv2.findContours(
        mask_green, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    contours_green = sorted(
        contours_green, key=lambda x: cv2.contourArea(x), reverse=True
    )
    contours_yellow, _ = cv2.findContours(
        mask_yellow, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    contours_yellow = sorted(
        contours_yellow, key=lambda x: cv2.contourArea(x), reverse=True
    )
    contours_magenta, _ = cv2.findContours(
        mask_magenta, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    contours_magenta = sorted(
        contours_magenta, key=lambda x: cv2.contourArea(x), reverse=True
    )

    x_green, y_green, w_green, h_green = 0, 0, 0, 0
    x_yellow, y_yellow, w_yellow, h_yellow = 0, 0, 0, 0
    x_magenta, y_magenta, w_magenta, h_magenta = 0, 0, 0, 0
    x, y, w, h = 0, 0, 0, 0

    for cnt in contours_green:
        # Get the bounding box of the largest contour
        x_green, y_green, w_green, h_green = cv2.boundingRect(cnt)
        x_medium_green, y_medium_green = int((x_green + x_green + w_green) / 2), int(
            (y_green + y_green + h_green) / 2
        )

        break

    for cnt in contours_yellow:
        # Get the bounding box of the largest contour
        x_yellow, y_yellow, w_yellow, h_yellow = cv2.boundingRect(cnt)
        x_medium_yellow, y_medium_yellow = int(
            (x_yellow + x_yellow + w_yellow) / 2
        ), int((y_yellow + y_yellow + h_yellow) / 2)

        break

    for cnt in contours_magenta:
        # Get the bounding box of the largest contour
        x_magenta, y_magenta, w_magenta, h_magenta = cv2.boundingRect(cnt)
        x_medium_magenta, y_medium_magenta = int(
            (x_magenta + x_magenta + w_magenta) / 2
        ), int((y_magenta + y_magenta + h_magenta) / 2)

        break

    for cnt in contours:
        # Get the bounding box of the largest contour
        x, y, w, h = cv2.boundingRect(cnt)
        # Calculate the centroid of the bounding box
        x_medium, y_medium = int((x + x + w) / 2), int((y + y + h) / 2)

        break

    if countdown_flag is False:
        base_green = (x_medium_green, y_medium_green)
        base_yellow = (x_medium_yellow, y_medium_yellow)
        magenta_point = (x_medium_magenta, y_medium_magenta)
        ball = (x_medium, y_medium)
        ratio_and_length = get_length_and_ratio(
            base_green, base_yellow, magenta_point, ball
        )
        pendulum[0] = ratio_and_length[0]
        pendulum[1] = ratio_and_length[1]
        pendulum[2] = ball
        pendulum[3] = ball
        ratio_and_length = (pendulum[0], pendulum[1])
        write_pendulum_values(pendulum[0], pendulum[1], pendulum[2], pendulum[3])

    if tracking_flag:
        if path_points:
            pendulum[3] = path_points[-1]
        write_pendulum_values(pendulum[0], pendulum[1], pendulum[2], pendulum[3])

    # Draw bounding box and path lines on the frame
    if tracking_flag and w > 10 and h > 10 and w < 500 and h < 500:
        # Update the last detection time
        last_detection_time = time.time()

        # Store the centroid point in the list
        path_points.append((x_medium, y_medium))

        # Draw lines connecting consecutive points in the path
        for i in range(1, len(path_points)):
            cv2.line(frame, path_points[i - 1], path_points[i], (0, 255, 0), 2)

    # Clear path_points if there is no detection for a certain period (e.g., 5 seconds)
    if time.time() - last_detection_time > 5:
        path_points = []

    return frame


def get_length_and_ratio(base_green, base_yellow, magenta_point, ball):
    distance_point = euclidian(magenta_point, base_yellow)
    distance_base = euclidian(base_green, base_yellow)
    distance_ball = euclidian(magenta_point, ball)
    ratio = 0.0
    realdistance_ball = 0.0
    if distance_base != 0:
        ratio = 56.5 / distance_point
        realdistance_ball = distance_ball * ratio
    return ratio, realdistance_ball


def write_pendulum_values(ratio, length, point0, current_point):
    global tracking_flag
    if tracking_flag is False:
        flag = 0
    else:
        flag = 1
    lst0 = list(point0)
    point0_x = lst0[0]
    point0_y = lst0[1]
    current_point_x = current_point[0]
    current_point_y = current_point[1]
    with open("pendulum_values.txt", "w") as file:
        file.write(
            f"Ratio: {ratio}\nLength: {length}\nPoint 0 X: {point0_x}\nPoint 0 Y: {point0_y}\nCurrent Point X: {current_point_x}\nCurrent Point Y: {current_point_y}\nFlag: {flag}"
        )


@flask_app.route("/video_feed")
def video_feed():
    """
    Flask route for video feed.

    Returns:
        Response: Video feed response.
    """
    return Response(
        generate_frames(camera_flag),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def quit_application():
    """
    Function to quit the application.

    Saves the current HSV values to a file before exiting.
    """
    global quit_flag, hMin, hMax, sMin, sMax, vMin, vMax, hMin_green, hMax_green, sMin_green, sMax_green, vMin_green, vMax_green, hMin_yellow, hMax_yellow, sMin_yellow, sMax_yellow, vMin_yellow, vMax_yellow, hMin_magenta, hMax_magenta, sMin_magenta, sMax_magenta, vMin_magenta, vMax_magenta

    # Save HSV values to a file
    with open("hsv_values.txt", "w") as file:
        file.write(
            f"hMin: {hMin}\nhMin_green: {hMin_green}\nhMin_yellow:{hMin_yellow}\nhMin_magenta: {hMin_magenta}\n"
        )
        file.write(
            f"hMax: {hMax}\nhMax_green: {hMax_green}\nhMax_yellow:{hMax_yellow}\nhMax_magenta: {hMax_magenta}\n"
        )
        file.write(
            f"sMin: {sMin}\nsMin_green: {sMin_green}\nsMin_yellow:{sMin_yellow}\nsMin_magenta: {sMin_magenta}\n"
        )
        file.write(
            f"sMax: {sMax}\nsMax_green: {sMax_green}\nsMax_yellow:{sMax_yellow}\nsMax_magenta: {sMax_magenta}\n"
        )
        file.write(
            f"vMin: {vMin}\nvMin_green: {vMin_green}\nvMin_yellow:{vMin_yellow}\nvMin_magenta: {vMin_magenta}\n"
        )
        file.write(
            f"vMax: {vMax}\nvMax_green: {vMax_green}\nvMax_yellow:{vMax_yellow}\nvMax_magenta: {vMax_magenta}\n"
        )

    # Set the quit flag to True
    quit_flag = True

    # Send a signal to terminate the script
    camera.release()
    cv2.destroyAllWindows()
    os.kill(os.getpid(), signal.SIGINT)


# Initialize a list of commands to cycle through
commands = ["frame", "hsv", "preview", "mask"]


def cycle_camera_commands():
    """
    Function to cycle camera through commands.
    """
    global camera_flag
    current_index = commands.index(camera_flag)
    next_index = (current_index + 1) % len(commands)
    camera_flag = commands[next_index]


@flask_app.route("/update_hsv", methods=["POST"])
def update_hsv():
    """
    Flask route to update HSV values.

    Returns:
        str: Status message.
    """
    global hMin, hMax, sMin, sMax, vMin, vMax, hMin_green, hMax_green, sMin_green, sMax_green, vMin_green, vMax_green, hMin_yellow, hMax_yellow, sMin_yellow, sMax_yellow, vMin_yellow, vMax_yellow, hMin_magenta, hMax_magenta, sMin_magenta, sMax_magenta, vMin_magenta, vMax_magenta

    # Update HSV values based on the form submission
    hMin = int(request.form["hMin"])
    hMax = int(request.form["hMax"])
    sMin = int(request.form["sMin"])
    sMax = int(request.form["sMax"])
    vMin = int(request.form["vMin"])
    vMax = int(request.form["vMax"])
    hMin_green = int(request.form["hMin_green"])
    hMax_green = int(request.form["hMax_green"])
    sMin_green = int(request.form["sMin_green"])
    sMax_green = int(request.form["sMax_green"])
    vMin_green = int(request.form["vMin_green"])
    vMax_green = int(request.form["vMax_green"])
    hMin_yellow = int(request.form["hMin_yellow"])
    hMax_yellow = int(request.form["hMax_yellow"])
    sMin_yellow = int(request.form["sMin_yellow"])
    sMax_yellow = int(request.form["sMax_yellow"])
    vMin_yellow = int(request.form["vMin_yellow"])
    vMax_yellow = int(request.form["vMax_yellow"])
    hMin_magenta = int(request.form["hMin_magenta"])
    hMax_magenta = int(request.form["hMax_magenta"])
    sMin_magenta = int(request.form["sMin_magenta"])
    sMax_magenta = int(request.form["sMax_magenta"])
    vMin_magenta = int(request.form["vMin_magenta"])
    vMax_magenta = int(request.form["vMax_magenta"])

    return "OK"


def start_tracking_with_countdown():
    global tracking_flag, countdown_time, countdown_flag

    countdown_flag = True
    countdown_time = 5
    while countdown_time > -1:
        time.sleep(1)
        countdown_time -= 1

    tracking_flag = True


@flask_app.route("/get_countdown", methods=["GET"])
def get_countdown():
    """
    Flask route to get the countdown value.

    Returns:
        Response: JSON response containing the countdown value.
    """
    global countdown_time
    return jsonify({"countdown_time": countdown_time})


def get_tracking_button_info():
    if tracking_flag:
        return "Stop Tracking", "stop-tracking"
    else:
        return "Start Tracking", ""


@flask_app.route("/submit_command", methods=["POST"])
def submit_command():
    """
    Flask route to handle form submission.

    Returns:
        str: Status message.
    """
    global camera_flag, tracking_flag, countdown_time, countdown_flag
    # Get the command from the form submission
    command = request.form.get("command", "")

    if command.lower() == "quit":
        # Quit the application if the 'quit' command is received
        quit_application()
    elif command.lower() == "cycle":
        # Cycle through camera commands if the 'cycle' command is received
        cycle_camera_commands()
    elif command.lower() == "start_tracking":
        if tracking_flag is False:
            countdown_flag = True
            start_tracking_with_countdown()
        else:
            tracking_flag = False
            countdown_flag = False
            countdown_time = 6

    return redirect(url_for("index"))


@flask_app.route("/")
def index():
    """
    Flask route for the home page.

    Returns:
        str: Rendered template content.
    """
    global hMin, hMax, sMin, sMax, vMin, vMax, hMin_green, hMax_green, sMin_green, sMax_green, vMin_green, vMax_green, hMin_yellow, hMax_yellow, sMin_yellow, sMax_yellow, vMin_yellow, vMax_yellow, hMin_magenta, hMax_magenta, sMin_magenta, sMax_magenta, vMin_magenta, vMax_magenta, countdown_time

    button_text, button_class = get_tracking_button_info()

    # Define Plot Data
    labels = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
    ]

    data = [0, 10, 15, 8, 22, 18, 25]

    # Render the HTML template with the current HSV values and countdown time
    return render_template(
        "index.html",
        hMin=hMin,
        hMax=hMax,
        sMin=sMin,
        sMax=sMax,
        vMin=vMin,
        vMax=vMax,
        hMin_green=hMin_green,
        hMax_green=hMax_green,
        sMin_green=sMin_green,
        sMax_green=sMax_green,
        vMin_green=vMin_green,
        vMax_green=vMax_green,
        hMin_yellow=hMin_yellow,
        hMax_yellow=hMax_yellow,
        sMin_yellow=sMin_yellow,
        sMax_yellow=sMax_yellow,
        vMin_yellow=vMin_yellow,
        vMax_yellow=vMax_yellow,
        hMin_magenta=hMin_magenta,
        hMax_magenta=hMax_magenta,
        sMin_magenta=sMin_magenta,
        sMax_magenta=sMax_magenta,
        vMin_magenta=vMin_magenta,
        vMax_magenta=vMax_magenta,
        countdown_time=countdown_time,
        button_text=button_text,
        button_class=button_class,
        data=data,
        labels=labels,
    )

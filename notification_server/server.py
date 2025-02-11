try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Error: Flask is not installed. Please run:")
    print("pip install flask")
    exit(1)

try:
    from win10toast import ToastNotifier
except ImportError:
    print("Error: win10toast is not installed. Please run:")
    print("pip install win10toast")
    exit(1)

import winsound
import os
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
toaster = ToastNotifier()

# Get the directory containing this script
SCRIPT_DIR = Path(__file__).parent.absolute()
SOUND_FILE = SCRIPT_DIR / "sounds" / "alarm.wav"


@app.route("/notify", methods=["POST"])
def notify():
    logger.debug("Received notification request")
    try:
        data = request.get_json()
        message = data.get("message", "Alarm notification!")
        logger.debug("Notification message: %s", message)

        logger.debug("Showing Windows toast notification")
        toaster.show_toast("Alarm Notification", message, duration=10, threaded=True)

        if SOUND_FILE.exists():
            logger.debug("Playing sound file: %s", SOUND_FILE)
            winsound.PlaySound(str(SOUND_FILE), winsound.SND_FILENAME)
        else:
            logger.debug("Playing default system sound")
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

        logger.info("Notification processed successfully")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error("Error processing notification: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    logger.info("Starting notification server")
    if not SOUND_FILE.parent.exists():
        logger.debug("Creating sounds directory")
        SOUND_FILE.parent.mkdir(parents=True)

    logger.info("Server starting on port %s", 5000)
    logger.info("Sound file location: %s", SOUND_FILE)
    app.run(host="0.0.0.0", port=5000)

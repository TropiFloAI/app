import os
import threading
import time
from pyngrok import ngrok

# 1. Set your app filename here
APP_FILENAME = "app.py"  # Change this if your file has a different name

# 2. Function to run Streamlit app
def run_streamlit():
    os.system(f"streamlit run {APP_FILENAME}")

# 3. Start Streamlit in a new thread
thread = threading.Thread(target=run_streamlit)
thread.daemon = True
thread.start()

# 4. Wait for Streamlit to start
time.sleep(3)

# 5. Create ngrok tunnel
public_url = ngrok.connect(8501)
print(f"\n🚀 Your public URL is: {public_url.public_url}\n")

# Keep the script running
print("Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
    ngrok.kill()

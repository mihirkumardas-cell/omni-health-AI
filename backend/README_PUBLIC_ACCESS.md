# Public Access with ngrok

## Setup
1. Make sure your Flask app is in the backend folder:
   `C:\Users\ASUS\OneDrive\Desktop\omnihealthAI\backend`
2. Install dependencies if not already installed:
   `python -m pip install -r requirements.txt`
3. Install ngrok from https://ngrok.com/download and unzip it.
4. Add the ngrok executable to your PATH, or run it from the folder where it is extracted.

## Start the app and ngrok
1. In one terminal, run:
   `python app.py`
2. In another terminal, run:
   `ngrok http 5000`

## Share with your friend
- Use the public URL shown by ngrok, for example:
  `https://xxxxx.ngrok.io`
- Your friend can open that URL in a browser and log in.

## Login options
- Normal user: register a new account on the login page.
- Admin user: use `admin` / `admin123` (only share with trusted people).

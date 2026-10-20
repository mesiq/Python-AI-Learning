# Gemini agent demo

`agent_demo.py` is a command-line demo that uses Gemini to identify actions
requested in a prompt and runs the corresponding lookup:

- **Stock prices:** Looks up the latest available one-minute closing price
  through Yahoo Finance using a ticker symbol.
- **Song interpreters:** Searches MusicBrainz for recording artists.
- **YouTube videos:** Searches YouTube and prints up to five video links.

## Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create a `.env` file in the project folder with your Gemini API key:

   ```text
   GEMINI_API_KEY=your_gemini_api_key
   ```

   YouTube searches also require a YouTube Data API key. Enable the YouTube
   Data API v3 for the associated Google Cloud project, then add the key to
   `.env`:

   ```text
   YOUTUBE_API_KEY=your_youtube_api_key
   ```

   The YouTube key is only needed for YouTube requests. Stock and MusicBrainz
   lookups do not require separate API keys.

## Run

From the project folder, run:

```powershell
python agent_demo.py
```

Enter a request when prompted. The script handles that single request and
exits:

```text
What would you like to know? What is Apple's stock price?
The latest available price for AAPL is $...
```

Example requests:

- `What is Apple's stock price?`
- `Who performs the song Imagine?`
- `Find videos about the Apollo 11 moon landing.`
- `Find videos of live performances of Imagine and tell me who performs the song.`

For stock requests, include a recognizable company name or ticker symbol. The
reported price is the latest available one-minute close returned by Yahoo
Finance; it may not be a live quote. YouTube requests need a valid, enabled
YouTube API key.

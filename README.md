# Gemini agent demo

`agent_demo.py` is a command-line demo that uses Gemini to identify actions
requested in a prompt and runs the corresponding lookup:

- **Stock prices:** Looks up the latest available one-minute closing price
  through Yahoo Finance using a ticker symbol.
- **Song interpreters:** Searches MusicBrainz for recording artists.
- **YouTube videos:** Searches YouTube and prints up to five video links.
- **Weather:** Finds a place by name with Open-Meteo and reports current
  conditions or a daily forecast. You can optionally request an Open-Meteo
  model and set the forecast length.

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

   The YouTube key is only needed for YouTube requests. Stock, MusicBrainz, and
   Open-Meteo lookups do not require separate API keys.

## Run

From the project folder, run:

```powershell
python agent_demo.py
```

The assistant stays open for multiple requests. Enter `I'm done` to exit:

```text
Hi! I can help with stock prices, song interpreters, YouTube videos, and weather. Say ‘I'm done’ to exit.
How can I help? What's the current weather in Paris?
...
How can I help? I'm done
Thank you for using this assistant. Goodbye!
```

Example requests:

- `What is Apple's stock price?`
- `Who performs the song Imagine?`
- `Find videos about the Apollo 11 moon landing.`
- `Find videos of live performances of Imagine and tell me who performs the song.`
- `What's the current weather in Paris?`
- `Give me the forecast for Tokyo for the next 3 days using the ICON seamless model.`
- `What's the weather in Montreal using ECMWF IFS 0.25°?`
- `¿Qué tiempo hará en Madrid durante los próximos 5 días?`

For stock requests, include a recognizable company name or ticker symbol. The
reported price is the latest available one-minute close returned by Yahoo
Finance; it may not be a live quote. YouTube requests need a valid, enabled
YouTube API key. Weather locations are resolved to the first matching result
from Open-Meteo's geocoding service; locations in prompts written in another
language are translated to English for the search. Current conditions use
Open-Meteo's `best_match` model by default. Forecasts default to seven days;
you can request a different number from 1 to 16 days. Weather output includes
temperatures in °C, and the forecast also includes daily conditions and
precipitation probability when available.

The assistant can match model names or model identifiers. Available choices
include:

- **ECMWF:** `ECMWF IFS 0.25°` (`ecmwf_ifs025`), `ECMWF AIFS 0.25°`
  (`ecmwf_aifs025`)
- **GFS:** `GFS seamless` (`gfs_seamless`), `GFS HRRR` (`gfs_hrrr`),
  `GFS global` (`gfs_global`)
- **ICON:** `ICON seamless` (`icon_seamless`), `ICON global` (`icon_global`),
  `ICON EU` (`icon_eu`), `ICON-D2` (`icon_d2`)
- **Other providers:** GEM, JMA, Météo-France, KNMI, UKMO, and BOM ACCESS
  models are also available. Ask for the provider and model type or region,
  such as `Météo-France AROME France` or `UKMO UK deterministic 2 km`.

If no model is requested or recognized, Open-Meteo's `best_match` selection is
used.

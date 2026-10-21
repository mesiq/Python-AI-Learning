import json
import os
import dotenv
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from google import genai
from google.genai import types 

dotenv.load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

OPEN_METEO_MODELS = {
    "Best match": "best_match",
    "ECMWF IFS 0.25°": "ecmwf_ifs025",
    "ECMWF AIFS 0.25°": "ecmwf_aifs025",
    "GFS seamless": "gfs_seamless",
    "GFS HRRR": "gfs_hrrr",
    "GFS global": "gfs_global",
    "ICON seamless": "icon_seamless",
    "ICON global": "icon_global",
    "ICON EU": "icon_eu",
    "ICON-D2": "icon_d2",
    "GEM seamless": "gem_seamless",
    "GEM global": "gem_global",
    "GEM regional": "gem_regional",
    "JMA seamless": "jma_seamless",
    "JMA GSM": "jma_gsm",
    "JMA MSM": "jma_msm",
    "Météo-France seamless": "meteofrance_seamless",
    "Météo-France ARPEGE World": "meteofrance_arpege_world",
    "Météo-France ARPEGE Europe": "meteofrance_arpege_europe",
    "Météo-France AROME France": "meteofrance_arome_france",
    "Météo-France AROME France HD": "meteofrance_arome_france_hd",
    "KNMI seamless": "knmi_seamless",
    "KNMI Harmonie AROME Europe": "knmi_harmonie_arome_europe",
    "UKMO seamless": "ukmo_seamless",
    "UKMO global deterministic 10 km": "ukmo_global_deterministic_10km",
    "UKMO UK deterministic 2 km": "ukmo_uk_deterministic_2km",
    "BOM ACCESS global": "bom_access_global",
    "BOM ACCESS regional": "bom_access_regional",
}


def get_json(url, headers=None):
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def choose_action(text):
    prompt = (
        'From the user message, identify every applicable action. '
        'Choose actions from: "stock", "song", "youtube", and "weather". '
        'Return an empty actions list when none apply. '
        'Return only JSON with an actions key containing a list of objects with action and query keys. '
        'Use null for unused values. '
        'For stock, query is a stock ticker symbol. If you cannot identify a ticker from the company name, use null. '
        'For stock, include a company key with the company name from the request, or null if unknown. '
        'For song, query is a song title. '
        'For youtube, query is a concise search query for the video the user wants. '
        'For weather, query is the location name. When the prompt is in localised language, translate location into english. '
        'When the user names or describes a weather model, infer the intended '
        'Open-Meteo model using the mapping below and return its exact identifier. Resolve common names, abbreviations, '
        'and provider names to codes; do not require the user to provide the code. Use the most specifically matching '
        'listed model when the user gives a regional or resolution qualifier. Open-Meteo model mapping:'+ json.dumps(OPEN_METEO_MODELS, ensure_ascii=False) + '. '
        'Set model to null only if no model is specified or no listed model is a reasonable match; null uses the default model. '
        'Include forecast as true only when a forecast is requested, otherwise false. '
        'For weather, include forecast_days as the requested number of forecast days, or null if not specified. '
        'User message: ' + text
    )
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    result = json.loads(response.text)
    # Accept the earlier single-action response shape as well.
    if isinstance(result, dict) and "actions" not in result and "action" in result:
        return {"actions": [result]}
    return result


def find_stock_price(symbol):
    params = urlencode({"range": "1d", "interval": "1m"})
    data = get_json(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{params}",
        {"User-Agent": "Mozilla/5.0"},
    )
    results = data.get("chart", {}).get("result")
    if not results:
        return f"I couldn't find a stock price for {symbol}. Please check the company name or ticker symbol."

    quote = results[0]
    prices = quote.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    latest = next((price for price in reversed(prices) if price is not None), None)
    if latest is None:
        return f"No recent stock price is available for {symbol.upper()}."

    return f"The latest available price for {symbol.upper()} is ${latest:.2f}."


def find_song_interpreter(title):
    params = urlencode({"query": title, "fmt": "json", "limit": 5})
    data = get_json(
        "https://musicbrainz.org/ws/2/recording/?" + params,
        {"User-Agent": "SimpleGeminiDemo/1.0 "},
    )
    artists = []
    for recording in data.get("recordings", []):
        credits = recording.get("artist-credit", [])
        artist = "".join(
            credit.get("name", "") + credit.get("joinphrase", "")
            for credit in credits if isinstance(credit, dict)
        ).strip()
        if artist and artist not in artists:
            artists.append(artist)
    if not artists:
        return f"I couldn't find an interpreter for '{title}'."
    names = ", ".join(artists)
    return f"The interpreter{'s' if len(artists) != 1 else ''} of '{title}' {'are' if len(artists) != 1 else 'is'} {names}."


def find_youtube_videos(query):
    params = urlencode({
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 5,
        "key": os.environ["YOUTUBE_API_KEY"],
    })
    data = get_json("https://www.googleapis.com/youtube/v3/search?" + params)
    items = data.get("items", [])
    if not items:
        return "No YouTube videos found."
    return "\n".join(
        f"{item['snippet']['title']} — https://www.youtube.com/watch?v={item['id']['videoId']}"
        for item in items
        if item.get("id", {}).get("videoId")
    ) or "No YouTube videos found."


def find_weather(location, model=None, forecast=False, forecast_days=7):
    location_data = get_json(
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urlencode({"name": location, "count": 1, "language": "en", "format": "json"})
    )
    locations = location_data.get("results", [])
    if not locations:
        return f"I couldn't find a location named '{location}'."

    place = locations[0]
    params = {
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "timezone": "auto",
    }
    requested_model = model.strip().casefold() if isinstance(model, str) else ""
    selected_model = next(
        (
            code for code in OPEN_METEO_MODELS.values()
            if code.casefold() == requested_model
        ),
        next(
            (
                code for name, code in OPEN_METEO_MODELS.items()
                if name.casefold() == requested_model
            ),
            "best_match",
        ),
    )
    if selected_model != "best_match":
        params["models"] = selected_model
    if forecast:
        params["daily"] = (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max"
        )
        try:
            forecast_days = int(forecast_days)
        except (TypeError, ValueError):
            forecast_days = 7
        params["forecast_days"] = max(1, min(forecast_days, 16))
    else:
        params["current"] = (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,weather_code,wind_speed_10m"
        )

    weather_data = get_json(
        "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
    )
    actual_model = weather_data.get("model") or weather_data.get("models")
    if isinstance(actual_model, (list, tuple)):
        actual_model = ", ".join(str(item) for item in actual_model)
    if not actual_model:
        actual_model = (
            f"{selected_model} (default selection)"
            if selected_model == "best_match" else selected_model
        )
    place_name = ", ".join(
        part for part in (place.get("name"), place.get("admin1"), place.get("country"))
        if part
    )
    weather_codes = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        56: "light freezing drizzle",
        57: "dense freezing drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        66: "light freezing rain",
        67: "heavy freezing rain",
        71: "slight snow fall",
        73: "moderate snow fall",
        75: "heavy snow fall",
        77: "snow grains",
        80: "slight rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",
        85: "slight snow showers",
        86: "heavy snow showers",
        95: "thunderstorm",
        96: "thunderstorm with slight hail",
        99: "thunderstorm with heavy hail",
    }

    def describe(code):
        return weather_codes.get(code, "unknown conditions")

    if forecast:
        daily = weather_data["daily"]
        lines = [
            f"{len(daily['time'])}-day forecast for {place_name}:",
            f"Open-Meteo model used: {actual_model}",
        ]
        for index, date in enumerate(daily["time"]):
            description = describe(daily["weather_code"][index])
            low = daily["temperature_2m_min"][index]
            high = daily["temperature_2m_max"][index]
            rain_chance = daily["precipitation_probability_max"][index]
            rain_text = (
                f", precipitation chance {rain_chance}%"
                if rain_chance is not None else ""
            )
            lines.append(
                f"{date}: {description}, {low} to {high} °C{rain_text}"
            )
        return "\n".join(lines)

    current = weather_data["current"]
    return (
        f"Current weather for {place_name} at {current['time']} "
        f"(Open-Meteo model used: {actual_model}): "
        f"{describe(current['weather_code'])}, {current['temperature_2m']} °C "
        f"(feels like {current['apparent_temperature']} °C), "
        f"humidity {current['relative_humidity_2m']}%, "
        f"wind {current['wind_speed_10m']} km/h, "
        f"precipitation {current['precipitation']} mm."
    )


def main():
    print("Hi! I can help with stock prices, song interpreters, YouTube videos, and weather. Say ‘I'm done’ to exit.")
    while True:
        text = input("How can I help? ").strip()
        if text.casefold() == "i'm done":
            print("Thank you for using this assistant. Goodbye!")
            break

        result = choose_action(text)
        actions = result.get("actions", []) if isinstance(result, dict) else []
        answers = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            kind = action.get("action")
            query = action.get("query")
            if kind == "stock":
                if isinstance(query, str) and query.strip():
                    answers.append(find_stock_price(query.strip()))
                else:
                    company = action.get("company")
                    if isinstance(company, str) and company.strip():
                        answers.append(f"No stock price found for {company.strip()}. Check the company name or ticker symbol.")
                    else:
                        answers.append("No stock price found. Check the company name or ticker symbol.")
            elif kind == "song" and isinstance(query, str) and query.strip():
                answers.append(find_song_interpreter(query.strip()))
            elif kind == "youtube" and isinstance(query, str) and query.strip():
                answers.append(find_youtube_videos(query.strip()))
            elif kind == "weather" and isinstance(query, str) and query.strip():
                model = action.get("model")
                forecast = action.get("forecast") is True
                forecast_days = action.get("forecast_days", 7)
                answers.append(find_weather(query.strip(), model, forecast, forecast_days))

        if answers:
            print("\n".join(answers))
        else:
            print("I couldn't identify a supported request. Try asking about stocks, songs, YouTube, or weather.")


if __name__ == "__main__":
    main()
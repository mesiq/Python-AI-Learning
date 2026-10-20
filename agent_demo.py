import json
import os
import dotenv
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from google import genai
from google.genai import types 

dotenv.load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def get_json(url, headers=None):
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def choose_action(text):
    prompt = (
        'From the user request, identify every applicable action. '
        'Choose actions from: "stock", "song", and "youtube". '
        'Return an empty actions list when none apply. '
        'Return only JSON with an actions key containing a list of objects with action and query keys. '
        'Use null for unused values. '
        'For stock, query is a stock ticker symbol. If you cannot identify a ticker from the company name, use null. '
        'For stock, include a company key with the company name from the request, or null if unknown. '
        'For song, query is a song title.'
        'For youtube, query is a concise search query for the video the user wants.'
        'User request: ' + text
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


def main():
    text = input("What would you like to know? ")
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

    if answers:
        print("\n".join(answers))
    else:
        print("I am a simple agent; I can help with stock prices, songs, or YouTube video requests.")


if __name__ == "__main__":
    main()
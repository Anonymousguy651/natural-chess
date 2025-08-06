import requests
import chess.pgn
import pandas as pd
import io
import time
import csv  # We'll reference csv.QUOTE_ALL, etc.

def fetch_user_studies(username, token):
    """Fetches PGN data for all studies of a specific Lichess user."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://lichess.org/study/by/{username}/export.pgn"
    
    params = {
        "comments": "true",      # Include analysis and annotator comments
        "clocks": "false",       # Exclude clock comments
        "variations": "false",   # Exclude variations
        "source": "false",       # Exclude source tags
        "orientation": "false"
    }

    retries = 0
    while retries < 5:  # Retry up to 5 times
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:  # Rate limiting
            print(f"Rate limit exceeded for {username}. Waiting for 60 seconds...")
            time.sleep(60)
            retries += 1
        elif response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch studies for {username}: Status {response.status_code}")
            return None
    print(f"Max retries exceeded for {username}.")
    return None

def parse_studies(pgn_text):
    """Parses all studies from a PGN text and extracts FENs, moves, and comments."""
    games = []
    pgn = io.StringIO(pgn_text)
    
    while True:
        try:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break

            # Extract study metadata if available
            study_id = game.headers.get("Site", "").split("/")[-1]
            
            try:
                board = game.board()
            except ValueError as e:
                print(f"Skipping game due to invalid FEN: {e}")
                continue

            for node in game.mainline():
                fen = board.fen()
                if node.move is None:
                    # Very rare edge case if node.move is None at root
                    continue

                move = node.move.uci()
                commentary = node.comment
                
                # If there's commentary, store it
                if commentary:
                    games.append({
                        "Study_ID": study_id,
                        "FEN": fen,
                        "Move": move,
                        "Commentary": commentary
                    })
                
                board.push(node.move)
        except Exception as e:
            print(f"Error parsing game: {e}")
            continue
    
    return games

def load_usernames(file_path):
    """Loads usernames from a text file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]

def main():
    usernames_file = "study_authors.txt"
    token = "lip_aZxy0K5vsZlXT6Nyscxc"  # Replace with your actual API token
    
    usernames = load_usernames(usernames_file)
    if not usernames:
        print("No usernames found in study_authors.txt")
        return

    all_games = []

    for username in usernames:
        print(f"Fetching studies for user {username}...")
        pgn_data = fetch_user_studies(username, token)
        if pgn_data:
            print(f"Parsing studies for {username}...")
            games = parse_studies(pgn_data)
            for game in games:
                game['Username'] = username
            all_games.extend(games)
            print(f"Found {len(games)} commented positions for {username}")

    if all_games:
        df = pd.DataFrame(all_games)
        
        # Key update: ensure multiline or comma-containing fields are fully quoted
        # and properly escaped. This prevents malformed CSV if commentary includes line breaks.
        df.to_csv(
            "lichess_studies.csv", 
            index=False,
            quoting=csv.QUOTE_ALL,        # Always quote all fields
            escapechar='\\',              # Escape internal quotes if needed
            lineterminator='\n',         # Ensure standard newline
            encoding='utf-8'              # In case of non-ASCII text
        )
        
        print(f"Saved {len(df)} positions to lichess_studies.csv")
    else:
        print("No commented positions found")

if __name__ == "__main__":
    main()
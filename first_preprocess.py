import pandas as pd
import chess
import re
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import concurrent.futures
import numpy as np
import csv  # We import csv so we can use csv.QUOTE_ALL

def is_probably_english(text):
    """Quick preliminary check if text is likely English based on common words."""
    english_markers = {
        'the', 'and', 'is', 'in', 'to', 'it', 'that', 'was', 'for',
        'with', 'now', 'here', 'this', 'but', 'piece', 'move', 'best',
        'king', 'queen', 'pawn', 'knight', 'bishop', 'rook', 'check',
        'mate', 'position', 'attack', 'defend', 'castle', 'pin',
        'fork', 'tactic', 'strategy', 'advantage', 'better', 'worse',
        'blunder', 'mistake', 'inaccuracy'
    }
    
    text = text.lower()
    words = set(re.findall(r'\b\w+\b', text))
    matches = words.intersection(english_markers)
    return len(matches) >= 2

def batch_process_language(texts, batch_size=1000):
    """Process language detection in batches with preliminary filtering."""
    results = []
    # Quick filtering
    likely_english_mask = [is_probably_english(text) for text in texts]
    texts_to_check = [text for text, is_likely in zip(texts, likely_english_mask) if is_likely]
    
    print(f"Preliminary filtering: {len(texts_to_check)} out of {len(texts)} need detailed check")
    
    def detect_lang_safe(t):
        try:
            return detect(t) == 'en'
        except LangDetectException:
            return False

    final_results = np.zeros(len(texts), dtype=bool)

    # Mark the ones that fail the quick filter as non-English right away
    for i, is_likely in enumerate(likely_english_mask):
        if not is_likely:
            final_results[i] = False

    texts_to_check_indices = [i for i, is_likely in enumerate(likely_english_mask) if is_likely]

    for i in range(0, len(texts_to_check), batch_size):
        batch = texts_to_check[i:i + batch_size]
        print(f"Processing batch {i // batch_size + 1}/{(len(texts_to_check) - 1) // batch_size + 1}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            batch_results = list(executor.map(detect_lang_safe, batch))
            
        # Update overall results
        for idx, is_english in zip(texts_to_check_indices[i:i + batch_size], batch_results):
            final_results[idx] = is_english
    
    return final_results

def validate_fen(fen):
    """Check if a FEN string is valid."""
    try:
        chess.Board(fen)
        return True
    except ValueError:
        return False

def convert_to_san(fen, move_uci):
    """Convert UCI move to SAN notation given a FEN position."""
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_uci)
        return board.san(move)
    except (ValueError, AttributeError):
        return None

def is_auto_generated(commentary, result_phrases):
    """Check if commentary matches auto-generated game result phrases."""
    stripped = re.sub(r'[.,!?]', '', commentary.strip()).lower()
    stripped_phrases = [re.sub(r'[.,!?]', '', phrase.lower()) for phrase in result_phrases]
    return stripped in stripped_phrases

def is_low_value_eval_comment(commentary):
    """Check if commentary is just a low-value evaluation or arrow comment."""
    if not commentary:
        return True
    
    patterns = [
        # e.g. "[%eval X] Inaccuracy. Y was best."
        r'^\[%eval\s+[+-]?\d+\.?\d*\]\s*(Inaccuracy|Blunder|Mistake)\.\s+\w+\d?\s+was\s+best\.*\s*$',
        # e.g. "Inaccuracy. X was best. [%eval Y]"
        r'^(Inaccuracy|Blunder|Mistake)\.\s+\w+\d?\s+was\s+best\.\s*\[%eval\s+[+-]?\d+\.?\d*\]\s*$',
        # e.g. just "[%eval X]"
        r'^\[%eval\s+[+-]?\d+\.?\d*\]\s*$',
        # e.g. arrow-only "→ e5"
        r'^→\s*\w+\s*$',
        # short arrow variations
        r'^[^→]{0,10}→[^→]{0,10}$'
    ]
    
    return any(bool(re.match(p, commentary.strip())) for p in patterns)

def clean_eval_comments(commentary, min_length=63, arrow_min=80):
    """Removes low-value eval commentary or short arrow text."""
    if commentary is None:
        return None
    
    if is_low_value_eval_comment(commentary):
        return None
    
    # Remove eval tags just for length checking
    cleaned_text = re.sub(r'\[%eval\s+[+-]?\d+\.?\d*\]', '', commentary).strip()
    
    # If it has an arrow, require arrow_min length
    if '→' in cleaned_text and len(cleaned_text) <= arrow_min:
        return None
    
    # Check for certain "valuable" terms
    valuable_terms = ['blunder', 'inaccuracy', 'mistake', 'tactical', 'positional', 'advantage']
    lower_commentary = cleaned_text.lower()
    has_valuable = any(term in lower_commentary for term in valuable_terms)
    
    # If it has a valuable term but is too short, discard
    if has_valuable:
        if len(cleaned_text) <= min_length:
            return None
        return commentary
    
    # If it lacks a "valuable" term, enforce min_length
    if len(cleaned_text) <= min_length:
        return None
    
    return commentary

def preprocess_data(input_file, output_file):
    """Preprocess the dataset and save the cleaned data to CSV, fully quoted."""
    df = pd.read_csv(input_file)
    print(f"Initial row count: {len(df)}")

    # Remove rows with missing commentary
    df = df[df['Commentary'].notna()]
    print(f"After removing null commentary: {len(df)} rows")

    # Language filtering
    print("Performing language filtering...")
    english_mask = batch_process_language(df['Commentary'].values)
    df = df[english_mask]
    print(f"After language filtering: {len(df)} rows")

    # Quick removal of lines containing "DVD"
    df = df[~df['Commentary'].str.contains("DVD", na=False)]
    print(f"After DVD filter: {len(df)} rows")

    # Validate FEN & convert moves to SAN
    print("Converting moves to SAN notation...")
    valid_indices = []
    san_moves = []

    for idx, row in df.iterrows():
        if validate_fen(row['FEN']) and pd.notna(row['Move']):
            san_move = convert_to_san(row['FEN'], row['Move'])
            if san_move is not None:
                valid_indices.append(idx)
                san_moves.append(san_move)
    
    df = df.loc[valid_indices].copy()
    df['SAN_Move'] = san_moves
    print(f"After FEN validation & move conversion: {len(df)} rows")

    # Filter out auto-generated game results
    result_phrases = [
        "1-0 Black resigns", "0-1 White resigns",
        "0-1 Black wins by checkmate", "1-0 White wins by checkmate",
        "1-0 White wins", "0-1 Black wins",
        "1/2-1/2 The game is a draw", "Game drawn by repetition",
        "Game drawn by agreement", "{username} won by resignation",
        "{username} won on time", "{username} won by checkmate",
        "White wins", "Black wins", "Game drawn",
        "Draw by repetition", "Draw by agreement",
        "1-0", "0-1", "1/2-1/2"
    ]
    auto_gen_mask = df['Commentary'].apply(lambda x: is_auto_generated(x, result_phrases))
    df = df[~auto_gen_mask]
    print(f"After removing auto-generated: {len(df)} rows")

    # Clean up low-value [%eval] comments
    df['Commentary'] = df['Commentary'].apply(clean_eval_comments)
    df = df[df['Commentary'].notna()]
    print(f"After cleaning eval comments: {len(df)} rows")

    # Trim whitespace
    df['Commentary'] = df['Commentary'].str.strip()

    # Create Input/Output columns for training
    df['Input'] = df.apply(lambda row: f"{row['FEN']} {row['SAN_Move']}", axis=1)
    df['Output'] = df['Commentary']

    # Drop unneeded columns
    df = df[['Input', 'Output', 'SAN_Move']]

    # **Key fix**: write preprocessed CSV with full quoting so commentary remains intact
    df.to_csv(
        output_file,
        index=False,
        quoting=csv.QUOTE_ALL,
        escapechar='\\',
        lineterminator='\n'
    )
    print(f"\nPreprocessed data saved to {output_file}")
    print(f"Final row count: {len(df)}")

    # Display sample rows
    print("\nSample of final processed data:")
    sample_df = df.head(3)
    for _, row in sample_df.iterrows():
        print(f"\nInput: {row['Input'][:50]}...")
        print(f"Move (SAN): {row['SAN_Move']}")
        print(f"Output: {row['Output'][:100]}...")

if __name__ == "__main__":
    INPUT_FILE = "lichess_studies.csv"
    OUTPUT_FILE = "preprocessed_lichess_data.csv"
    preprocess_data(INPUT_FILE, OUTPUT_FILE)
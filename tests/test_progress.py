#!/usr/bin/env python3
"""
Test para verificar el sistema de barras de progreso
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_multiuser import YouTubeBot


def test_progress_bar():
    """Test básico de las barras de progreso"""
    bot = YouTubeBot("fake_token")
    
    print("Probando barras de progreso:")
    print("=" * 50)
    
    # Probar diferentes porcentajes
    for percent in [0, 10, 25, 50, 75, 90, 100]:
        bar = bot.create_progress_bar(percent)
        print(f"{percent:3d}% {bar}")
    
    print("\nProbando función format_time:")
    print("=" * 30)
    
    # Probar diferentes tiempos
    for seconds in [30, 90, 150, 3600, 3665]:
        formatted = bot.format_time(seconds)
        print(f"{seconds:4d}s -> {formatted}")
    
    print("\nProbando escape_markdown:")
    print("=" * 30)
    
    # Probar diferentes textos problemáticos
    test_texts = [
        "Mojinos Escozíos - La Camella",
        "Artist with (parentheses) & symbols!",
        "Song with [brackets] and _underscores_",
        "Title with *asterisks* and #hashtags"
    ]
    
    for text in test_texts:
        escaped = bot.escape_markdown(text)
        print(f"Original: {text}")
        print(f"Escaped:  {escaped}")
        print()


if __name__ == "__main__":
    test_progress_bar()

import google.generativeai as genai
import pandas as pd

# 1. Setup the AI
genai.configure(api_key="AIzaSyAK5y-KqlJq7RSwoT5gY3rJyGIwK27izyg")
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_coaching(lap_df):
    # Summary statistics for the lap (Mechanical Engineering metrics)
    max_speed = lap_df['speed'].max()
    avg_throttle = lap_df['throttle'].mean()
    full_brake_count = len(lap_df[lap_df['brake'] > 90])
    
    # Create the Prompt
    prompt = f"""
    You are a professional F1 Race Engineer. Analyze this lap telemetry:
    - Max Speed: {max_speed} km/h
    - Average Throttle Application: {avg_throttle:.1f}%
    - Heavy Braking Events (>90%): {full_brake_count}
    
    Based on these stats, give me 3 specific tips to improve my lap time. 
    Keep it technical and concise, focusing on weight transfer and traction.
    """
    
    response = model.generate_content(prompt)
    return response.text
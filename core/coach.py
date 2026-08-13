# core/coach.py
import os
import google.generativeai as genai

class AIRaceEngineer:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_lap(self, df):
        max_speed = df['speed'].max()
        avg_throttle = df['throttle'].mean()
        heavy_brakes = len(df[df['brake'] > 90])
        avg_ers = df['ers_energy'].mean()

        prompt = f"""
        You are a senior F1 Race Engineer analyzing telemetry:
        - Max Speed: {max_speed} km/h
        - Avg Throttle: {avg_throttle:.1f}%
        - Heavy Braking Events (>90%): {heavy_brakes}
        - Avg ERS Store Level: {avg_ers:.1f} J

        Provide 3 concise, high-impact driving tips focusing on braking points, ERS usage, and traction exit.
        """
        response = self.model.generate_content(prompt)
        return response.text
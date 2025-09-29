FloodRiskPrediction-CDMX

This project is an AI-powered agent that predicts the probability of flooding in Mexico City (CDMX) based on geographic, hydrological, and historical data.

🌎 Interactive Map (React + Leaflet): Users can click anywhere in Mexico City to obtain latitude/longitude, place a marker, and query the flood risk.

🤖 Prediction API (FastAPI + Python): Coordinates are sent to a Python backend that analyzes multiple datasets (topography, water bodies, rainfall forecasts, historical reports) to estimate the flood probability.

📊 Risk Assessment: Returns both raw geospatial indicators and a compact summary including risk level (Low, Moderate, High).

📝 Explainable AI: Generates a natural-language report of the area’s vulnerability and weather forecast using an LLM (via OpenRouter).

⚡ Tech Stack: Python (FastAPI, GeoPandas, Pandas), React + Vite + Tailwind, Leaflet for maps, REST API integration.

This project demonstrates how AI, data science, and geospatial visualization can be combined to support urban risk management and provide accessible insights to citizens and decision-makers.

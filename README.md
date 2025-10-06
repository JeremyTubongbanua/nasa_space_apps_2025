# SkyDashboard

SkyDashboard aggregates open air-quality, satellite, and weather feeds into a single dashboard that powers proactive alerts. The FastAPI backend unifies TEMPO, OpenAQ, and Open-Meteo data, while the React frontend visualizes local conditions and the alert service pushes SMS notifications through Twilio.

## Live Demo

[http://159.203.5.107](http://159.203.5.107)

## Architecture Overview

![SkyDashboard architecture diagram showing data sources feeding the API, web app, and Twilio notifications](frontend/src/assets/soft_arch.png)

## Product Gallery

![SkyDashboard home screen mock](docs/assets/home.png)
![Home screen implementation preview](docs/assets/home_actual.png)
![Air quality detail mock](docs/assets/aqi_actual.png)
![Interactive map mock](docs/assets/map.png)
![Interactive map implementation preview](docs/assets/map_actual.png)
![Forecast panels mock](docs/assets/forecasts.png)
![Quiz feature mock](docs/assets/quiz.png)
![Quiz results screen implementation preview](docs/assets/quiz_results.png)
![Insights dashboard implementation preview](docs/assets/insights.png)
![Guidebook highlights mock](docs/assets/guidebook.png)
![Design prototyping board](docs/assets/prototyping.png)
![Team about page implementation preview](docs/assets/about_actual.png)

All images are sourced from the `docs/assets` directory to keep the README self-contained.

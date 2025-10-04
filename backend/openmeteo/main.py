from flask import Flask, request, jsonify
from flask_cors import CORS
from fetch import get_weather_data

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

@app.route("/api/weather", methods=['GET'])
def weather_endpoint():
    args = request.args

    latitude = args.get('latitude')
    longitude = args.get('longitude')

    if not latitude or not longitude:
        return jsonify({"error": "Missing latitude or longitude parameter"}), 400

    try:
        lat_float = float(latitude)
        lon_float = float(longitude)
    except ValueError:
        return jsonify({"error": "Invalid latitude or longitude format"}), 400

    # Extract all other query parameters to pass to the fetch function
    # This makes the endpoint flexible.
    api_params = {key: value for key, value in args.items() if key not in ['latitude', 'longitude']}

    try:
        forecast_data = get_weather_data(lat_float, lon_float, **api_params)
        return jsonify(forecast_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
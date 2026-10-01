import string
import random
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# Simple in-memory database (dictionary) to store URLs
# Format: { "short_code": "https://example.com" }
url_database = {}

def generate_short_code(length=6):
    """Generates a random 6-character string for the short link, avoiding collisions."""
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if code not in url_database:
            return code

# HTML template for the frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple URL Shortener</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 50px; background: #f4f4f9; color: #333; }
        .container { max-width: 500px; background: white; padding: 30px; border-radius: 8px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 80%; padding: 10px; margin-right: 10px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 15px; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { margin-top: 20px; }
        .error { color: #b00020; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>URL Shortener</h2>
        <form method="POST">
            <input type="text" name="url" placeholder="Enter long URL here..." required>
            <button type="submit">Shorten</button>
        </form>
        {% if short_url %}
        <div class="result">
            <p>Your Shortened Link:</p>
            <a href="{{ short_url }}" target="_blank">{{ short_url }}</a>
        </div>
        {% endif %}
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    short_url = None
    error = None

    if request.method == 'POST':
        long_url = request.form.get('url', '').strip()

        if not long_url:
            error = "Please enter a URL."
        else:
            # Fix: correctly check for existing http:// or https:// scheme
            # (the original had a typo: 'https://.' instead of 'https://')
            if not long_url.startswith(('http://', 'https://')):
                long_url = 'http://' + long_url

            short_code = generate_short_code()
            url_database[short_code] = long_url

            # Generate the full short URL based on the current host.
            # In environments like GitHub Codespaces, the app is accessed
            # through a forwarding proxy, which sets X-Forwarded-Host /
            # X-Forwarded-Proto headers with the real public address.
            # request.host_url alone would incorrectly return 127.0.0.1,
            # so we prefer the forwarded headers when present.
            forwarded_host = request.headers.get('X-Forwarded-Host')
            forwarded_proto = request.headers.get('X-Forwarded-Proto', 'https')

            if forwarded_host:
                base_url = f"{forwarded_proto}://{forwarded_host}/"
            else:
                base_url = request.host_url

            short_url = base_url + short_code

    return render_template_string(HTML_TEMPLATE, short_url=short_url, error=error)

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """When someone clicks the short link, redirect them to the original URL."""
    long_url = url_database.get(short_code)
    if long_url:
        return redirect(long_url)
    return "Link not found!", 404

if __name__ == '__main__':
    # NOTE: debug=True should be turned off in production, as it exposes
    # a debugger that can allow arbitrary code execution if the server
    # is reachable from outside your machine.
    # host='0.0.0.0' makes the server reachable via Codespaces/container
    # port forwarding (binding to 127.0.0.1 only accepts connections from
    # inside the container itself).
    app.run(host='0.0.0.0', port=5000, debug=True)
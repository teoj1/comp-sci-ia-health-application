from flask import Flask, render_template

app = Flask(__name__)
@app.route('/')

def main():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)


# To run this server, use the command:
# python -m flask --app server run
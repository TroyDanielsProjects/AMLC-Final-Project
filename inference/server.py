from flask import Flask, render_template, request
from inference import Inference

app = Flask(__name__)

inference = Inference()

@app.route('/', methods=['GET', 'POST'])
def get_anaylst():
    response = "No opinion"
    if request.method == 'POST':
        text = request.form.get("message")
        if text:
            response = inference.inference(text)
        else:
            response = "Sorry I didn't get that"
    return render_template('inference.html', response=response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
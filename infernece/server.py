from flask import Flask, render_template, request
from inference import Inference
from huggingface_hub import login
from dotenv import load_dotenv
import os

os.environ["BNB_CUDA_VERSION"] = "123"

app = Flask(__name__)

inference = Inference()
original_inference = Inference(original=True)

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

@app.route('/original', methods=['GET', 'POST'])
def get_anaylst_original():
    response = "No opinion"
    if request.method == 'POST':
        text = request.form.get("message")
        if text:
            response = original_inference.inference(text)
        else:
            response = "Sorry I didn't get that"
    return render_template('inference.html', response=response)

if __name__ == '__main__':
    load_dotenv()
    access_token = os.getenv("HF_TOKEN")
    login(token=access_token)
    app.run(host='0.0.0.0', port=8081)
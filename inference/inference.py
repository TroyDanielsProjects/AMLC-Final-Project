import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import sys
from peft import PeftModel, PeftConfig
from huggingface_hub import login
from dotenv import load_dotenv
import os
  

class Inference:
    """
    Handles model training for the NHL Buzz news generation task.
    """
    def __init__(self):
        """
        Initialize with model
        """
        self.device = self.determine_device()
        self.model = self.load_model().to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
        self.model.eval()
        


    def determine_device(self):
        """
        Determine the best available device for training.
        
        Returns:
            str: 'cuda', 'mps', or 'cpu' device identifier
        """
        device = "cpu"
        try:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_built() or torch.mps.is_available(): 
                device = "mps"
            else:
                device = "cpu" 
        except Exception as e:
            print(f"Exception thrown: {e}")
            device = "cpu"
        finally:
            print(f"using {device}")
            return device
    
    def load_model(self):
        model = None
        try:
            base_model = AutoModelForCausalLM.from_pretrained("google/gemma-2b")
            model = PeftModel.from_pretrained(base_model, "/mnt/gemma-scraping/models/finetuned_model/checkpoint-990")
            print("Saved model successfully loaded")
            return model
        except Exception as e:
            print(f"Failed to load model: {e}")
            sys.exit()


            
    def inference(self, prompt):
        tokenized_prompt = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(**tokenized_prompt, max_length=800)
        response = self.tokenizer.decode(outputs[0])
        print(len(response))
        print(response)
        return response

    def test_inference(self):
        response = self.inference("What are the daily updates for the Dallas Stars on April-16-2025?")
        print(response)

    def test_flast(self, prompt):
        return prompt.upper()


if __name__ == "__main__":
    load_dotenv()
    access_token = os.getenv("HF_TOKEN")
    print("WE HAVE THE ACCESS TOKEN??? {access_token}")

    login(token=access_token)
    inference = Inference()
    inference.test_inference()
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from cleanAndLoadData import DataCleaner
from webScraper import Webscraper

class BuzzDataset(Dataset):
    """
    Custom dataset for NHL Buzz news data.
    Formats data into prompt-response pairs for fine-tuning.
    """
    def __init__(self, data, tokenizer):
        """
        Initialize dataset with hockey news data and tokenizer.
        
        Args:
            data: List of BuzzDataPoint objects
            tokenizer: HuggingFace tokenizer
        """
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = None

    def __len__(self):
        """Return the total number of samples in the dataset."""
        return len(self.data)
    
    def set_max_length(self, max_length):
        """
        Set maximum sequence length for padding.
        
        Args:
            max_length: Maximum token length for sequences
        """
        self.max_length = max_length
    
    def __getitem__(self, index):
        """
        Get a tokenized training sample at the specified index.
        
        Creates a prompt-response pair from hockey news data and converts
        to model inputs with appropriate labels for teacher forcing.
        
        Args:
            index: Sample index
            
        Returns:
            Dict containing input_ids, attention_mask, and labels
        """
        # Extract data fields from the data point
        data_point = self.data[index]
        year = data_point.year
        month = data_point.month
        day = data_point.day
        team = data_point.team
        text = data_point.text
        
        # Create a prompt asking for daily updates
        prompt = f"What are the daily updates for the {team} on {month}-{day}-{year}?"

        # Tokenize the prompt separately
        prompt_encoding = self.tokenizer(prompt, return_tensors="pt")
        prompt_ids = prompt_encoding['input_ids'].squeeze(0)
        prompt_attention_mask = prompt_encoding['attention_mask'].squeeze(0)

        # Tokenize the response with optional padding/truncation
        if self.max_length:
            response_encoding = self.tokenizer(
                text, 
                return_tensors="pt", 
                max_length=(self.max_length - prompt_ids.shape[0]), 
                padding='max_length', 
                padding_side='right'
            )
        else:
            response_encoding = self.tokenizer(text, return_tensors="pt")
            
        input_ids = response_encoding['input_ids'].squeeze(0)
        attention_mask = response_encoding['attention_mask'].squeeze(0)

        # Concatenate prompt and response tokens
        encoding = torch.concat((prompt_ids, input_ids), 0)
        attention_mask = torch.concat((prompt_attention_mask, attention_mask), 0)
        
        # Create labels: mask prompt tokens with -100 (ignored in loss calculation)
        labels = encoding.clone()
        labels[:prompt_ids.shape[0]] = -100

        # Truncate if exceeding maximum context length
        if encoding.shape[0] > 8192:
            encoding = encoding[:8192]
            attention_mask = attention_mask[:8192]
            labels = labels[:8192]  # Also truncate labels

        return {
            'input_ids': encoding,
            'attention_mask': attention_mask,
            'labels': labels,  # Teacher forcing: labels are the same as input_ids
        }
    
class Trainer:
    """
    Handles model training for the NHL Buzz news generation task.
    """
    def __init__(self, get_data=True):
        """
        Initialize trainer with model, tokenizer, and optimizer.
        """
        self.device = self.determine_device()
        self.webscrapper = Webscraper()
        self.dataCleaner = DataCleaner()
        if get_data:
            # self.webscrapper.run()
            self.dataCleaner.run()
        self.tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
        # quantization implementation
        self.quantization_config = BitsAndBytesConfig(load_in_4bit=True)
        self.model = self.load_model()
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=5e-5)
        self.dataset = None
        self.dataloader = None
        # Space for LoRA implementation
        self.lora_config = None

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
            elif torch.mps.is_available(): 
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
            model = AutoModelForCausalLM.from_pretrained("./models/finetuned_model").to(self.device)
            print("Saved model successfully loaded")
        except Exception as e:
            print(f"Failed to load model: {e}")
        if model is None:
            model = AutoModelForCausalLM.from_pretrained("google/gemma-2b", quantization_config=self.quantization_config).to(self.device)
            print("Loading new model")
            model.to("cpu")
            model.save_pretrained("./models/finetuned_model")
            model.tokenizer.save_pretrained("./models/finetuned_model")
        return model
    
    @staticmethod    
    def largest_tokenization(dataset):
        """
        Find the largest tokenized sequence length in the dataset.
        
        Args:
            dataset: Dataset to analyze
            
        Returns:
            int: Maximum token length found
        """
        largest = 0
        for i in range(len(dataset)):
            size = dataset[i]['input_ids'].shape[0]
            if size > largest:
                largest = size
        print(f"The largest encoded tensor is {largest}")
        return largest

    def load_in_buzz_data(self, batch=4):
        """
        Load and prepare NHL Buzz data for training.
        
        Args:
            batch: Batch size for training
        """
        self.dataset = BuzzDataset(DataCleaner.load_buzz_data(), self.tokenizer)
        self.dataset.set_max_length(self.largest_tokenization(self.dataset)) 
        self.dataloader = DataLoader(self.dataset, batch_size=batch, shuffle=True) 
        
    def setup_lora(self):
        """
        Set up Low-Rank Adaptation (LoRA) for parameter-efficient fine-tuning.
        """
        # TODO: Implement LoRA setup
        pass

    def train_buzz(self, epochs=3):
        """
        Train the model.
        
        Args:
            epochs: Number of training epochs
        """
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for i, batch in enumerate(self.dataloader):
                # Move batch to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                # Zero gradients
                self.optimizer.zero_grad()

                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels 
                )

                loss = outputs.loss
                loss.backward()  # Backward pass
                self.optimizer.step()  # Update weights

                total_loss += loss.item()
                print(f"Finished batch: {i} - batch loss: {loss.item() / len(batch)} - Progress: { (i+1) / len(self.dataloader) * 100:.2f}%") 

            # Report epoch results
            avg_loss = total_loss / len(self.dataloader)
            print(f"Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}")
            
        # Save the fine-tuned model and tokenizer
        self.model.to("cpu")
        self.model.save_pretrained("./models/finetuned_model")
        self.tokenizer.save_pretrained("./models/finetuned_model")

    def infernece(self, prompt):
        tokenized_prompt = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**tokenized_prompt, max_length=800)
        response = self.tokenizer.decode(outputs[0])
        return response

    def test_inference(self):
        response = self.infernece("What are the daily updates for the Colorado Avalanche on January-1-2025?")
        print(response)


if __name__ == "__main__":
    trainer = Trainer()
    trainer.load_in_buzz_data()
    trainer.train_buzz()
    trainer.test_inference()
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from cleanAndLoadData import DataCleaner
from buzz_data.webScraper import Webscraper
from dotenv import load_dotenv
import os
from huggingface_hub import login
from tqdm import tqdm
from accelerate import Accelerator
import os
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from google.cloud import storage
import glob

os.environ["BNB_CUDA_VERSION"] = "123"

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
                truncation=True,
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

class PodCastDataset(Dataset):
    """
    Custom dataset for Spittin Chiclets Podcast data.
    Formats data into prompt-response pairs for fine-tuning.
    """
    def __init__(self, data, tokenizer):
        """
        Initialize dataset with podcast data and tokenizer.
        
        Args:
            data: List of Spittin Chiclets objects
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
        text = data_point.text
        
        # Create a prompt asking for podcast information
        prompt = f"Today is {month}-{day}-{year}, tell me about some interesting stuff happening in the NHL."


        # Tokenize the prompt separately
        prompt_encoding = self.tokenizer(prompt, return_tensors="pt")
        #squeeze to drop batch dimension
        prompt_ids = prompt_encoding['input_ids'].squeeze(0)
        prompt_attention_mask = prompt_encoding['attention_mask'].squeeze(0)

        # Tokenize the response with optional padding/truncation
        # Dynamically adjusted padding to ensure uniform padding for batch
        if self.max_length:
            response_encoding = self.tokenizer(
                text, 
                return_tensors="pt", 
                max_length=(self.max_length - prompt_ids.shape[0]),
                truncation=True,
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

        self.download_directory_from_bucket("models/finetuned_model", "./models/finetuned_model")
        self.download_from_bucket("clean_data/usable_buzz_data.txt", "./clean_data/usable_buzz_data.txt")
        self.download_directory_from_bucket("spittin-chiclets", "./spittin-chiclets")
        self.tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
        # quantization implementation
        self.quantization_config = BitsAndBytesConfig(
                                    load_in_4bit=True,
                                    bnb_4bit_quant_type='nf4',
                                    bnb_4bit_compute_dtype='float16',
                                    bnb_4bit_use_double_quant=True,
                                )
        self.lora_config = LoraConfig(
                    r=16,                     # Rank
                    lora_alpha=32,           # Alpha scaling
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Which modules to apply LoRA to
                    lora_dropout=0.05,
                    bias="none",
                    task_type="CAUSAL_LM"
                )
        self.accelerator = Accelerator()
        self.model = self.load_model()
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=5e-5)
        self.model, self.optimizer = self.accelerator.prepare(self.model, self.optimizer)
        self.scheduler = torch.optim.lr_scheduler.StepLR(self.optimizer, step_size=1, gamma=0.99)
        self.dataset = None
        self.dataloader = None
        

    def upload_directory_to_bucket(self, source_directory, destination_directory, bucket_name="modelsbucket-amlc"):
        """
        Uploads all files from a local directory to a GCP bucket directory.
        
        Args:
            bucket_name: Name of the GCP bucket
            source_directory: Local directory path with files to upload
            destination_directory: Destination directory path in the bucket
        """
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Make sure source directory ends with slash for correct path handling
        if not source_directory.endswith('/'):
            source_directory += '/'
            
        # Get all files in the directory and subdirectories
        files = glob.glob(f"{source_directory}**", recursive=True)
        
        for file_path in files:
            # Skip directories, we only want to upload files
            if os.path.isdir(file_path):
                continue
                
            # Calculate the relative path to maintain directory structure
            relative_path = file_path.replace(source_directory, '')
            destination_blob_name = os.path.join(destination_directory, relative_path)
            
            # Create blob and upload
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path)
            print(f"Uploaded {file_path} to {destination_blob_name}")

    def download_from_bucket(self, source_blob_name, destination_file_name, bucket_name="modelsbucket-amlc"):
        """
        Downloads a file from a GCP bucket to a local destination.
        
        Args:
            bucket_name: Name of the GCP bucket
            source_blob_name: Path to the file in the bucket
            destination_file_name: Local path where the file should be saved
        """
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        
        blob.download_to_filename(destination_file_name)
        print(f"Downloaded {source_blob_name} to {destination_file_name}")



    def download_directory_from_bucket(
        self,
        source_directory,
        destination_directory,
        bucket_name="modelsbucket-amlc"):
        """Downloads all blobs under `source_directory` to `destination_directory`."""
        os.makedirs(destination_directory, exist_ok=True)

        storage_client = storage.Client()
        blobs = storage_client.list_blobs(bucket_name, prefix=source_directory)

        for blob in blobs:
            if blob.name.endswith("/"):          # skip “directory” placeholders
                continue

            # make path relative and kill any leading slash
            relative_path = blob.name[len(source_directory):].lstrip("/")
            local_file_path = os.path.join(destination_directory, relative_path)

            # ensure sub-dirs exist
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            blob.download_to_filename(local_file_path)
            print(f"Downloaded {blob.name} → {local_file_path}")

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
            model = AutoModelForCausalLM.from_pretrained("./models/finetuned_model", device_map="auto", quantization_config=self.quantization_config, torch_dtype=torch.float16)
            model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
            model = get_peft_model(model, self.lora_config)
            model.print_trainable_parameters()
            print("Saved model successfully loaded")
        except Exception as e:
            print(f"Failed to load model: {e}")
        if model is None:
            model = AutoModelForCausalLM.from_pretrained("google/gemma-2b")
            model = AutoModelForCausalLM.from_pretrained("google/gemma-2b", device_map="auto", quantization_config=self.quantization_config, torch_dtype=torch.float16)
            model = prepare_model_for_kbit_training(model ,use_gradient_checkpointing=True)
            model = get_peft_model(model, self.lora_config)
            model.print_trainable_parameters()
            print("Loading new model")
            if not os.path.isdir("./models/finetuned_model"):
                os.makedirs("./models/finetuned_model")
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
        for i in tqdm(range(len(dataset)), desc=f"Finding Max Length"):
            size = dataset[i]['input_ids'].shape[0]
            if size > largest:
                largest = size
        print(f"The largest encoded tensor is {largest}")
        return largest
    

    def load_in_buzz_data(self, batch=2):
        """
        Load and prepare NHL Buzz data for training.
        
        Args:
            batch: Batch size for training
        """
        self.dataset = BuzzDataset(DataCleaner.load_buzz_data(), self.tokenizer)
        self.dataset.set_max_length(self.largest_tokenization(self.dataset)) 
        self.dataloader = DataLoader(self.dataset, batch_size=batch, shuffle=True) 
        self.dataloader = self.accelerator.prepare(self.dataloader)
        self.accelerator.register_for_checkpointing(self.scheduler)
        self.accelerator.save_state(output_dir="./models/checkpoints")
        print(self.accelerator.device)
        

    def load_in_podcast_data(self, batch=2):
        """
        Load and prepare Spittin Chiclets data for training.
        
        Args:
            batch: Batch size for training
        """
        self.dataset = PodCastDataset(DataCleaner.load_pod_data(), self.tokenizer)
        self.dataset.set_max_length(816)
        self.dataloader = DataLoader(self.dataset, batch_size=batch, shuffle=True, num_workers=0, persistent_workers=False)
        self.dataloader = self.accelerator.prepare(self.dataloader)

    def train(self, epochs=4):
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
                print(f"Finished batch: {i} - batch loss: {loss.item()/len(batch)} - Progress: { (i+1) / len(self.dataloader) * 100:.2f}%") 

            # Report epoch results
            avg_loss = total_loss / len(self.dataloader)
            print(f"Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}")
            
            self.model = self.model.to("cpu")
            self.model.save_pretrained("./models/finetuned_model")
            self.tokenizer.save_pretrained("./models/finetuned_model")
            self.model = self.model.to(self.device)
            self.upload_directory_to_bucket("./models/finetuned_model", "models/finetuned_model")
            self.scheduler.step()
            
    def infernece(self, prompt):
        tokenized_prompt = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        self.model = self.model.to(self.device)
        outputs = self.model.generate(**tokenized_prompt, max_length=800)
        response = self.tokenizer.decode(outputs[0])
        return response

    def test_inference(self):
        response = self.infernece("What are the daily updates for the Dallas Stars on April-16-2025?")
        print(response)


if __name__ == "__main__":
    load_dotenv()
    access_token = os.getenv("HF_TOKEN")
    login(token=access_token)
    trainer = Trainer(get_data=False)
    trainer.load_in_buzz_data()
    trainer.train()
    trainer.load_in_podcast_data()
    trainer.train()
    trainer.test_inference()
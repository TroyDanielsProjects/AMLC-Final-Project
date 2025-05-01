import torch
from torch.utils.data import Dataset
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
from cleanAndLoadData import DataCleaner
from dotenv import load_dotenv
import os
from huggingface_hub import login
from tqdm import tqdm
import os
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from google.cloud import storage
import glob
from trl import SFTTrainer

os.environ["BNB_CUDA_VERSION"] = "123"

class Trainer:
    """
    Handles model training for the NHL Buzz news generation task.
    """
    def __init__(self):
        """
        Initialize trainer with model, tokenizer, and optimizer.
        """
        self.device = self.determine_device()
        self.datacleaner = DataCleaner()
        self.download_directory_from_bucket("models/finetuned_model", "./models/finetuned_model")
        self.download_from_bucket("clean_data/usable_buzz_data.txt", "./clean_data/usable_buzz_data.txt")
        self.download_directory_from_bucket("spittin-chiclets", "./spittin-chiclets")
        self.tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
        self.datacleaner.create_buzz_SFTTrainer_json()
        self.datacleaner.create_pod_SFTTrainer_json()
        # quantization implementation
        self.quantization_config = quantization_config = BitsAndBytesConfig(
                                    load_in_4bit=True,
                                    bnb_4bit_compute_dtype=torch.float16,
                                    bnb_4bit_quant_type="nf4"
                                )
        self.lora_config = LoraConfig(
                    r=16,                     # Rank
                    lora_alpha=32,           # Alpha scaling
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Which modules to apply LoRA to
                    lora_dropout=0.05,
                    bias="none",
                    task_type="CAUSAL_LM"
                )
        self.model = self.load_model()
        self.training_arguments = TrainingArguments(
            output_dir="./models/finetuned_model",
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            optim="paged_adamw_32bit",
            save_steps=10,
            logging_steps=10,
            learning_rate=2e-4,
            max_grad_norm=0.3,
            max_steps=1000,
            warmup_ratio=0.3,
            lr_scheduler_type="constant",
            gradient_checkpointing=True,
            fp16=False,
            bf16=False,
        )
        self.dataset = None
        

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
            model = AutoModelForCausalLM.from_pretrained(
            "google/gemma-2b", 
            quantization_config=self.uantization_config, 
            torch_dtype=torch.float32,
            attn_implementation="sdpa"
        )
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
        self.dataset = load_dataset("json", data_files="./clean_data/clean_buzz_SFT.jsonl", split="train")
        

    def load_in_podcast_data(self, batch=2):
        """
        Load and prepare Spittin Chiclets data for training.
        
        Args:
            batch: Batch size for training
        """
        self.dataset = load_dataset("json", data_files="./clean_data/clean_podcast_SFT.jsonl", split="train")

    def train(self, epochs=4):
        """
        Train the model.
        
        Args:
            epochs: Number of training epochs
        """
        trainer = SFTTrainer(
            model=self.model,
            args=self.training_arguments,
            train_dataset=self.dataset,
            peft_config=self.lora_config,
        )

        trainer.train()
        self.upload_directory_to_bucket("./models/finetuned_model", "/bucket/models/finetuned_model")
            
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
    trainer = Trainer()
    trainer.load_in_buzz_data()
    trainer.train()
    trainer.load_in_podcast_data()
    trainer.train()
    trainer.test_inference()
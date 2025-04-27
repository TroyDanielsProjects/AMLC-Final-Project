import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, AdamW
from cleanAndLoadData import DataCleaner

def largest_tokenization(dataset):
    largest = 0
    for i in range(len(dataset)):
        size = dataset[i]['input_ids'].shape[0]
        if size > largest:
            largest = size
    print(f"The largest encoded tensor is {largest}")
    return largest

class BuzzDataset(Dataset):

    def __init__(self, data, tokenizer):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = None

    def __len__(self):
        return len(self.data)
    
    def set_max_length(self, max_length):
        self.max_length = max_length
    
    def __getitem__(self, index):

        data_point =  self.data[index]
        year = data_point.year
        month = data_point.month
        day = data_point.day
        team = data_point.team
        text = data_point.text
        prompt = f"What are the daily updates for the {team} on {month}-{day}-{year}?"

        prompt_encoding = self.tokenizer(prompt, return_tensors="pt")
        prompt_ids = prompt_encoding['input_ids'].squeeze(0)
        prompt_attention_mask = prompt_encoding['attention_mask'].squeeze(0)

        if self.max_length:
            response_encoding = self.tokenizer(text, return_tensors="pt", max_length=(self.max_length - prompt_ids.shape[0]), padding='max_length', padding_side='right')
        else:
            response_encoding = self.tokenizer(text, return_tensors="pt")
        input_ids = response_encoding['input_ids'].squeeze(0)
        attention_mask = response_encoding['attention_mask'].squeeze(0)

        encoding = torch.concat((prompt_ids, input_ids), 0)
        attention_mask = torch.concat((prompt_attention_mask,attention_mask),0)
        labels = encoding.clone()
        labels[:prompt_ids.shape[0]] = -100

        if encoding.shape[0] > 8192:
            encoding = encoding[:8192]
            attention_mask = attention_mask[:8192]

        return {
            'input_ids': encoding,
            'attention_mask': attention_mask,
            'labels': labels,  # Teacher Forcing: labels are the same as input_ids
        }
    
data = DataCleaner().load_data()
tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
dataset = BuzzDataset(data,tokenizer)

largest = largest_tokenization(dataset)
dataset.set_max_length(largest)

train_loader = DataLoader(dataset, batch_size=4, shuffle=True)
model = AutoModelForCausalLM.from_pretrained("google/gemma-2b")

optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)

# Check if GPU is available
device = torch.device("mps" if torch.mps.is_available() else "cpu")
print(f"Using {device}")
model = model.to(device)

epochs = 1

model.train()

for epoch in range(epochs):
    total_loss = 0
    for i , batch in enumerate(train_loader):
        # Move input data to the same device as the model
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        optimizer.zero_grad()  # Reset gradients to avoid accumulation

        # Forward pass with teacher forcing: feed correct previous token
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels  # Teacher forcing mode
        )

        loss = outputs.loss  # CrossEntropy loss automatically computed inside model
        loss.backward()  # Compute gradients

        optimizer.step()  # Update parameters

        total_loss += loss.item()  # Accumulate total loss
        print(f"Finished batch: {i} - {i / len(train_loader)}%")

    avg_loss = total_loss / len(train_loader)  # Average loss per batch
    print(f"Epoch {epoch + 1} - Loss: {avg_loss:.4f}")
     
model.save_pretrained("./finetuned_model")
tokenizer.save_pretrained("./finetuned_model")
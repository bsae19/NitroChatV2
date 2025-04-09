from transformers import TFAutoModelForSequenceClassification, CamembertTokenizer

model_name = "tblard/tf-allocine"
model = TFAutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = CamembertTokenizer.from_pretrained(model_name, use_fast=False)

# Save the model and tokenizer locally
model.save_pretrained("../saved_model")
tokenizer.save_pretrained("../saved_model")
model_name = "../saved_model"
model = TFAutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = CamembertTokenizer.from_pretrained(model_name, use_fast=False)

print("Model and tokenizer saved to ./saved_model")
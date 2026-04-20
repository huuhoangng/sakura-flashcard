import os
import json
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizer, DistilBertPreTrainedModel, DistilBertModel

class MultiTaskDistilBert(DistilBertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.distilbert = DistilBertModel(config)
        self.dropout = torch.nn.Dropout(config.seq_classif_dropout)
        
        self.classifier_cefr1 = torch.nn.Linear(config.hidden_size, config.num_labels_cefr1)
        self.classifier_cefr2 = torch.nn.Linear(config.hidden_size, config.num_labels_cefr2)
        self.classifier_rel = torch.nn.Linear(config.hidden_size, config.num_labels_rel)
        
        self.post_init()

    def forward(self, input_ids, attention_mask=None, **kwargs):
        outputs = self.distilbert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs[0][:, 0]
        pooled_output = self.dropout(pooled_output)
        
        logits_cefr1 = self.classifier_cefr1(pooled_output)
        logits_cefr2 = self.classifier_cefr2(pooled_output)
        logits_rel = self.classifier_rel(pooled_output)
        
        return {"logits_cefr1": logits_cefr1, "logits_cefr2": logits_cefr2, "logits_rel": logits_rel}

class SemanticClassifier:
    def __init__(self, model_dir="./distilBERTModel"):
        """Loads the model, tokenizer, and encoders into memory."""
        print(f"Loading model from {model_dir}...")
        
        # Load Tokenizer
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_dir)
        
        # Load Model
        self.model = MultiTaskDistilBert.from_pretrained(model_dir)
        self.model.eval() # Set model to evaluation mode
        
        # Load Label Encoders
        encoder_path = os.path.join(model_dir, "label_encoders.json")
        with open(encoder_path, "r") as f:
            self.encoders = json.load(f)

    def predict(self, input1: str, input2: str, def1: str, def2: str):

        combined_text = f"Word 1: {input1} - Def: {def1} [SEP] Word 2: {input2} - Def: {def2}"
        
        # 2. Tokenize the input
        inputs = self.tokenizer(
            combined_text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"])
            
        probs_cefr1 = F.softmax(outputs["logits_cefr1"], dim=1)
        probs_cefr2 = F.softmax(outputs["logits_cefr2"], dim=1)
        probs_rel = F.softmax(outputs["logits_rel"], dim=1)
        
        conf_cefr1, idx_cefr1 = torch.max(probs_cefr1, dim=1)
        conf_cefr2, idx_cefr2 = torch.max(probs_cefr2, dim=1)
        conf_rel, idx_rel = torch.max(probs_rel, dim=1)
        
        label_cefr1 = self.encoders["cefr1"][idx_cefr1.item()]
        label_cefr2 = self.encoders["cefr2"][idx_cefr2.item()]
        label_rel = self.encoders["relationship"][idx_rel.item()]
        
        conf_cefr1 = round(conf_cefr1.item(), 4)
        conf_cefr2 = round(conf_cefr2.item(), 4)
        conf_rel = round(conf_rel.item(), 4)
        
        return label_cefr1, conf_cefr1, label_cefr2, conf_cefr2, label_rel, conf_rel
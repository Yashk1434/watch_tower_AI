import clip
import cv2
import numpy as np
import torch
import yaml
from PIL import Image

class Model:
    def __init__(self, settings_path: str = './settings.yaml'):
        with open(settings_path, "r") as file:
            self.settings = yaml.safe_load(file)

        # Initialize device
        self.device = torch.device("cpu")
        self.model_name = self.settings['model-settings']['model-name']
        self.threshold = self.settings['model-settings']['prediction-threshold']
        self.model, self.preprocess = clip.load(self.model_name, device=self.device)
        self.labels = self.settings['label-settings']['labels']
        self.labels_ = ['a photo of ' + label for label in self.labels]
        self.text_features = self.vectorize_text(self.labels_)
        self.default_label = self.settings['label-settings']['default-label']

    @torch.no_grad()
    def transform_image(self, image: np.ndarray):
        pil_image = Image.fromarray(image).convert('RGB')
        tf_image = self.preprocess(pil_image).unsqueeze(0).to(self.device)
        return tf_image

    @torch.no_grad()
    def tokenize(self, text: list):
        text = clip.tokenize(text).to(self.device)
        return text

    @torch.no_grad()
    def vectorize_text(self, text: list):
        tokens = self.tokenize(text=text)
        text_features = self.model.encode_text(tokens)
        return text_features

    @torch.no_grad()
    def predict_(self, text_features: torch.Tensor, image_features: torch.Tensor):
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        similarity = image_features @ text_features.T
        values, indices = similarity[0].topk(1)
        return values, indices

    @torch.no_grad()
    def predict(self, image: np.array) -> dict:
        tf_image = self.transform_image(image)
        image_features = self.model.encode_image(tf_image)
        values, indices = self.predict_(text_features=self.text_features, image_features=image_features)
        label_index = indices[0].cpu().item()
        label_text = self.default_label
        model_confidance = abs(values[0].cpu().item())
        if model_confidance >= self.threshold:
            label_text = self.labels[label_index]

        prediction = {
            'label': label_text,
            'confidence': model_confidance
        }
        return prediction

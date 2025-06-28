import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from typing import Tuple, Dict, Any, Optional
import cv2
import os
import urllib.request
from pathlib import Path

from pipeline.base_processor import BaseProcessor


class NIMA(nn.Module):
    """NIMA model using MobileNet as base."""
    
    def __init__(self, base_model: nn.Module):
        super(NIMA, self).__init__()
        self.features = base_model.features
        self.classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(1280, 10),  # MobileNetV2 has 1280 output features
            nn.Softmax(dim=1)
        )
        
    def forward(self, x):
        x = self.features(x)
        x = nn.functional.adaptive_avg_pool2d(x, 1).reshape(x.shape[0], -1)
        x = self.classifier(x)
        return x


class QualityAssessmentProcessor(BaseProcessor):
    """
    Uses NIMA (Neural Image Assessment) to evaluate image quality.
    Provides both aesthetic and technical quality scores.
    """
    
    MODEL_URL = "https://github.com/idealo/image-quality-assessment/releases/download/v1.0/mobilenet_aesthetic_0.07.pth"
    MODEL_PATH = Path("models/nima_mobilenet_aesthetic.pth")
    
    def __init__(self):
        super().__init__(name="Quality Assessment", processor_type="quality_assessment")
        self.parameters = {
            'threshold': 5.0,  # Quality threshold (1-10)
            'auto_cull': False,  # Automatically mark low quality images
            'assess_type': 'aesthetic',  # 'aesthetic' or 'technical'
        }
        self.model: Optional[NIMA] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        self._load_model()
    
    def _load_model(self):
        """Load the NIMA model."""
        try:
            # Create models directory if it doesn't exist
            self.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Download model if not exists
            if not self.MODEL_PATH.exists():
                print(f"Downloading NIMA model to {self.MODEL_PATH}...")
                urllib.request.urlretrieve(self.MODEL_URL, self.MODEL_PATH)
                print("Download complete!")
            
            # Load base model
            base_model = models.mobilenet_v2(pretrained=False)
            
            # Create NIMA model
            self.model = NIMA(base_model)
            
            # Load weights
            state_dict = torch.load(self.MODEL_PATH, map_location=self.device)
            # Handle different state dict formats
            if 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']
            
            # Fix state dict keys if needed
            new_state_dict = {}
            for k, v in state_dict.items():
                if k.startswith('module.'):
                    new_state_dict[k[7:]] = v
                else:
                    new_state_dict[k] = v
            
            self.model.load_state_dict(new_state_dict, strict=False)
            self.model.to(self.device)
            self.model.eval()
            
        except Exception as e:
            print(f"Warning: Failed to load NIMA model: {e}")
            print("Quality assessment will return mock scores.")
            self.model = None
    
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """Estimate memory usage for quality assessment."""
        # Model inference is relatively light
        # Main memory is for image preprocessing and model
        return 224 * 224 * 3 * 4 + 100 * 1024 * 1024  # ~100MB for model
    
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """For preview, just return the image with quality score overlay."""
        score, distribution = self._assess_quality(image)
        
        # Add quality score overlay
        result = image.copy()
        self._add_quality_overlay(result, score)
        
        return result
    
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """Full processing returns image with detailed quality metrics."""
        score, distribution = self._assess_quality(image)
        
        # Store quality metrics in parameters for access
        self.parameters['last_score'] = score
        self.parameters['last_distribution'] = distribution
        
        # If auto-cull is enabled and score is below threshold
        if self.parameters['auto_cull'] and score < self.parameters['threshold']:
            # Mark image for culling (actual culling handled by pipeline)
            self.parameters['marked_for_cull'] = True
        
        # Return original image (assessment doesn't modify the image)
        return image
    
    def _assess_quality(self, image: np.ndarray) -> Tuple[float, np.ndarray]:
        """Assess image quality using NIMA model."""
        if self.model is None:
            # Return mock score if model not loaded
            return 5.0 + np.random.randn() * 0.5, np.ones(10) / 10
        
        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Transform image
            img_tensor = self.transform(image_rgb).unsqueeze(0).to(self.device)
            
            # Get prediction
            with torch.no_grad():
                output = self.model(img_tensor)
                distribution = output.cpu().numpy()[0]
            
            # Calculate mean score
            score_range = np.arange(1, 11)
            score = np.sum(score_range * distribution)
            
            return float(score), distribution
            
        except Exception as e:
            print(f"Error in quality assessment: {e}")
            return 5.0, np.ones(10) / 10
    
    def _add_quality_overlay(self, image: np.ndarray, score: float):
        """Add quality score overlay to image."""
        height, width = image.shape[:2]
        
        # Create semi-transparent overlay
        overlay = image.copy()
        
        # Determine color based on score
        if score >= 7:
            color = (0, 255, 0)  # Green for high quality
        elif score >= 5:
            color = (0, 165, 255)  # Orange for medium quality
        else:
            color = (0, 0, 255)  # Red for low quality
        
        # Add score box
        cv2.rectangle(overlay, (10, 10), (150, 50), (0, 0, 0), -1)
        cv2.putText(overlay, f"Quality: {score:.2f}", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Blend with original
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get detailed quality metrics from last assessment."""
        return {
            'score': self.parameters.get('last_score', 0),
            'distribution': self.parameters.get('last_distribution', []),
            'threshold': self.parameters['threshold'],
            'marked_for_cull': self.parameters.get('marked_for_cull', False),
            'assess_type': self.parameters['assess_type']
        }
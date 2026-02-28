import os
import torch

class ModelManager:
    """Manages AI model loading and caching"""
    
    def __init__(self):
        self.cache_dir = os.getenv('CACHE_DIR', './models_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._models = {}
    
    def get_device(self):
        """Get the current compute device"""
        return self.device
    
    def get_compute_type(self):
        """Get optimal compute type for the device"""
        return "float16" if self.device == "cuda" else "int8"
    
    def is_model_loaded(self, model_name):
        """Check if a model is already loaded"""
        return model_name in self._models
    
    def cache_model(self, model_name, model):
        """Cache a loaded model"""
        self._models[model_name] = model
    
    def get_cached_model(self, model_name):
        """Get a cached model"""
        return self._models.get(model_name)
    
    def clear_cache(self):
        """Clear all cached models"""
        self._models.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def get_model_info(self):
        """Get information about loaded models"""
        return {
            'device': self.device,
            'compute_type': self.get_compute_type(),
            'cuda_available': torch.cuda.is_available(),
            'loaded_models': list(self._models.keys()),
            'cache_dir': self.cache_dir
        }

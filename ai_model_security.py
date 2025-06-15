"""
AI Model Security Module for DeFi Arbitrage System
-------------------------------------------------
This module provides comprehensive security features for AI/ML models used in the arbitrage system:
1. Model Registry: Versioning, encryption, and integrity verification
2. Adversarial Protection: Detection and prevention of adversarial attacks
3. Performance Monitoring: Detect model degradation and drift
4. Data Validation: Ensure input data quality and detect poisoning attempts
"""

import os
import json
import hashlib
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime
from cryptography.fernet import Fernet
import tensorflow as tf
import torch
import pickle
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import shutil
import tempfile
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai_security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_model_security")

# Constants
MODEL_REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_registry")
ADVERSARIAL_EXAMPLES_PATH = os.path.join(MODEL_REGISTRY_PATH, "adversarial_examples")
PERFORMANCE_HISTORY_PATH = os.path.join(MODEL_REGISTRY_PATH, "performance_history")
DATASET_STATISTICS_PATH = os.path.join(MODEL_REGISTRY_PATH, "dataset_statistics")
BACKUP_PATH = os.path.join(MODEL_REGISTRY_PATH, "backups")

# Create necessary directories
for path in [MODEL_REGISTRY_PATH, ADVERSARIAL_EXAMPLES_PATH, PERFORMANCE_HISTORY_PATH, 
             DATASET_STATISTICS_PATH, BACKUP_PATH]:
    os.makedirs(path, exist_ok=True)

# Generate encryption key if not exists
KEY_PATH = os.path.join(MODEL_REGISTRY_PATH, ".key")
if not os.path.exists(KEY_PATH):
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as key_file:
        key_file.write(key)
else:
    with open(KEY_PATH, "rb") as key_file:
        key = key_file.read()

# Initialize encryption
fernet = Fernet(key)

class ModelMetadata:
    """Metadata for registered models"""
    def __init__(self, model_id: str, version: str, framework: str, 
                 model_hash: str, created_at: datetime, 
                 file_path: str, is_encrypted: bool = True):
        self.model_id = model_id
        self.version = version
        self.framework = framework
        self.model_hash = model_hash
        self.created_at = created_at
        self.file_path = file_path
        self.is_encrypted = is_encrypted
        self.is_production = False
        self.last_validated = None
        self.validation_score = None

class ModelRegistry:
    """Registry for managing AI models with versioning and security features"""
    
    def __init__(self, registry_path: str = MODEL_REGISTRY_PATH):
        """Initialize the model registry"""
        self.registry_path = registry_path
        self.metadata_path = os.path.join(registry_path, "metadata.json")
        self.models_metadata = self._load_metadata()
        
        # Ensure model directory exists
        os.makedirs(registry_path, exist_ok=True)
        
        logger.info(f"Model registry initialized at {registry_path}")
    
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load model metadata from disk"""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r") as f:
                    metadata = json.load(f)
                return metadata
            except Exception as e:
                # Use the centralized error handler
                from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
                error_details = ErrorHandler.handle_exception(
                    e,
                    category=ErrorCategory.CONFIGURATION,
                    severity=ErrorSeverity.ERROR,
                    error_id=2001,
                    context={"operation": "load_metadata", "path": self.metadata_path}
                )
                logger.error(f"Error loading metadata: {error_details['error_code']}")
                return {}
        return {}
    
    def _save_metadata(self):
        """Save model metadata to disk"""
        with open(self.metadata_path, "w") as f:
            json.dump(self.models_metadata, f, indent=2, default=str)
    
    def register_model(self, model, model_id: str, version: str, framework: str,
                      encrypt: bool = True, additional_metadata: Dict = None) -> str:
        """
        Register a model in the registry
        
        Args:
            model: The model object to register
            model_id: Unique identifier for the model
            version: Version string
            framework: Framework used (tensorflow, pytorch, sklearn, etc.)
            encrypt: Whether to encrypt the model file
            additional_metadata: Additional metadata to store
            
        Returns:
            model_hash: Hash of the registered model
        """
        # Validate inputs
        if not model_id or not version or not framework:
            raise ValueError("model_id, version, and framework are required")
        
        # Generate model hash
        model_hash = self._generate_model_hash(model)
        
        # Check if model already exists
        model_key = f"{model_id}_{version}"
        if model_key in self.models_metadata:
            logger.warning(f"Model {model_id} version {version} already exists. Overwriting.")
        
        # Save model to file
        file_path = self._save_model(model, model_id, version, framework)
        
        # Encrypt model if requested
        if encrypt:
            self._encrypt_model(file_path)
        
        # Create metadata
        metadata = {
            "model_id": model_id,
            "version": version,
            "framework": framework,
            "model_hash": model_hash,
            "created_at": datetime.now(),
            "file_path": file_path,
            "is_encrypted": encrypt,
            "is_production": False,
            "last_validated": None,
            "validation_score": None
        }
        
        # Add additional metadata if provided
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Store metadata
        self.models_metadata[model_key] = metadata
        self._save_metadata()
        
        logger.info(f"Model {model_id} version {version} registered successfully")
        return model_hash
    
    def _save_model(self, model, model_id: str, version: str, framework: str) -> str:
        """Save model to file based on framework"""
        # Create directory for model if it doesn't exist
        model_dir = os.path.join(self.registry_path, model_id)
        os.makedirs(model_dir, exist_ok=True)
        
        # Determine file extension based on framework
        if framework.lower() == "tensorflow":
            file_path = os.path.join(model_dir, f"{version}")
            tf.keras.models.save_model(model, file_path)
        elif framework.lower() == "pytorch":
            file_path = os.path.join(model_dir, f"{version}.pt")
            torch.save(model.state_dict(), file_path)
        elif framework.lower() == "sklearn":
            file_path = os.path.join(model_dir, f"{version}.joblib")
            joblib.dump(model, file_path)
        else:
            # Default to pickle for unknown frameworks
            file_path = os.path.join(model_dir, f"{version}.pkl")
            with open(file_path, "wb") as f:
                pickle.dump(model, f)
        
        return file_path
    
    def _encrypt_model(self, model_path: str):
        """Encrypt model file"""
        try:
            # Read the model file
            with open(model_path, "rb") as f:
                model_data = f.read()
            
            # Encrypt the data
            encrypted_data = fernet.encrypt(model_data)
            
            # Write encrypted data back to file
            with open(model_path, "wb") as f:
                f.write(encrypted_data)
            
            logger.info(f"Model at {model_path} encrypted successfully")
        except Exception as e:
            logger.error(f"Error encrypting model: {e}")
            raise
    
    def _decrypt_model(self, model_path: str, output_path: str):
        """Decrypt model file to a temporary location"""
        try:
            # Read the encrypted model file
            with open(model_path, "rb") as f:
                encrypted_data = f.read()
            
            # Decrypt the data
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Write decrypted data to output path
            with open(output_path, "wb") as f:
                f.write(decrypted_data)
            
            logger.info(f"Model decrypted to {output_path}")
        except Exception as e:
            logger.error(f"Error decrypting model: {e}")
            raise
    
    def _generate_model_hash(self, model) -> str:
        """Generate a hash for the model"""
        # For TensorFlow models
        if isinstance(model, tf.keras.Model):
            model_json = model.to_json()
            weights = []
            for layer in model.layers:
                weights.extend([w.numpy().tobytes() for w in layer.weights])
            model_bytes = model_json.encode() + b''.join(weights)
        
        # For PyTorch models
        elif isinstance(model, torch.nn.Module):
            buffer = io.BytesIO()
            torch.save(model.state_dict(), buffer)
            model_bytes = buffer.getvalue()
        
        # For scikit-learn models
        else:
            buffer = io.BytesIO()
            pickle.dump(model, buffer)
            model_bytes = buffer.getvalue()
        
        # Generate hash
        return hashlib.sha256(model_bytes).hexdigest()
    
    def load_model(self, model_id: str, version: str = None) -> Tuple[Any, Dict]:
        """
        Load a model from the registry
        
        Args:
            model_id: Model identifier
            version: Specific version to load, or None for production version
            
        Returns:
            model: The loaded model
            metadata: Model metadata
        """
        # If version is not specified, load the production version
        if version is None:
            # Find production version
            for key, metadata in self.models_metadata.items():
                if metadata["model_id"] == model_id and metadata.get("is_production", False):
                    version = metadata["version"]
                    break
            
            if version is None:
                raise ValueError(f"No production version found for model {model_id}")
        
        # Get model metadata
        model_key = f"{model_id}_{version}"
        if model_key not in self.models_metadata:
            raise ValueError(f"Model {model_id} version {version} not found")
        
        metadata = self.models_metadata[model_key]
        file_path = metadata["file_path"]
        framework = metadata["framework"]
        is_encrypted = metadata.get("is_encrypted", False)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Model file not found: {file_path}")
            self._handle_integrity_failure(model_id, version)
            raise FileNotFoundError(f"Model file not found: {file_path}")
        
        # Create temporary file for decrypted model if needed
        temp_file = None
        try:
            if is_encrypted:
                # Create temporary file
                temp_fd, temp_path = tempfile.mkstemp()
                os.close(temp_fd)
                
                # Decrypt model to temporary file
                self._decrypt_model(file_path, temp_path)
                load_path = temp_path
            else:
                load_path = file_path
            
            # Load model based on framework
            if framework.lower() == "tensorflow":
                model = tf.keras.models.load_model(load_path)
            elif framework.lower() == "pytorch":
                # Get model class
                model_class = self._get_model_class(model_id)
                model = model_class()
                model.load_state_dict(torch.load(load_path))
                model.eval()
            elif framework.lower() == "sklearn":
                model = joblib.load(load_path)
            else:
                # Default to pickle for unknown frameworks
                with open(load_path, "rb") as f:
                    model = pickle.load(f)
            
            logger.info(f"Model {model_id} version {version} loaded successfully")
            return model, metadata
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self._handle_integrity_failure(model_id, version)
            raise
        finally:
            # Clean up temporary file if it was created
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def _get_model_class(self, model_id: str):
        """Get the model class for PyTorch models"""
        # This would need to be implemented based on your model architecture
        # For now, we'll raise an error
        raise NotImplementedError("Model class lookup not implemented")
    
    def _handle_integrity_failure(self, model_id: str, version: str):
        """Handle integrity failure by rolling back to a previous version"""
        logger.warning(f"Integrity failure for model {model_id} version {version}")
        
        # Find previous versions
        previous_versions = []
        for key, metadata in self.models_metadata.items():
            if metadata["model_id"] == model_id and metadata["version"] != version:
                previous_versions.append((metadata["version"], metadata["created_at"]))
        
        if previous_versions:
            # Sort by creation date (newest first)
            previous_versions.sort(key=lambda x: x[1], reverse=True)
            
            # Try to roll back to the most recent previous version
            rollback_version = previous_versions[0][0]
            logger.info(f"Attempting to roll back to version {rollback_version}")
            
            # Mark the current version as compromised
            model_key = f"{model_id}_{version}"
            self.models_metadata[model_key]["compromised"] = True
            self.models_metadata[model_key]["is_production"] = False
            
            # Set the previous version as production
            rollback_key = f"{model_id}_{rollback_version}"
            self.models_metadata[rollback_key]["is_production"] = True
            
            self._save_metadata()
            logger.info(f"Rolled back to version {rollback_version}")
        else:
            logger.error(f"No previous versions found for model {model_id}")
    
    def set_production_version(self, model_id: str, version: str):
        """Set a specific version as the production version"""
        # Check if model exists
        model_key = f"{model_id}_{version}"
        if model_key not in self.models_metadata:
            raise ValueError(f"Model {model_id} version {version} not found")
        
        # Unset current production version
        for key, metadata in self.models_metadata.items():
            if metadata["model_id"] == model_id and metadata.get("is_production", False):
                self.models_metadata[key]["is_production"] = False
        
        # Set new production version
        self.models_metadata[model_key]["is_production"] = True
        self._save_metadata()
        
        logger.info(f"Model {model_id} version {version} set as production")
    
    def create_backup(self, model_id: str, version: str):
        """Create a backup of a model version"""
        # Check if model exists
        model_key = f"{model_id}_{version}"
        if model_key not in self.models_metadata:
            raise ValueError(f"Model {model_id} version {version} not found")
        
        metadata = self.models_metadata[model_key]
        file_path = metadata["file_path"]
        
        # Create backup directory
        backup_dir = os.path.join(BACKUP_PATH, model_id)
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{version}_{timestamp}")
        
        # Copy model file
        shutil.copy2(file_path, backup_path)
        
        # Save backup metadata
        backup_metadata = metadata.copy()
        backup_metadata["original_path"] = file_path
        backup_metadata["backup_path"] = backup_path
        backup_metadata["backup_time"] = timestamp
        
        backup_meta_path = os.path.join(backup_dir, f"{version}_{timestamp}.json")
        with open(backup_meta_path, "w") as f:
            json.dump(backup_metadata, f, indent=2, default=str)
        
        logger.info(f"Backup created for model {model_id} version {version}")
        return backup_path
    
    def rollback(self, model_id: str, target_version: str):
        """Roll back to a specific version"""
        # Check if target version exists
        target_key = f"{model_id}_{target_version}"
        if target_key not in self.models_metadata:
            raise ValueError(f"Target version {target_version} not found for model {model_id}")
        
        # Find current production version
        current_prod_version = None
        for key, metadata in self.models_metadata.items():
            if metadata["model_id"] == model_id and metadata.get("is_production", False):
                current_prod_version = metadata["version"]
                break
        
        # Create backup of current production version if it exists
        if current_prod_version:
            self.create_backup(model_id, current_prod_version)
        
        # Set target version as production
        self.set_production_version(model_id, target_version)
        
        logger.info(f"Rolled back model {model_id} to version {target_version}")


class AdversarialProtection:
    """Protection against adversarial attacks on AI models"""
    
    def __init__(self, model_registry: ModelRegistry):
        """Initialize adversarial protection"""
        self.model_registry = model_registry
        self.adversarial_examples = self._load_adversarial_examples()
        
        # Initialize anomaly detectors for each model
        self.anomaly_detectors = {}
        
        # Initialize statistical thresholds for each model
        self.statistical_thresholds = {}
        
        # Initialize input validation models
        self.input_validators = {}
        
        logger.info("Adversarial protection initialized")
    
    def _load_adversarial_examples(self) -> Dict[str, List[np.ndarray]]:
        """Load known adversarial examples"""
        examples = {}
        
        if os.path.exists(ADVERSARIAL_EXAMPLES_PATH):
            for model_id in os.listdir(ADVERSARIAL_EXAMPLES_PATH):
                model_path = os.path.join(ADVERSARIAL_EXAMPLES_PATH, model_id)
                if os.path.isdir(model_path):
                    examples[model_id] = []
                    for example_file in os.listdir(model_path):
                        if example_file.endswith(".npy"):
                            example_path = os.path.join(model_path, example_file)
                            try:
                                example = np.load(example_path)
                                examples[model_id].append(example)
                            except Exception as e:
                                logger.error(f"Error loading adversarial example: {e}")
        
        return examples
    
    def detect_adversarial_input(self, model_id: str, input_data: np.ndarray) -> bool:
        """
        Detect if input is potentially adversarial
        
        Args:
            model_id: Model identifier
            input_data: Input data to check
            
        Returns:
            is_adversarial: True if input appears to be adversarial
        """
        # Check if we have adversarial examples for this model
        if model_id not in self.adversarial_examples or not self.adversarial_examples[model_id]:
            logger.warning(f"No adversarial examples for model {model_id}")
            return self._is_statistical_outlier(input_data)
        
        # Check similarity to known adversarial examples
        for example in self.adversarial_examples[model_id]:
            similarity = self._compute_similarity(input_data, example)
            if similarity > 0.85:  # High similarity threshold
                logger.warning(f"Input similar to known adversarial example (similarity: {similarity})")
                return True
        
        # Check if input is a statistical outlier
        if self._is_statistical_outlier(input_data):
            logger.warning("Input detected as statistical outlier")
            return True
        
        # Use anomaly detector if available
        if model_id in self.anomaly_detectors:
            detector = self.anomaly_detectors[model_id]
            # Reshape for isolation forest if needed
            reshaped_input = input_data.reshape(1, -1)
            prediction = detector.predict(reshaped_input)
            if prediction[0] == -1:  # Isolation Forest returns -1 for anomalies
                logger.warning("Input detected as anomaly by isolation forest")
                return True
        
        return False
    
    def _compute_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute similarity between two inputs"""
        # Ensure inputs are flattened
        a_flat = a.flatten()
        b_flat = b.flatten()
        
        # If dimensions don't match, return 0 similarity
        if a_flat.shape != b_flat.shape:
            return 0.0
        
        # Compute cosine similarity
        dot_product = np.dot(a_flat, b_flat)
        norm_a = np.linalg.norm(a_flat)
        norm_b = np.linalg.norm(b_flat)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _is_statistical_outlier(self, data: np.ndarray, z_threshold: float = 3.0) -> bool:
        """Check if data is a statistical outlier"""
        # Flatten data
        flat_data = data.flatten()
        
        # Calculate z-scores
        mean = np.mean(flat_data)
        std = np.std(flat_data)
        
        if std == 0:
            return False
        
        z_scores = np.abs((flat_data - mean) / std)
        
        # Check if any value exceeds the threshold
        return np.any(z_scores > z_threshold)
    
    def add_adversarial_example(self, model_id: str, example: np.ndarray):
        """Add a known adversarial example"""
        # Create directory for model if it doesn't exist
        model_dir = os.path.join(ADVERSARIAL_EXAMPLES_PATH, model_id)
        os.makedirs(model_dir, exist_ok=True)
        
        # Initialize list for model if it doesn't exist
        if model_id not in self.adversarial_examples:
            self.adversarial_examples[model_id] = []
        
        # Add example to list
        self.adversarial_examples[model_id].append(example)
        
        # Save example to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        example_path = os.path.join(model_dir, f"adversarial_{timestamp}.npy")
        np.save(example_path, example)
        
        logger.info(f"Added adversarial example for model {model_id}")
    
    def generate_adversarial_examples(self, model_id: str, version: str,
                                     benign_inputs: np.ndarray, benign_labels: np.ndarray,
                                     epsilon: float = 0.1, num_examples: int = 10) -> List[np.ndarray]:
        """
        Generate adversarial examples using Fast Gradient Sign Method (FGSM)
        
        Args:
            model_id: Model identifier
            version: Model version
            benign_inputs: Clean inputs
            benign_labels: True labels
            epsilon: Perturbation magnitude
            num_examples: Number of examples to generate
            
        Returns:
            adversarial_examples: List of generated adversarial examples
        """
        # Load model
        model, metadata = self.model_registry.load_model(model_id, version)
        framework = metadata["framework"]
        
        adversarial_examples = []
        
        # Generate examples based on framework
        if framework.lower() == "tensorflow":
            # TensorFlow implementation
            for i in range(min(num_examples, len(benign_inputs))):
                x = tf.convert_to_tensor(benign_inputs[i:i+1])
                y = tf.convert_to_tensor(benign_labels[i:i+1])
                
                with tf.GradientTape() as tape:
                    tape.watch(x)
                    prediction = model(x)
                    loss = tf.keras.losses.categorical_crossentropy(y, prediction)
                
                gradient = tape.gradient(loss, x)
                signed_grad = tf.sign(gradient)
                adversarial_x = x + epsilon * signed_grad
                adversarial_x = tf.clip_by_value(adversarial_x, 0, 1)  # Ensure valid range
                
                # Add to examples
                adversarial_examples.append(adversarial_x.numpy()[0])
                
                # Save as known adversarial example
                self.add_adversarial_example(model_id, adversarial_x.numpy()[0])
        
        elif framework.lower() == "pytorch":
            # PyTorch implementation
            model.eval()
            for i in range(min(num_examples, len(benign_inputs))):
                x = torch.tensor(benign_inputs[i:i+1], requires_grad=True)
                y = torch.tensor(benign_labels[i:i+1])
                
                output = model(x)
                loss = torch.nn.functional.cross_entropy(output, y)
                
                model.zero_grad()
                loss.backward()
                
                adversarial_x = x + epsilon * torch.sign(x.grad)
                adversarial_x = torch.clamp(adversarial_x, 0, 1)  # Ensure valid range
                
                # Add to examples
                adversarial_examples.append(adversarial_x.detach().numpy()[0])
                
                # Save as known adversarial example
                self.add_adversarial_example(model_id, adversarial_x.detach().numpy()[0])
        
        else:
            logger.warning(f"Adversarial example generation not implemented for framework {framework}")
        
        return adversarial_examples
    
    def train_anomaly_detector(self, model_id: str, normal_inputs: np.ndarray):
        """Train an anomaly detector for a model using Isolation Forest"""
        # Reshape inputs for Isolation Forest
        reshaped_inputs = normal_inputs.reshape(normal_inputs.shape[0], -1)
        
        # Train Isolation Forest
        detector = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=0.01,  # Assume 1% of training data might be anomalous
            random_state=42
        )
        detector.fit(reshaped_inputs)
        
        # Store detector
        self.anomaly_detectors[model_id] = detector
        
        # Save detector to file
        model_dir = os.path.join(ADVERSARIAL_EXAMPLES_PATH, model_id)
        os.makedirs(model_dir, exist_ok=True)
        detector_path = os.path.join(model_dir, "anomaly_detector.joblib")
        joblib.dump(detector, detector_path)
        
        logger.info(f"Trained anomaly detector for model {model_id}")


class PerformanceMonitor:
    """Monitor model performance and detect degradation"""
    
    def __init__(self, model_registry: ModelRegistry):
        """Initialize performance monitor"""
        self.model_registry = model_registry
        self.performance_history = self._load_performance_history()
        
        # Thresholds for performance degradation
        self.degradation_thresholds = {
            "accuracy": 0.05,  # 5% drop in accuracy
            "precision": 0.05,
            "recall": 0.05,
            "f1": 0.05,
            "mse": 0.1,  # 10% increase in MSE
            "mae": 0.1,
            "profit": 0.15  # 15% drop in profit
        }
        
        logger.info("Performance monitor initialized")
    
    def _load_performance_history(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Load performance history from disk"""
        history = {}
        
        if os.path.exists(PERFORMANCE_HISTORY_PATH):
            for model_id in os.listdir(PERFORMANCE_HISTORY_PATH):
                model_path = os.path.join(PERFORMANCE_HISTORY_PATH, model_id)
                if os.path.isdir(model_path):
                    history[model_id] = {}
                    
                    for version_file in os.listdir(model_path):
                        if version_file.endswith(".json"):
                            version = version_file.split(".")[0]
                            version_path = os.path.join(model_path, version_file)
                            
                            try:
                                with open(version_path, "r") as f:
                                    version_history = json.load(f)
                                
                                history[model_id][version] = version_history
                            except Exception as e:
                                logger.error(f"Error loading performance history: {e}")
        
        return history
    
    def record_performance(self, model_id: str, version: str,
                          metrics: Dict[str, float], timestamp: datetime = None):
        """
        Record model performance metrics
        
        Args:
            model_id: Model identifier
            version: Model version
            metrics: Dictionary of performance metrics
            timestamp: Timestamp of the measurement (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Initialize model and version in history if they don't exist
        if model_id not in self.performance_history:
            self.performance_history[model_id] = {}
        
        if version not in self.performance_history[model_id]:
            self.performance_history[model_id][version] = []
        
        # Add metrics to history
        record = {
            "timestamp": timestamp,
            "metrics": metrics
        }
        
        self.performance_history[model_id][version].append(record)
        
        # Save to disk
        model_dir = os.path.join(PERFORMANCE_HISTORY_PATH, model_id)
        os.makedirs(model_dir, exist_ok=True)
        
        version_path = os.path.join(model_dir, f"{version}.json")
        with open(version_path, "w") as f:
            json.dump(self.performance_history[model_id][version], f, indent=2, default=str)
        
        logger.info(f"Recorded performance metrics for model {model_id} version {version}")
        
        # Check for degradation
        degradation = self.check_degradation(model_id, version, metrics)
        if degradation:
            logger.warning(f"Performance degradation detected for model {model_id} version {version}")
            return degradation
        
        return None
    
    def check_degradation(self, model_id: str, version: str,
                         current_metrics: Dict[str, float],
                         window_size: int = 5) -> Dict[str, float]:
        """
        Check if current performance indicates degradation
        
        Args:
            model_id: Model identifier
            version: Model version
            current_metrics: Current performance metrics
            window_size: Number of previous measurements to compare against
            
        Returns:
            degradation: Dictionary of degraded metrics and their magnitude, or None
        """
        # Check if we have enough history
        if (model_id not in self.performance_history or
            version not in self.performance_history[model_id] or
            len(self.performance_history[model_id][version]) < window_size):
            return None
        
        # Get recent history
        history = self.performance_history[model_id][version][-window_size:]
        
        # Calculate average metrics over the window
        avg_metrics = {}
        for metric in current_metrics.keys():
            values = [record["metrics"].get(metric, 0) for record in history if metric in record["metrics"]]
            if values:
                avg_metrics[metric] = sum(values) / len(values)
        
        # Check for degradation
        degradation = {}
        for metric, current_value in current_metrics.items():
            if metric in avg_metrics and metric in self.degradation_thresholds:
                threshold = self.degradation_thresholds[metric]
                avg_value = avg_metrics[metric]
                
                # For metrics where higher is better (accuracy, precision, recall, f1, profit)
                if metric in ["accuracy", "precision", "recall", "f1", "profit"]:
                    if avg_value - current_value > threshold * avg_value:
                        degradation[metric] = {
                            "previous": avg_value,
                            "current": current_value,
                            "change": (current_value - avg_value) / avg_value
                        }
                
                # For metrics where lower is better (mse, mae)
                elif metric in ["mse", "mae"]:
                    if current_value - avg_value > threshold * avg_value:
                        degradation[metric] = {
                            "previous": avg_value,
                            "current": current_value,
                            "change": (current_value - avg_value) / avg_value
                        }
        
        return degradation if degradation else None
    
    def plot_performance_trend(self, model_id: str, version: str, metric: str):
        """
        Plot performance trend for a specific metric
        
        Args:
            model_id: Model identifier
            version: Model version
            metric: Metric to plot
        """
        if (model_id not in self.performance_history or
            version not in self.performance_history[model_id]):
            logger.warning(f"No performance history for model {model_id} version {version}")
            return
        
        history = self.performance_history[model_id][version]
        
        # Extract timestamps and metric values
        timestamps = []
        values = []
        
        for record in history:
            if metric in record["metrics"]:
                timestamps.append(record["timestamp"])
                values.append(record["metrics"][metric])
        
        if not timestamps:
            logger.warning(f"No data for metric {metric}")
            return
        
        # Create plot
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, values, marker='o')
        plt.title(f"{metric.upper()} Trend for Model {model_id} Version {version}")
        plt.xlabel("Time")
        plt.ylabel(metric.upper())
        plt.grid(True)
        
        # Add trend line
        z = np.polyfit(range(len(timestamps)), values, 1)
        p = np.poly1d(z)
        plt.plot(timestamps, p(range(len(timestamps))), "r--", alpha=0.8)
        
        # Save plot
        model_dir = os.path.join(PERFORMANCE_HISTORY_PATH, model_id)
        os.makedirs(model_dir, exist_ok=True)
        plot_path = os.path.join(model_dir, f"{version}_{metric}_trend.png")
        plt.savefig(plot_path)
        
        logger.info(f"Performance trend plot saved to {plot_path}")


class DataValidation:
    """Validate input data and detect poisoning attempts"""
    
    def __init__(self):
        """Initialize data validation"""
        self.dataset_statistics = {}
        
        # Load existing statistics if available
        if os.path.exists(os.path.join(DATASET_STATISTICS_PATH, "statistics.json")):
            try:
                with open(os.path.join(DATASET_STATISTICS_PATH, "statistics.json"), "r") as f:
                    self.dataset_statistics = json.load(f)
            except Exception as e:
                logger.error(f"Error loading dataset statistics: {e}")
        
        logger.info("Data validation initialized")
    
    def compute_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """Compute statistical properties of data"""
        # Flatten data for consistent statistics
        flat_data = data.reshape(-1)
        
        stats = {
            "mean": float(np.mean(flat_data)),
            "std": float(np.std(flat_data)),
            "min": float(np.min(flat_data)),
            "max": float(np.max(flat_data)),
            "median": float(np.median(flat_data)),
            "q1": float(np.percentile(flat_data, 25)),
            "q3": float(np.percentile(flat_data, 75)),
            "skewness": float(((flat_data - np.mean(flat_data))**3).mean() / np.std(flat_data)**3),
            "kurtosis": float(((flat_data - np.mean(flat_data))**4).mean() / np.std(flat_data)**4 - 3)
        }
        
        return stats
    
    def register_dataset_statistics(self, dataset_id: str, data: np.ndarray):
        """Register statistics for a dataset"""
        stats = self.compute_statistics(data)
        self.dataset_statistics[dataset_id] = stats
        
        # Save to disk
        os.makedirs(DATASET_STATISTICS_PATH, exist_ok=True)
        with open(os.path.join(DATASET_STATISTICS_PATH, "statistics.json"), "w") as f:
            json.dump(self.dataset_statistics, f, indent=2)
    
    def validate_data(self, dataset_id: str, data: np.ndarray,
                     threshold: float = 0.2) -> Dict[str, float]:
        """
        Validate data against registered statistics
        
        Args:
            dataset_id: Dataset identifier
            data: Data to validate
            threshold: Threshold for statistical deviation
            
        Returns:
            deviations: Dictionary of deviations from expected statistics
        """
        if dataset_id not in self.dataset_statistics:
            logger.warning(f"No registered statistics for dataset {dataset_id}")
            return None
        
        # Compute statistics for current data
        current_stats = self.compute_statistics(data)
        registered_stats = self.dataset_statistics[dataset_id]
        
        # Check for deviations
        deviations = {}
        for stat, value in current_stats.items():
            if stat in registered_stats:
                expected = registered_stats[stat]
                if expected != 0:
                    relative_deviation = abs(value - expected) / abs(expected)
                    if relative_deviation > threshold:
                        deviations[stat] = {
                            "expected": expected,
                            "actual": value,
                            "deviation": relative_deviation
                        }
        
        if deviations:
            logger.warning(f"Data validation failed for dataset {dataset_id}: {deviations}")
        
        return deviations if deviations else None
    
    def detect_outliers(self, data: np.ndarray, threshold: float = 3.0) -> np.ndarray:
        """Detect outliers in data using z-score"""
        # Flatten data
        flat_data = data.reshape(data.shape[0], -1)
        
        # Calculate z-scores for each sample
        mean = np.mean(flat_data, axis=0)
        std = np.std(flat_data, axis=0)
        
        # Avoid division by zero
        std = np.where(std == 0, 1e-10, std)
        
        z_scores = np.abs((flat_data - mean) / std)
        
        # Average z-score for each sample
        avg_z_scores = np.mean(z_scores, axis=1)
        
        # Identify outliers
        outliers = avg_z_scores > threshold
        
        return outliers
    
    def detect_poisoning(self, training_data: np.ndarray,
                        labels: np.ndarray,
                        contamination_ratio: float = 0.05) -> np.ndarray:
        """
        Detect potential poisoning in training data
        
        Args:
            training_data: Training data
            labels: Labels for training data
            contamination_ratio: Expected ratio of poisoned samples
            
        Returns:
            poisoned_indices: Indices of potentially poisoned samples
        """
        # Reshape data
        reshaped_data = training_data.reshape(training_data.shape[0], -1)
        
        # Train isolation forest
        detector = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=contamination_ratio,
            random_state=42
        )
        
        # Fit and predict
        predictions = detector.fit_predict(reshaped_data)
        
        # Isolation Forest returns -1 for anomalies and 1 for normal samples
        poisoned_indices = np.where(predictions == -1)[0]
        
        # Additional check: look for clusters of mislabeled data
        # This is a simplified approach - in practice, more sophisticated methods would be used
        for label in np.unique(labels):
            label_indices = np.where(labels == label)[0]
            label_data = reshaped_data[label_indices]
            
            if len(label_indices) > 10:  # Only check if we have enough samples
                # Check for outliers within this label
                label_detector = IsolationForest(contamination=contamination_ratio)
                label_predictions = label_detector.fit_predict(label_data)
                label_anomalies = np.where(label_predictions == -1)[0]
                
                # Add to poisoned indices
                poisoned_indices = np.union1d(poisoned_indices, label_indices[label_anomalies])
        
        return poisoned_indices


class AISecurityManager:
    """Main class for managing AI model security"""
    
    def __init__(self):
        """Initialize AI security manager"""
        # Create model registry
        self.model_registry = ModelRegistry()
        
        # Create adversarial protection
        self.adversarial_protection = AdversarialProtection(self.model_registry)
        
        # Create performance monitor
        self.performance_monitor = PerformanceMonitor(self.model_registry)
        
        # Create data validation
        self.data_validation = DataValidation()
        
        logger.info("AI Security Manager initialized")
    
    def secure_prediction(self, model_id: str, input_data: np.ndarray,
                         version: str = None) -> Tuple[np.ndarray, Dict]:
        """
        Make a secure prediction with adversarial detection
        
        Args:
            model_id: Model identifier
            input_data: Input data for prediction
            version: Model version (default: production version)
            
        Returns:
            prediction: Model prediction
            security_info: Security information about the prediction
        """
        security_info = {
            "adversarial_detected": False,
            "input_validated": True,
            "model_verified": True,
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            # Check for adversarial input
            is_adversarial = self.adversarial_protection.detect_adversarial_input(model_id, input_data)
            security_info["adversarial_detected"] = is_adversarial
            
            if is_adversarial:
                logger.warning(f"Adversarial input detected for model {model_id}")
                # Return empty prediction with warning
                return np.array([]), security_info
            
            # Load model
            model, metadata = self.model_registry.load_model(model_id, version)
            
            # Make prediction based on framework
            framework = metadata["framework"]
            if framework.lower() == "tensorflow":
                prediction = model.predict(input_data)
            elif framework.lower() == "pytorch":
                model.eval()
                with torch.no_grad():
                    tensor_input = torch.tensor(input_data, dtype=torch.float32)
                    prediction = model(tensor_input).numpy()
            else:
                # Default for scikit-learn and other frameworks
                prediction = model.predict(input_data)
            
            security_info["execution_time"] = time.time() - start_time
            return prediction, security_info
            
        except Exception as e:
            # Use the centralized error handler
            from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
            error_details = ErrorHandler.handle_exception(
                e,
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.ERROR,
                error_id=2050,
                context={
                    "operation": "secure_predict", 
                    "model_id": model_id,
                    "version": version
                }
            )
            
            logger.error(f"Error in secure prediction: {error_details['error_code']}")
            security_info["model_verified"] = False
            security_info["error_code"] = error_details["error_code"]
            security_info["error_message"] = error_details["message"]
            security_info["execution_time"] = time.time() - start_time
            return np.array([]), security_info
    
    def register_model_version(self, model, model_id: str, version: str,
                              framework: str, training_data: np.ndarray = None,
                              encrypt: bool = True) -> str:
        """
        Register a new model version with security features
        
        Args:
            model: Model object
            model_id: Model identifier
            version: Version string
            framework: Framework used
            training_data: Training data used (for anomaly detection)
            encrypt: Whether to encrypt the model
            
        Returns:
            model_hash: Hash of the registered model
        """
        # Register model in registry
        model_hash = self.model_registry.register_model(
            model, model_id, version, framework, encrypt
        )
        
        # If training data is provided, train anomaly detector
        if training_data is not None:
            self.adversarial_protection.train_anomaly_detector(model_id, training_data)
            
            # Register dataset statistics
            self.data_validation.register_dataset_statistics(f"{model_id}_{version}", training_data)
        
        logger.info(f"Model {model_id} version {version} registered with security features")
        return model_hash
    
    def validate_model_performance(self, model_id: str, version: str,
                                 test_data: np.ndarray, test_labels: np.ndarray,
                                 metrics: List[str] = None) -> Dict[str, float]:
        """
        Validate model performance and check for degradation
        
        Args:
            model_id: Model identifier
            version: Model version
            test_data: Test data
            test_labels: Test labels
            metrics: List of metrics to compute (default: accuracy, precision, recall, f1)
            
        Returns:
            results: Dictionary of performance metrics
        """
        if metrics is None:
            metrics = ["accuracy", "precision", "recall", "f1"]
        
        try:
            # Load model
            model, metadata = self.model_registry.load_model(model_id, version)
            framework = metadata["framework"]
            
            # Make predictions
            if framework.lower() == "tensorflow":
                predictions = model.predict(test_data)
                # Convert to class indices for classification metrics
                if len(predictions.shape) > 1 and predictions.shape[1] > 1:
                    predictions = np.argmax(predictions, axis=1)
                    test_labels = np.argmax(test_labels, axis=1) if len(test_labels.shape) > 1 else test_labels
            elif framework.lower() == "pytorch":
                model.eval()
                with torch.no_grad():
                    tensor_input = torch.tensor(test_data, dtype=torch.float32)
                    predictions = model(tensor_input).numpy()
                    # Convert to class indices for classification metrics
                    if len(predictions.shape) > 1 and predictions.shape[1] > 1:
                        predictions = np.argmax(predictions, axis=1)
                        test_labels = np.argmax(test_labels, axis=1) if len(test_labels.shape) > 1 else test_labels
            else:
                # Default for scikit-learn and other frameworks
                predictions = model.predict(test_data)
            
            # Compute metrics
            results = {}
            if "accuracy" in metrics:
                results["accuracy"] = accuracy_score(test_labels, predictions)
            if "precision" in metrics:
                results["precision"] = precision_score(test_labels, predictions, average='weighted')
            if "recall" in metrics:
                results["recall"] = recall_score(test_labels, predictions, average='weighted')
            if "f1" in metrics:
                results["f1"] = f1_score(test_labels, predictions, average='weighted')
            
            # Record performance
            degradation = self.performance_monitor.record_performance(model_id, version, results)
            
            # Add degradation info to results if detected
            if degradation:
                results["degradation"] = degradation
                logger.warning(f"Performance degradation detected for model {model_id} version {version}")
            
            return results
            
        except Exception as e:
            # Use the centralized error handler
            from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
            error_details = ErrorHandler.handle_exception(
                e,
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.ERROR,
                error_id=2075,
                context={
                    "operation": "validate_model_performance", 
                    "model_id": model_id,
                    "version": version
                }
            )
            
            logger.error(f"Error validating model performance: {error_details['error_code']}")
            return {
                "error_code": error_details["error_code"],
                "error_message": error_details["message"],
                "success": False
            }
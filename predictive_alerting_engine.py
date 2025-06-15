#!/usr/bin/env python3
"""
Predictive Alerting Engine
Predicts potential issues before they occur and generates proactive alerts
"""

import os
import sys
import time
import json
import yaml
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from collections import defaultdict
import joblib
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("predictive_alerting.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("predictive_alerting_engine")

# Try to import ML libraries
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from statsmodels.tsa.arima.model import ARIMA
    ML_LIBRARIES_AVAILABLE = True
except ImportError:
    logger.warning("ML libraries not available. Limited functionality.")
    ML_LIBRARIES_AVAILABLE = False

# Try to import deep learning libraries
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    DL_LIBRARIES_AVAILABLE = True
except ImportError:
    logger.warning("Deep learning libraries not available. LSTM models disabled.")
    DL_LIBRARIES_AVAILABLE = False

class PredictiveAlertingEngine:
    """
    Predicts potential issues before they occur and generates proactive alerts
    - Uses multiple prediction models (LSTM, ARIMA, Isolation Forest)
    - Monitors various metrics (price, volume, gas, etc.)
    - Generates alerts based on predictions
    - Provides confidence levels for predictions
    """
    
    def __init__(self, config_path="sentinel_config.yaml"):
        """
        Initialize the Predictive Alerting Engine
        
        Args:
            config_path: Path to the sentinel configuration file
        """
        self.config_path = config_path
        self.models = {}
        self.data_store = {}
        self.last_prediction_time = {}
        self.last_training_time = {}
        
        # Load configuration
        self.load_config()
        
        # Initialize prediction models
        self._init_prediction_models()
        
        logger.info("Predictive Alerting Engine initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Extract predictive alerting configuration
            self.config = config.get("advanced_features", {}).get("predictive_alerting", {})
            
            # Set defaults if not specified
            if not self.config:
                self.config = {
                    "enabled": True,
                    "models": [
                        {
                            "name": "price_prediction",
                            "type": "lstm",
                            "confidence_threshold": 0.85,
                            "lookback_window": "24h",
                            "prediction_horizon": "1h"
                        },
                        {
                            "name": "volume_anomaly",
                            "type": "isolation_forest",
                            "confidence_threshold": 0.9,
                            "lookback_window": "12h",
                            "contamination": 0.05
                        },
                        {
                            "name": "gas_spike",
                            "type": "arima",
                            "confidence_threshold": 0.8,
                            "lookback_window": "6h",
                            "prediction_horizon": "30m"
                        }
                    ],
                    "alert_triggers": [
                        {
                            "name": "price_drop_prediction",
                            "model": "price_prediction",
                            "condition": "predicted_change < -0.05",
                            "severity": "medium"
                        },
                        {
                            "name": "volume_spike_prediction",
                            "model": "volume_anomaly",
                            "condition": "anomaly_score > 0.8",
                            "severity": "high"
                        },
                        {
                            "name": "gas_spike_prediction",
                            "model": "gas_spike",
                            "condition": "predicted_value > 200",
                            "severity": "medium"
                        }
                    ]
                }
                
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
    
    def _init_prediction_models(self):
        """Initialize prediction models based on configuration"""
        if not self.config.get("enabled", True):
            logger.info("Predictive alerting is disabled")
            return
            
        if not ML_LIBRARIES_AVAILABLE:
            logger.warning("ML libraries not available. Cannot initialize prediction models.")
            return
            
        for model_config in self.config.get("models", []):
            model_name = model_config.get("name")
            model_type = model_config.get("type")
            
            if model_type == "lstm" and not DL_LIBRARIES_AVAILABLE:
                logger.warning(f"Deep learning libraries not available. Skipping LSTM model: {model_name}")
                continue
                
            try:
                if model_type == "lstm":
                    self._init_lstm_model(model_name, model_config)
                elif model_type == "arima":
                    self._init_arima_model(model_name, model_config)
                elif model_type == "isolation_forest":
                    self._init_isolation_forest_model(model_name, model_config)
                else:
                    logger.warning(f"Unknown model type: {model_type}")
            except Exception as e:
                logger.error(f"Error initializing model {model_name}: {e}")
    
    def _init_lstm_model(self, model_name: str, model_config: Dict[str, Any]):
        """
        Initialize LSTM model
        
        Args:
            model_name: Name of the model
            model_config: Model configuration
        """
        # Check if model file exists
        model_file = f"models/{model_name}.h5"
        
        if os.path.exists(model_file):
            try:
                # Load existing model
                lstm_model = load_model(model_file)
                logger.info(f"Loaded existing LSTM model: {model_name}")
            except Exception as e:
                logger.error(f"Error loading LSTM model {model_name}: {e}")
                lstm_model = self._create_lstm_model(model_config)
        else:
            # Create new model
            lstm_model = self._create_lstm_model(model_config)
            
        # Create data store for this model
        self.data_store[model_name] = []
        
        # Store model
        self.models[model_name] = {
            "type": "lstm",
            "model": lstm_model,
            "config": model_config,
            "scaler": StandardScaler(),
            "trained": False
        }
        
        logger.info(f"Initialized LSTM model: {model_name}")
    
    def _create_lstm_model(self, model_config: Dict[str, Any]) -> Sequential:
        """
        Create a new LSTM model
        
        Args:
            model_config: Model configuration
            
        Returns:
            Sequential: LSTM model
        """
        # Parse lookback window
        lookback_window = self._parse_time_window(model_config.get("lookback_window", "24h"))
        
        # Create model
        model = Sequential()
        
        # Add LSTM layers
        model.add(LSTM(50, return_sequences=True, input_shape=(lookback_window, 1)))
        model.add(Dropout(0.2))
        model.add(LSTM(50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(1))
        
        # Compile model
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        return model
    
    def _init_arima_model(self, model_name: str, model_config: Dict[str, Any]):
        """
        Initialize ARIMA model
        
        Args:
            model_name: Name of the model
            model_config: Model configuration
        """
        # Create data store for this model
        self.data_store[model_name] = []
        
        # Store model configuration
        self.models[model_name] = {
            "type": "arima",
            "model": None,  # Will be created when needed
            "config": model_config,
            "trained": False
        }
        
        logger.info(f"Initialized ARIMA model: {model_name}")
    
    def _init_isolation_forest_model(self, model_name: str, model_config: Dict[str, Any]):
        """
        Initialize Isolation Forest model
        
        Args:
            model_name: Name of the model
            model_config: Model configuration
        """
        # Create model
        contamination = model_config.get("contamination", 0.05)
        n_estimators = model_config.get("n_estimators", 100)
        
        isolation_forest = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42
        )
        
        # Create data store for this model
        self.data_store[model_name] = []
        
        # Store model
        self.models[model_name] = {
            "type": "isolation_forest",
            "model": isolation_forest,
            "config": model_config,
            "scaler": StandardScaler(),
            "trained": False
        }
        
        logger.info(f"Initialized Isolation Forest model: {model_name}")
    
    def _parse_time_window(self, window_str: str) -> int:
        """
        Parse time window string to seconds
        
        Args:
            window_str: Time window string (e.g., "24h", "30m", "1d")
            
        Returns:
            int: Time window in seconds
        """
        if not window_str:
            return 86400  # Default to 24 hours
            
        unit = window_str[-1].lower()
        value = int(window_str[:-1])
        
        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        else:
            logger.warning(f"Unknown time unit: {unit}, defaulting to seconds")
            return value
    
    def add_data_point(self, model_name: str, data_point: Dict[str, Any]):
        """
        Add a data point for a model
        
        Args:
            model_name: Name of the model
            data_point: Data point dictionary
        """
        if not self.config.get("enabled", True):
            return
            
        if model_name not in self.models:
            logger.warning(f"Unknown model: {model_name}")
            return
            
        if model_name not in self.data_store:
            self.data_store[model_name] = []
            
        # Add timestamp if not present
        if "timestamp" not in data_point:
            data_point["timestamp"] = time.time()
            
        # Add to data store
        self.data_store[model_name].append(data_point)
        
        # Trim data store if needed
        model_config = self.models[model_name]["config"]
        lookback_window = self._parse_time_window(model_config.get("lookback_window", "24h"))
        
        # Keep only data points within lookback window
        current_time = time.time()
        self.data_store[model_name] = [
            dp for dp in self.data_store[model_name]
            if current_time - dp.get("timestamp", 0) <= lookback_window
        ]
        
        # Check if we should train the model
        self._check_model_training(model_name)
        
        # Check if we should make a prediction
        self._check_prediction(model_name)
    
    def _check_model_training(self, model_name: str):
        """
        Check if a model should be trained
        
        Args:
            model_name: Name of the model
        """
        if model_name not in self.models:
            return
            
        model_info = self.models[model_name]
        model_config = model_info["config"]
        
        # Get training interval
        training_interval = self._parse_time_window(model_config.get("training_interval", "1d"))
        
        # Check if enough time has passed since last training
        current_time = time.time()
        last_training = self.last_training_time.get(model_name, 0)
        
        if current_time - last_training >= training_interval:
            # Check if we have enough data
            if len(self.data_store.get(model_name, [])) >= 10:
                self._train_model(model_name)
    
    def _train_model(self, model_name: str):
        """
        Train a model
        
        Args:
            model_name: Name of the model
        """
        if model_name not in self.models:
            return
            
        model_info = self.models[model_name]
        model_type = model_info["type"]
        
        try:
            if model_type == "lstm":
                self._train_lstm_model(model_name)
            elif model_type == "arima":
                self._train_arima_model(model_name)
            elif model_type == "isolation_forest":
                self._train_isolation_forest_model(model_name)
                
            # Update last training time
            self.last_training_time[model_name] = time.time()
            
            # Mark model as trained
            model_info["trained"] = True
            
            logger.info(f"Trained model: {model_name}")
        except Exception as e:
            logger.error(f"Error training model {model_name}: {e}")
    
    def _train_lstm_model(self, model_name: str):
        """
        Train LSTM model
        
        Args:
            model_name: Name of the model
        """
        if not DL_LIBRARIES_AVAILABLE:
            logger.warning("Deep learning libraries not available. Cannot train LSTM model.")
            return
            
        model_info = self.models[model_name]
        model = model_info["model"]
        scaler = model_info["scaler"]
        model_config = model_info["config"]
        
        # Get data
        data = self.data_store.get(model_name, [])
        
        if not data:
            logger.warning(f"No data available for model: {model_name}")
            return
            
        # Extract values
        values = [dp.get("value", 0) for dp in data]
        
        # Scale data
        values = np.array(values).reshape(-1, 1)
        scaled_values = scaler.fit_transform(values)
        
        # Create sequences
        lookback_window = self._parse_time_window(model_config.get("lookback_window", "24h"))
        lookback_steps = min(len(scaled_values) - 1, 24)  # Use at most 24 steps
        
        X, y = [], []
        
        for i in range(len(scaled_values) - lookback_steps):
            X.append(scaled_values[i:i+lookback_steps])
            y.append(scaled_values[i+lookback_steps])
            
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        model.fit(X, y, epochs=50, batch_size=32, verbose=0)
        
        # Save model
        os.makedirs("models", exist_ok=True)
        model.save(f"models/{model_name}.h5")
    
    def _train_arima_model(self, model_name: str):
        """
        Train ARIMA model
        
        Args:
            model_name: Name of the model
        """
        model_info = self.models[model_name]
        
        # Get data
        data = self.data_store.get(model_name, [])
        
        if not data:
            logger.warning(f"No data available for model: {model_name}")
            return
            
        # Extract values
        values = [dp.get("value", 0) for dp in data]
        
        # Create time series
        ts = pd.Series(values)
        
        # Train ARIMA model
        model = ARIMA(ts, order=(5, 1, 0))
        model_fit = model.fit()
        
        # Store model
        model_info["model"] = model_fit
    
    def _train_isolation_forest_model(self, model_name: str):
        """
        Train Isolation Forest model
        
        Args:
            model_name: Name of the model
        """
        model_info = self.models[model_name]
        model = model_info["model"]
        scaler = model_info["scaler"]
        
        # Get data
        data = self.data_store.get(model_name, [])
        
        if not data:
            logger.warning(f"No data available for model: {model_name}")
            return
            
        # Extract features
        features = []
        
        for dp in data:
            if "features" in dp and isinstance(dp["features"], dict):
                feature_values = list(dp["features"].values())
                features.append(feature_values)
                
        if not features:
            logger.warning(f"No features available for model: {model_name}")
            return
            
        # Scale features
        features = np.array(features)
        scaled_features = scaler.fit_transform(features)
        
        # Train model
        model.fit(scaled_features)
        
        # Save model
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, f"models/{model_name}.joblib")
    
    def _check_prediction(self, model_name: str):
        """
        Check if a prediction should be made
        
        Args:
            model_name: Name of the model
        """
        if model_name not in self.models:
            return
            
        model_info = self.models[model_name]
        
        # Skip if model is not trained
        if not model_info["trained"]:
            return
            
        model_config = model_info["config"]
        
        # Get prediction interval
        prediction_interval = self._parse_time_window(model_config.get("prediction_interval", "5m"))
        
        # Check if enough time has passed since last prediction
        current_time = time.time()
        last_prediction = self.last_prediction_time.get(model_name, 0)
        
        if current_time - last_prediction >= prediction_interval:
            self._make_prediction(model_name)
    
    def _make_prediction(self, model_name: str):
        """
        Make a prediction using a model
        
        Args:
            model_name: Name of the model
        """
        if model_name not in self.models:
            return
            
        model_info = self.models[model_name]
        model_type = model_info["type"]
        
        try:
            if model_type == "lstm":
                prediction = self._predict_lstm(model_name)
            elif model_type == "arima":
                prediction = self._predict_arima(model_name)
            elif model_type == "isolation_forest":
                prediction = self._predict_isolation_forest(model_name)
            else:
                logger.warning(f"Unknown model type: {model_type}")
                return
                
            # Update last prediction time
            self.last_prediction_time[model_name] = time.time()
            
            # Check if prediction should trigger an alert
            if prediction:
                self._check_alert_triggers(model_name, prediction)
                
            return prediction
        except Exception as e:
            logger.error(f"Error making prediction with model {model_name}: {e}")
            return None
    
    def _predict_lstm(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Make a prediction using LSTM model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Optional[Dict[str, Any]]: Prediction result or None if prediction fails
        """
        if not DL_LIBRARIES_AVAILABLE:
            logger.warning("Deep learning libraries not available. Cannot make LSTM prediction.")
            return None
            
        model_info = self.models[model_name]
        model = model_info["model"]
        scaler = model_info["scaler"]
        model_config = model_info["config"]
        
        # Get data
        data = self.data_store.get(model_name, [])
        
        if not data:
            logger.warning(f"No data available for model: {model_name}")
            return None
            
        # Extract values
        values = [dp.get("value", 0) for dp in data]
        
        # Scale data
        values = np.array(values).reshape(-1, 1)
        scaled_values = scaler.fit_transform(values)
        
        # Create input sequence
        lookback_steps = min(len(scaled_values), 24)  # Use at most 24 steps
        input_seq = scaled_values[-lookback_steps:].reshape(1, lookback_steps, 1)
        
        # Make prediction
        scaled_prediction = model.predict(input_seq, verbose=0)[0][0]
        
        # Inverse transform
        prediction = scaler.inverse_transform([[scaled_prediction]])[0][0]
        
        # Calculate confidence
        confidence = 0.9  # Default confidence
        
        # Calculate change
        current_value = values[-1][0]
        predicted_change = (prediction - current_value) / current_value
        
        # Create prediction result
        prediction_horizon = model_config.get("prediction_horizon", "1h")
        result = {
            "model": model_name,
            "timestamp": time.time(),
            "current_value": current_value,
            "predicted_value": prediction,
            "predicted_change": predicted_change,
            "confidence": confidence,
            "horizon": prediction_horizon
        }
        
        logger.info(f"LSTM prediction for {model_name}: {prediction} (change: {predicted_change:.2%}, confidence: {confidence:.2f})")
        
        return result
    
    def _predict_arima(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Make a prediction using ARIMA model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Optional[Dict[str, Any]]: Prediction result or None if prediction fails
        """
        model_info = self.models[model_name]
        model_fit = model_info["model"]
        model_config = model_info["config"]
        
        if not model_fit:
            logger.warning(f"ARIMA model not trained: {model_name}")
            return None
            
        # Get data
        data = self.data_store.get(model_name, [])
        
        if not data:
            logger.warning(f"No data available for model: {model_name}")
            return None
            
        # Extract values
        values = [dp.get("value", 0) for dp in data]
        
        # Get prediction horizon
        prediction_horizon_str = model_config.get("prediction_horizon", "30m")
        prediction_steps = 1  # Default to 1 step ahead
        
        # Make prediction
        forecast = model_fit.forecast(steps=prediction_steps)
        prediction = forecast[0]
        
        # Calculate confidence
        confidence = 0.8  # Default confidence
        
        # Calculate change
        current_value = values[-1]
        predicted_change = (prediction - current_value) / current_value
        
        # Create prediction result
        result = {
            "model": model_name,
            "timestamp": time.time(),
            "current_value": current_value,
            "predicted_value": prediction,
            "predicted_change": predicted_change,
            "confidence": confidence,
            "horizon": prediction_horizon_str
        }
        
        logger.info(f"ARIMA prediction for {model_name}: {prediction} (change: {predicted_change:.2%}, confidence: {confidence:.2f})")
        
        return result
    
    def _predict_isolation_forest(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Make a prediction using Isolation Forest model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Optional[Dict[str, Any]]: Prediction result or None if prediction fails
        """
        model_info = self.models[model_name]
        model = model_info["model"]
        scaler = model_info["scaler"]
        
        # Get data
        data = self.data_store.get(model_name, [])
        
        if not data:
            logger.warning(f"No data available for model: {model_name}")
            return None
            
        # Extract features from most recent data point
        latest_dp = data[-1]
        
        if "features" not in latest_dp or not isinstance(latest_dp["features"], dict):
            logger.warning(f"No features in latest data point for model: {model_name}")
            return None
            
        feature_values = list(latest_dp["features"].values())
        
        # Scale features
        scaled_features = scaler.transform([feature_values])
        
        # Make prediction
        anomaly_score = model.decision_function(scaled_features)[0]
        anomaly_score = -anomaly_score  # Convert to positive for anomalies
        
        # Calculate confidence
        confidence = min(1.0, max(0.0, anomaly_score))
        
        # Create prediction result
        result = {
            "model": model_name,
            "timestamp": time.time(),
            "anomaly_score": anomaly_score,
            "confidence": confidence,
            "features": latest_dp["features"]
        }
        
        logger.info(f"Isolation Forest prediction for {model_name}: anomaly_score={anomaly_score:.2f}, confidence={confidence:.2f}")
        
        return result
    
    def _check_alert_triggers(self, model_name: str, prediction: Dict[str, Any]):
        """
        Check if a prediction should trigger an alert
        
        Args:
            model_name: Name of the model
            prediction: Prediction result
        """
        # Get alert triggers for this model
        triggers = [
            trigger for trigger in self.config.get("alert_triggers", [])
            if trigger.get("model") == model_name
        ]
        
        for trigger in triggers:
            # Get trigger condition
            condition = trigger.get("condition", "")
            
            if not condition:
                continue
                
            # Evaluate condition
            try:
                # Create local variables from prediction
                locals_dict = dict(prediction)
                
                # Evaluate condition
                result = eval(condition, {"__builtins__": {}}, locals_dict)
                
                if result:
                    # Condition met, generate alert
                    self._generate_alert(trigger, prediction)
            except Exception as e:
                logger.error(f"Error evaluating condition '{condition}': {e}")
    
    def _generate_alert(self, trigger: Dict[str, Any], prediction: Dict[str, Any]):
        """
        Generate an alert based on a prediction
        
        Args:
            trigger: Alert trigger configuration
            prediction: Prediction result
        """
        # Get alert details
        trigger_name = trigger.get("name", "unknown")
        model_name = trigger.get("model", "unknown")
        severity = trigger.get("severity", "medium")
        
        # Create alert
        alert = {
            "alert_id": f"predictive_{int(time.time())}_{model_name}",
            "sentinel": "predictive_sentinel",
            "severity": severity,
            "type": "prediction",
            "title": f"Predictive Alert: {trigger_name}",
            "message": self._format_alert_message(trigger, prediction),
            "timestamp": time.time(),
            "data": {
                "prediction": prediction,
                "trigger": trigger_name,
                "confidence": prediction.get("confidence", 0)
            }
        }
        
        # Emit alert
        self._emit_alert(alert)
        
        logger.info(f"Generated predictive alert: {alert['title']}")
    
    def _format_alert_message(self, trigger: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """
        Format alert message based on prediction
        
        Args:
            trigger: Alert trigger configuration
            prediction: Prediction result
            
        Returns:
            str: Formatted alert message
        """
        trigger_name = trigger.get("name", "unknown")
        model_name = trigger.get("model", "unknown")
        
        if "predicted_value" in prediction:
            current_value = prediction.get("current_value", 0)
            predicted_value = prediction.get("predicted_value", 0)
            predicted_change = prediction.get("predicted_change", 0)
            horizon = prediction.get("horizon", "unknown")
            confidence = prediction.get("confidence", 0)
            
            return (
                f"Predicted {model_name} value: {predicted_value:.2f} "
                f"(change: {predicted_change:.2%} from current {current_value:.2f}) "
                f"within {horizon} with {confidence:.0%} confidence"
            )
        elif "anomaly_score" in prediction:
            anomaly_score = prediction.get("anomaly_score", 0)
            confidence = prediction.get("confidence", 0)
            
            return (
                f"Anomaly detected in {model_name} with score {anomaly_score:.2f} "
                f"and {confidence:.0%} confidence"
            )
        else:
            return f"Predictive alert triggered: {trigger_name}"
    
    def _emit_alert(self, alert: Dict[str, Any]):
        """
        Emit an alert to the alert routing system
        
        Args:
            alert: Alert data
        """
        # In a real implementation, this would send the alert to the alert routing engine
        # For this example, we'll just log it
        logger.warning(f"PREDICTIVE ALERT: {alert['severity']} - {alert['title']} - {alert['message']}")
        
        # Try to import alert routing engine
        try:
            from alert_routing_engine import AlertRoutingEngine
            
            # Initialize engine
            routing_engine = AlertRoutingEngine()
            
            # Route alert
            routing_engine.route_alert(alert)
            
            logger.info("Alert sent to routing engine")
        except ImportError:
            logger.warning("Alert routing engine not available. Alert not routed.")
    
    def add_price_data(self, asset: str, price: float, volume: float = None):
        """
        Add price data for prediction
        
        Args:
            asset: Asset name
            price: Asset price
            volume: Trading volume (optional)
        """
        # Add to price prediction model
        if "price_prediction" in self.models:
            data_point = {
                "timestamp": time.time(),
                "value": price,
                "asset": asset
            }
            
            self.add_data_point("price_prediction", data_point)
            
        # Add to volume anomaly model if volume provided
        if volume is not None and "volume_anomaly" in self.models:
            data_point = {
                "timestamp": time.time(),
                "value": volume,
                "asset": asset,
                "features": {
                    "volume": volume,
                    "price": price,
                    "volume_price_ratio": volume / price if price > 0 else 0
                }
            }
            
            self.add_data_point("volume_anomaly", data_point)
    
    def add_gas_data(self, gas_price: float, gas_used: float = None, block_number: int = None):
        """
        Add gas data for prediction
        
        Args:
            gas_price: Gas price in gwei
            gas_used: Gas used (optional)
            block_number: Block number (optional)
        """
        if "gas_spike" in self.models:
            data_point = {
                "timestamp": time.time(),
                "value": gas_price,
                "block_number": block_number
            }
            
            if gas_used is not None:
                data_point["gas_used"] = gas_used
                
            self.add_data_point("gas_spike", data_point)
    
    def shutdown(self):
        """Shutdown the predictive alerting engine"""
        logger.info("Shutting down Predictive Alerting Engine")
        
        # Save models
        for model_name, model_info in self.models.items():
            if model_info["trained"]:
                try:
                    if model_info["type"] == "lstm" and DL_LIBRARIES_AVAILABLE:
                        os.makedirs("models", exist_ok=True)
                        model_info["model"].save(f"models/{model_name}.h5")
                    elif model_info["type"] == "isolation_forest":
                        os.makedirs("models", exist_ok=True)
                        joblib.dump(model_info["model"], f"models/{model_name}.joblib")
                except Exception as e:
                    logger.error(f"Error saving model {model_name}: {e}")
        
        # Clean up resources
        self.models = {}
        self.data_store = {}
        
        logger.info("Predictive Alerting Engine shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the predictive alerting engine
    
    # Initialize engine
    engine = PredictiveAlertingEngine(config_path="sentinel_config.yaml")
    
    # Simulate price data
    for i in range(100):
        # Generate synthetic price data with some noise
        price = 2000 + 100 * np.sin(i / 10) + np.random.normal(0, 20)
        volume = 1000 + 500 * np.sin(i / 5) + np.random.normal(0, 100)
        
        # Add data
        engine.add_price_data("ETH", price, volume)
        
        # Simulate gas data
        gas_price = 50 + 10 * np.sin(i / 20) + np.random.normal(0, 5)
        engine.add_gas_data(gas_price)
        
        # Sleep to simulate time passing
        time.sleep(0.1)
    
    # Make predictions
    price_prediction = engine._make_prediction("price_prediction")
    if price_prediction:
        print(f"Price prediction: {price_prediction['predicted_value']:.2f} (change: {price_prediction['predicted_change']:.2%})")
        
    gas_prediction = engine._make_prediction("gas_spike")
    if gas_prediction:
        print(f"Gas prediction: {gas_prediction['predicted_value']:.2f}")
        
    volume_prediction = engine._make_prediction("volume_anomaly")
    if volume_prediction:
        print(f"Volume anomaly score: {volume_prediction['anomaly_score']:.2f}")
    
    # Shutdown
    engine.shutdown()
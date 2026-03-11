import pytest
import pandas as pd
from app import model

def test_model_prediction():
    
    # ensure we pass a 2‑D shape since XGBoost expects (n_samples, n_features)
    prediction = model.predict([[1.0, 1.0, 10, 12]])[0]
    assert 0 <= prediction <= 100
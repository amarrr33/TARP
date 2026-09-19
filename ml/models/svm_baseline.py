import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

class SVMBaseline:
    """
    Candidate 1: Classical Acoustic Baseline.
    RBF Support Vector Machine on statistical MFCC features (240 dimensions).
    """
    def __init__(self, C=1.0, kernel='rbf', gamma='scale'):
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('svm', SVC(C=C, kernel=kernel, gamma=gamma, probability=True, random_state=42))
        ])
        self.classes_ = None

    def fit(self, X, y):
        self.pipeline.fit(X, y)
        self.classes_ = self.pipeline.named_steps['svm'].classes_
        return self

    def predict(self, X):
        return self.pipeline.predict(X)

    def predict_proba(self, X):
        return self.pipeline.predict_proba(X)

    def save(self, filepath):
        joblib.dump(self.pipeline, filepath)

    def load(self, filepath):
        self.pipeline = joblib.load(filepath)
        self.classes_ = self.pipeline.named_steps['svm'].classes_
        return self

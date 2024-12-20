import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd
import torch
import shap
import lime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import StandardScaler

class AdvancedModelInterpreter:
    """
    Comprehensive machine learning model interpretability toolkit
    Supports multiple interpretation techniques for various model types
    """
    
    def __init__(self, 
                 model: Any, 
                 feature_names: Optional[List[str]] = None,
                 output_dir: str = 'model_explanations'):
        """
        Initialize model interpreter
        
        :param model: Machine learning model to interpret
        :param feature_names: Optional list of feature names
        :param output_dir: Directory to save interpretation results
        """
        self.model = model
        self.feature_names = feature_names or [f'feature_{i}' for i in range(self._get_feature_count())]
        
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Output directory
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _get_feature_count(self) -> int:
        """
        Determine number of features in the model
        
        :return: Number of features
        """
        if hasattr(self.model, 'feature_names_in_'):
            return len(self.model.feature_names_in_)
        elif hasattr(self.model, 'n_features_in_'):
            return self.model.n_features_in_
        else:
            return 0

    def shap_explanation(self, 
                         X: Union[np.ndarray, pd.DataFrame], 
                         background_data: Optional[Union[np.ndarray, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        Generate SHAP (SHapley Additive exPlanations) model interpretations
        
        :param X: Input data for explanation
        :param background_data: Optional background dataset for baseline
        :return: SHAP explanation results
        """
        try:
            # Prepare background data
            if background_data is None:
                background_data = X[:min(100, len(X))]
            
            # Determine explainer type based on model
            if isinstance(self.model, torch.nn.Module):
                explainer = shap.DeepExplainer(self.model, background_data)
            else:
                explainer = shap.Explainer(self.model, background_data)
            
            # Compute SHAP values
            shap_values = explainer.shap_values(X)
            
            # Visualization
            plt.figure(figsize=(10, 6))
            shap.summary_plot(shap_values, X, feature_names=self.feature_names, show=False)
            plt.title('SHAP Feature Importance')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'shap_summary.png'))
            plt.close()
            
            return {
                'shap_values': shap_values,
                'summary_plot_path': os.path.join(self.output_dir, 'shap_summary.png')
            }
        
        except Exception as e:
            self.logger.error(f"SHAP explanation error: {e}")
            return {}

    def lime_explanation(self, 
                         X: Union[np.ndarray, pd.DataFrame], 
                         num_features: int = 10) -> Dict[str, Any]:
        """
        Generate LIME (Local Interpretable Model-agnostic Explanations)
        
        :param X: Input data for explanation
        :param num_features: Number of top features to explain
        :return: LIME explanation results
        """
        try:
            # Prepare data
            if isinstance(X, pd.DataFrame):
                X_array = X.values
            else:
                X_array = X
            
            # Determine prediction function
            if hasattr(self.model, 'predict_proba'):
                predict_fn = self.model.predict_proba
            elif hasattr(self.model, 'predict'):
                predict_fn = self.model.predict
            else:
                raise ValueError("Model does not have prediction method")
            
            # LIME explainer
            explainer = lime.lime_tabular.LimeTabularExplainer(
                X_array, 
                feature_names=self.feature_names,
                class_names=['Class 0', 'Class 1']  # Adjust based on your model
            )
            
            # Explanation for first sample
            explanation = explainer.explain_instance(
                X_array[0], 
                predict_fn, 
                num_features=num_features
            )
            
            # Save explanation plot
            plt.figure(figsize=(10, 6))
            explanation.as_pyplot_figure()
            plt.title('LIME Local Explanation')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'lime_explanation.png'))
            plt.close()
            
            return {
                'explanation': explanation,
                'plot_path': os.path.join(self.output_dir, 'lime_explanation.png')
            }
        
        except Exception as e:
            self.logger.error(f"LIME explanation error: {e}")
            return {}

    def permutation_importance_analysis(self, 
                                        X: Union[np.ndarray, pd.DataFrame], 
                                        y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """
        Compute feature importance via permutation
        
        :param X: Input features
        :param y: Target variable
        :return: Permutation importance results
        """
        try:
            # Compute permutation importance
            result = permutation_importance(
                self.model, 
                X, 
                y, 
                n_repeats=10,
                random_state=42
            )
            
            # Create importance plot
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': result.importances_mean,
                'std': result.importances_std
            }).sort_values('importance', ascending=False)
            
            plt.figure(figsize=(10, 6))
            sns.barplot(x='importance', y='feature', data=importance_df, 
                        xerr=importance_df['std'], capsize=0.3)
            plt.title('Feature Importance via Permutation')
            plt.xlabel('Mean Decrease in Performance')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'permutation_importance.png'))
            plt.close()
            
            return {
                'importance_df': importance_df,
                'plot_path': os.path.join(self.output_dir, 'permutation_importance.png')
            }
        
        except Exception as e:
            self.logger.error(f"Permutation importance error: {e}")
            return {}

    def generate_comprehensive_report(self, 
                                      X: Union[np.ndarray, pd.DataFrame], 
                                      y: Optional[Union[np.ndarray, pd.Series]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive model interpretation report
        
        :param X: Input features
        :param y: Optional target variable
        :return: Comprehensive interpretation report
        """
        report = {
            'shap_explanation': self.shap_explanation(X),
            'lime_explanation': self.lime_explanation(X)
        }
        
        if y is not None:
            report['permutation_importance'] = self.permutation_importance_analysis(X, y)
        
        # Save report as JSON
        report_path = os.path.join(self.output_dir, 'model_interpretation_report.json')
        with open(report_path, 'w') as f:
            json.dump({k: str(v) for k, v in report.items()}, f, indent=2)
        
        report['report_path'] = report_path
        return report

def create_model_interpreter(
    model: Any, 
    feature_names: Optional[List[str]] = None,
    output_dir: str = 'model_explanations'
) -> AdvancedModelInterpreter:
    """
    Factory method to create model interpreter
    
    :param model: Machine learning model to interpret
    :param feature_names: Optional list of feature names
    :param output_dir: Directory to save interpretation results
    :return: Configured model interpreter
    """
    return AdvancedModelInterpreter(
        model, 
        feature_names, 
        output_dir
    )

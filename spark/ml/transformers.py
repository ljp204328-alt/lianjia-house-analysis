"""
自定义Transformer类
用于Pipeline训练和预测
"""
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelEncoder
import pandas as pd


class LabelEncodeTransformer(BaseEstimator, TransformerMixin):
    """Label编码转换器"""
    def __init__(self):
        self.encoders_ = {}
    
    def fit(self, X, y=None):
        for col in X.columns:
            le = LabelEncoder()
            le.fit(X[col].astype(str))
            self.encoders_[col] = le
        return self
    
    def transform(self, X):
        X_copy = X.copy()
        for col in X_copy.columns:
            le = self.encoders_[col]
            # 处理未见过的类别
            X_copy[col] = X_copy[col].astype(str).apply(
                lambda x: le.transform([x])[0] if x in le.classes_ else 0
            )
        return X_copy
    
    def get_encoder_classes(self):
        """获取编码器类别信息"""
        return {col: le.classes_.tolist() for col, le in self.encoders_.items()}


class TargetEncodeTransformer(BaseEstimator, TransformerMixin):
    """目标编码转换器"""
    def __init__(self):
        self.maps_ = {}
        self.global_mean_ = 0
    
    def fit(self, X, y):
        self.global_mean_ = y.mean()
        for col in X.columns:
            # 手动计算每个类别的目标均值
            col_map = {}
            for val in X[col].unique():
                mask = X[col] == val
                col_map[val] = y[mask].mean()
            self.maps_[col] = col_map
        return self
    
    def transform(self, X):
        X_copy = X.copy()
        for col in X_copy.columns:
            X_copy[col] = X_copy[col].map(self.maps_[col]).fillna(self.global_mean_)
        return X_copy
    
    def get_maps(self):
        """获取编码映射"""
        return self.maps_


class AreaTransformer(BaseEstimator, TransformerMixin):
    """面积转换器（保持为数值）"""
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return X.astype(float)


class RentTypeAreaInteraction(BaseEstimator, TransformerMixin):
    """整租/合租与面积的交互特征：rent_type_encoded * area"""
    def __init__(self):
        self.rent_type_encoder = LabelEncoder()
    
    def fit(self, X, y=None):
        # X 应该有两列: rent_type, area
        rent_type_col = X.iloc[:, 0]
        self.rent_type_encoder.fit(rent_type_col.astype(str))
        return self
    
    def transform(self, X):
        rent_type_col = X.iloc[:, 0].astype(str).apply(
            lambda x: self.rent_type_encoder.transform([x])[0] if x in self.rent_type_encoder.classes_ else 0
        )
        area_col = X.iloc[:, 1].astype(float)
        return (rent_type_col * area_col).values.reshape(-1, 1)

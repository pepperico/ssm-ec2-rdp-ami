"""
インスタンスタイプ検証クラス
インスタンスタイプの妥当性検証を担当
"""

import re
from typing import List, Tuple, Optional
from .types import InvalidValueError


class InstanceTypeValidator:
    """インスタンスタイプの妥当性検証を担当するクラス"""
    
    # AWS EC2 インスタンスファミリー（カテゴリ別に整理）
    INSTANCE_FAMILIES = [
        # 汎用インスタンス
        'a1', 't2', 't3', 't3a', 't4g', 
        'm4', 'm5', 'm5a', 'm5ad', 'm5d', 'm5dn', 'm5n', 'm5zn', 
        'm6a', 'm6g', 'm6gd', 'm6i', 'm6id', 'm6idn', 'm6in',
        'm7a', 'm7g', 'm7gd', 'm7i', 'm7i-flex',
        
        # コンピュート最適化インスタンス
        'c4', 'c5', 'c5a', 'c5ad', 'c5d', 'c5n',
        'c6a', 'c6g', 'c6gd', 'c6gn', 'c6i', 'c6id', 'c6in',
        'c7a', 'c7g', 'c7gd', 'c7gn', 'c7i', 'c7i-flex',
        
        # メモリ最適化インスタンス
        'r4', 'r5', 'r5a', 'r5ad', 'r5b', 'r5d', 'r5dn', 'r5n',
        'r6a', 'r6g', 'r6gd', 'r6i', 'r6id', 'r6idn', 'r6in',
        'r7a', 'r7g', 'r7gd', 'r7i', 'r7iz',
        'u-3tb1', 'u-6tb1', 'u-9tb1', 'u-12tb1', 'u-18tb1', 'u-24tb1',
        'x1', 'x1e', 'x2gd', 'x2idn', 'x2iedn', 'x2iezn', 'z1d',
        
        # ストレージ最適化インスタンス
        'd2', 'd3', 'd3en', 'h1', 'i3', 'i3en', 'i4g', 'i4i', 'im4gn', 'is4gen',
        
        # 高速化コンピューティングインスタンス
        'f1', 'g3', 'g4ad', 'g4dn', 'g5', 'g5g',
        'inf1', 'inf2', 'p2', 'p3', 'p3dn', 'p4d', 'p4de', 'p5',
        'trn1', 'trn1n', 'vt1',
        
        # ハイパフォーマンスコンピューティング
        'hpc6a', 'hpc6id', 'hpc7a', 'hpc7g'
    ]
    
    # インスタンスサイズ（小さいものから大きいものへ順序付け）
    INSTANCE_SIZES = [
        'nano', 'micro', 'small', 'medium', 'large', 'xlarge',
        '2xlarge', '3xlarge', '4xlarge', '6xlarge', '8xlarge', '9xlarge',
        '10xlarge', '12xlarge', '16xlarge', '18xlarge', '24xlarge', '32xlarge',
        '48xlarge', '56xlarge', '96xlarge', '112xlarge'
    ]
    
    def __init__(self):
        """InstanceTypeValidatorを初期化"""
        pass
    
    def validate_instance_type(self, instance_type: str) -> bool:
        """
        インスタンスタイプの妥当性を検証
        
        Args:
            instance_type: 検証対象のインスタンスタイプ
            
        Returns:
            bool: 有効な場合True
            
        Raises:
            InvalidValueError: インスタンスタイプが無効な場合
        """
        if not instance_type:
            raise InvalidValueError("インスタンスタイプが指定されていません。")
        
        if not isinstance(instance_type, str):
            raise InvalidValueError("インスタンスタイプは文字列である必要があります。")
        
        # 基本形式チェック
        if not self._is_valid_format(instance_type):
            raise InvalidValueError(
                f"無効なインスタンスタイプ形式です: {instance_type}. "
                "形式: {ファミリー}[世代][属性].{サイズ} (例: t3.medium, m5.large)"
            )
        
        # 詳細検証
        family, size = instance_type.split('.')
        
        if not self._is_valid_family(family):
            raise InvalidValueError(
                f"サポートされていないインスタンスファミリーです: {family}. "
                f"有効なファミリー例: {', '.join(self.INSTANCE_FAMILIES[:10])}..."
            )
        
        if not self._is_valid_size(size):
            raise InvalidValueError(
                f"サポートされていないインスタンスサイズです: {size}. "
                f"有効なサイズ例: {', '.join(self.INSTANCE_SIZES[:10])}..."
            )
        
        return True
    
    def _is_valid_format(self, instance_type: str) -> bool:
        """
        インスタンスタイプの基本形式をチェック
        
        Args:
            instance_type: インスタンスタイプ
            
        Returns:
            bool: 形式が正しい場合True
        """
        # 基本パターン: {family}.{size}
        pattern = r'^[a-z][a-z0-9]*[a-z0-9-]*\.[a-z0-9]+$'
        return bool(re.match(pattern, instance_type.lower()))
    
    def _is_valid_family(self, family: str) -> bool:
        """
        インスタンスファミリーの妥当性をチェック
        
        Args:
            family: インスタンスファミリー
            
        Returns:
            bool: 有効なファミリーの場合True
        """
        return family.lower() in [f.lower() for f in self.INSTANCE_FAMILIES]
    
    def _is_valid_size(self, size: str) -> bool:
        """
        インスタンスサイズの妥当性をチェック
        
        Args:
            size: インスタンスサイズ
            
        Returns:
            bool: 有効なサイズの場合True
        """
        return size.lower() in [s.lower() for s in self.INSTANCE_SIZES]
    
    def get_family_and_size(self, instance_type: str) -> Tuple[str, str]:
        """
        インスタンスタイプをファミリーとサイズに分離
        
        Args:
            instance_type: インスタンスタイプ
            
        Returns:
            Tuple[str, str]: (ファミリー, サイズ)
            
        Raises:
            InvalidValueError: インスタンスタイプが無効な場合
        """
        if not self._is_valid_format(instance_type):
            raise InvalidValueError(f"無効なインスタンスタイプ形式です: {instance_type}")
        
        family, size = instance_type.split('.', 1)
        return family.lower(), size.lower()
    
    def suggest_similar_instance_types(self, instance_type: str, limit: int = 5) -> List[str]:
        """
        似たインスタンスタイプを提案
        
        Args:
            instance_type: 基準となるインスタンスタイプ
            limit: 提案する最大数
            
        Returns:
            List[str]: 似たインスタンスタイプのリスト
        """
        try:
            family, size = self.get_family_and_size(instance_type)
        except InvalidValueError:
            # 無効な形式の場合は人気の高いインスタンスタイプを提案
            return ['t3.micro', 't3.small', 't3.medium', 'm5.large', 'c5.large'][:limit]
        
        suggestions = []
        
        # 同じファミリーで異なるサイズ
        for candidate_size in self.INSTANCE_SIZES:
            candidate = f"{family}.{candidate_size}"
            if candidate != instance_type:
                suggestions.append(candidate)
            if len(suggestions) >= limit:
                break
        
        return suggestions[:limit]
    
    def is_burstable_instance(self, instance_type: str) -> bool:
        """
        バーストable（T系）インスタンスかどうかを判定
        
        Args:
            instance_type: インスタンスタイプ
            
        Returns:
            bool: T系インスタンスの場合True
        """
        try:
            family, _ = self.get_family_and_size(instance_type)
            return family.startswith('t')
        except InvalidValueError:
            return False
    
    def get_instance_category(self, instance_type: str) -> str:
        """
        インスタンスタイプのカテゴリを取得
        
        Args:
            instance_type: インスタンスタイプ
            
        Returns:
            str: インスタンスカテゴリ
        """
        try:
            family, _ = self.get_family_and_size(instance_type)
        except InvalidValueError:
            return "Unknown"
        
        # カテゴリマッピング
        category_map = {
            # 汎用
            't': 'Burstable Performance', 
            'a': 'General Purpose',
            'm': 'General Purpose',
            # コンピュート最適化
            'c': 'Compute Optimized',
            # メモリ最適化
            'r': 'Memory Optimized',
            'x': 'Memory Optimized',
            'z': 'Memory Optimized', 
            'u': 'High Memory',
            # ストレージ最適化
            'd': 'Storage Optimized',
            'h': 'Storage Optimized',
            'i': 'Storage Optimized',
            # 高速化コンピューティング
            'f': 'Accelerated Computing',
            'g': 'Accelerated Computing', 
            'p': 'Accelerated Computing',
            'inf': 'Accelerated Computing',
            'trn': 'Accelerated Computing',
            'vt': 'Accelerated Computing',
            # HPC
            'hpc': 'High Performance Computing'
        }
        
        # ファミリーの最初の文字または文字列でマッチング
        for prefix, category in category_map.items():
            if family.startswith(prefix):
                return category
        
        return "General Purpose"  # デフォルト
    
    def validate_and_get_info(self, instance_type: str) -> dict:
        """
        インスタンスタイプを検証し、詳細情報を返す
        
        Args:
            instance_type: インスタンスタイプ
            
        Returns:
            dict: インスタンスタイプの詳細情報
            
        Raises:
            InvalidValueError: インスタンスタイプが無効な場合
        """
        # 検証実行
        self.validate_instance_type(instance_type)
        
        # 情報取得
        family, size = self.get_family_and_size(instance_type)
        
        return {
            'instance_type': instance_type,
            'family': family,
            'size': size,
            'category': self.get_instance_category(instance_type),
            'is_burstable': self.is_burstable_instance(instance_type),
            'is_valid': True
        }
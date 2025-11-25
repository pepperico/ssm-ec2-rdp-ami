"""
Key Pair管理クラス
Key Pairの管理と検証を担当
"""

from typing import Optional
from aws_cdk import Stack, aws_ec2 as ec2
from .types import KeyPairNotFoundError


class KeyPairManager:
    """Key Pairの管理と検証を担当するクラス"""
    
    def __init__(self, stack: Stack):
        """
        KeyPairManagerを初期化
        
        Args:
            stack: CDK Stackインスタンス
        """
        self.stack = stack
    
    def get_key_pair(self, key_pair_name: Optional[str]) -> Optional[ec2.IKeyPair]:
        """
        Key Pair名からIKeyPairオブジェクトを取得
        
        Args:
            key_pair_name: Key Pair名（Noneの場合はNoneを返す）
            
        Returns:
            Optional[ec2.IKeyPair]: KeyPairオブジェクト、または None
            
        Raises:
            KeyPairNotFoundError: Key Pairが見つからない場合
        """
        if key_pair_name is None:
            return None
        
        if not key_pair_name or not key_pair_name.strip():
            return None
        
        try:
            # CDKでKey Pairを参照
            key_pair = ec2.KeyPair.from_key_pair_name(
                self.stack,
                f"KeyPair-{key_pair_name}",
                key_pair_name
            )
            return key_pair
        except Exception as e:
            raise KeyPairNotFoundError(
                f"指定されたKey Pair '{key_pair_name}' が見つかりません。"
                f"Key Pairがこのリージョンに存在することを確認してください。"
            ) from e
    
    def has_key_pair(self, key_pair_name: Optional[str]) -> bool:
        """
        Key Pairが存在するかどうかを確認
        
        Args:
            key_pair_name: Key Pair名
            
        Returns:
            bool: Key Pairが存在する場合True
        """
        if key_pair_name is None or not key_pair_name.strip():
            return False
        
        try:
            self.get_key_pair(key_pair_name)
            return True
        except KeyPairNotFoundError:
            return False
    
    def validate_key_pair_name(self, key_pair_name: Optional[str]) -> bool:
        """
        Key Pair名の形式を検証
        
        Args:
            key_pair_name: Key Pair名
            
        Returns:
            bool: 有効な形式の場合True
        """
        if key_pair_name is None:
            return True  # Noneは有効（任意項目のため）
        
        if not isinstance(key_pair_name, str):
            return False
        
        if not key_pair_name.strip():
            return False
        
        # Key Pair名の基本ルール
        # - 1-255文字
        # - ASCII英数字、スペース、および以下の文字: - _ . : / ( ) # , @ [ ] + = ; ! $ &
        if len(key_pair_name) > 255:
            return False
        
        # 基本的な文字チェック（より制限的な実装）
        import re
        pattern = r'^[a-zA-Z0-9_.-]+$'
        return bool(re.match(pattern, key_pair_name))
    
    def get_key_pair_info(self, key_pair_name: Optional[str]) -> dict:
        """
        Key Pairの詳細情報を取得
        
        Args:
            key_pair_name: Key Pair名
            
        Returns:
            dict: Key Pairの詳細情報
        """
        if key_pair_name is None:
            return {
                'key_pair_name': None,
                'is_specified': False,
                'is_valid_format': True,
                'exists': None,  # 未確認
                'recommended_action': 'Key Pair未指定 - SSM Session Managerでのアクセスを推奨'
            }
        
        is_valid_format = self.validate_key_pair_name(key_pair_name)
        
        if not is_valid_format:
            return {
                'key_pair_name': key_pair_name,
                'is_specified': True,
                'is_valid_format': False,
                'exists': False,
                'recommended_action': 'Key Pair名の形式が無効です'
            }
        
        exists = self.has_key_pair(key_pair_name)
        
        return {
            'key_pair_name': key_pair_name,
            'is_specified': True,
            'is_valid_format': True,
            'exists': exists,
            'recommended_action': (
                'Key Pairが利用可能です' if exists 
                else f'Key Pair \"{key_pair_name}\" が見つかりません'
            )
        }
    
    def suggest_key_pair_alternatives(self, key_pair_name: Optional[str]) -> list[str]:
        """
        Key Pairが見つからない場合の代替案を提案
        
        Args:
            key_pair_name: Key Pair名
            
        Returns:
            list[str]: 代替案のリスト
        """
        if key_pair_name is None:
            return [
                "SSM Session Managerを使用（推奨）",
                "新しいKey Pairを作成してください",
                "既存のKey Pair名を確認してください"
            ]
        
        return [
            f"Key Pair名のスペルを確認: {key_pair_name}",
            "正しいリージョンでKey Pairが作成されているか確認",
            "AWS EC2コンソールでKey Pairの存在を確認",
            "SSM Session Managerでのアクセスを検討（Key Pair不要）",
            "新しいKey Pairを作成してください"
        ]
    
    def create_instance_parameters(
        self, 
        key_pair_name: Optional[str],
        base_parameters: dict
    ) -> dict:
        """
        Key Pair設定を含むインスタンスパラメータを作成
        
        Args:
            key_pair_name: Key Pair名
            base_parameters: ベースとなるインスタンスパラメータ
            
        Returns:
            dict: Key Pair設定を含むインスタンスパラメータ
            
        Raises:
            KeyPairNotFoundError: 指定されたKey Pairが見つからない場合
        """
        # ベースパラメータをコピー
        parameters = base_parameters.copy()
        
        # Key Pair設定
        key_pair = self.get_key_pair(key_pair_name)
        if key_pair is not None:
            parameters['key_pair'] = key_pair
        
        return parameters
    
    def get_access_methods(self, key_pair_name: Optional[str]) -> dict:
        """
        利用可能なアクセス方法を取得
        
        Args:
            key_pair_name: Key Pair名
            
        Returns:
            dict: アクセス方法の情報
        """
        has_key_pair = key_pair_name is not None and self.has_key_pair(key_pair_name)
        
        access_methods = {
            'ssm_session_manager': {
                'available': True,
                'description': 'AWS Systems Manager Session Manager',
                'recommended': True,
                'requirements': ['IAM権限', 'SSM Agent']
            }
        }
        
        if has_key_pair:
            access_methods['ssh_rdp'] = {
                'available': True,
                'description': 'SSH/RDP (Key Pairを使用)',
                'recommended': False,  # SSMを推奨
                'requirements': ['Key Pair', 'セキュリティグループ設定']
            }
        else:
            access_methods['ssh_rdp'] = {
                'available': False,
                'description': 'SSH/RDP (Key Pair必要)',
                'recommended': False,
                'requirements': ['Key Pair作成が必要']
            }
        
        return access_methods
    
    def is_key_pair_recommended(self, key_pair_name: Optional[str]) -> bool:
        """
        Key Pairの使用が推奨されるかどうかを判定
        
        通常はSSM Session Managerを推奨するため、Falseを返す
        
        Args:
            key_pair_name: Key Pair名
            
        Returns:
            bool: Key Pair使用が推奨される場合True
        """
        # セキュリティベストプラクティスとして、
        # SSM Session Managerの使用を推奨
        return False
    
    def get_security_recommendations(self, key_pair_name: Optional[str]) -> list[str]:
        """
        セキュリティ推奨事項を取得
        
        Args:
            key_pair_name: Key Pair名
            
        Returns:
            list[str]: セキュリティ推奨事項
        """
        recommendations = [
            "SSM Session Managerを主要なアクセス方法として使用する",
            "インスタンスをプライベートサブネットに配置する",
            "必要最小限のセキュリティグループルールを設定する"
        ]
        
        if key_pair_name is not None:
            recommendations.extend([
                "Key Pairを安全に保管し、共有を避ける",
                "定期的にKey Pairをローテーションする",
                "Key Pairは緊急時のアクセス手段としてのみ使用する"
            ])
        else:
            recommendations.append(
                "Key Pair未指定により、SSH/RDPアクセスが制限されセキュリティが向上"
            )
        
        return recommendations
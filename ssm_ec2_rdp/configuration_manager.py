"""
設定管理クラス
cdk.jsonからの設定読み取り、検証、統合を担当
"""

from typing import Optional, Dict, Any
from aws_cdk import App
from .types import EC2Configuration, validate_configuration, get_configuration_help


class ConfigurationManager:
    """設定の読み取り、検証、統合を担当するクラス"""
    
    def __init__(self, app: App):
        """
        ConfigurationManagerを初期化
        
        Args:
            app: CDK Appインスタンス
        """
        self.app = app
    
    def get_configuration(self) -> EC2Configuration:
        """
        cdk.jsonから設定を読み取り、検証済みオブジェクトを返す
        
        Returns:
            EC2Configuration: 検証済みの設定オブジェクト
            
        Raises:
            ConfigurationError: 設定に問題がある場合
        """
        # cdk.jsonのcontextから設定値を取得
        context = self._extract_context_values()
        
        # 設定を検証してEC2Configurationオブジェクトを作成
        return validate_configuration(context)
    
    def _extract_context_values(self) -> Dict[str, Any]:
        """
        CDK Appのcontextから必要な設定値を抽出
        
        Returns:
            Dict[str, Any]: 抽出された設定値の辞書
        """
        return {
            'ami-id': self.app.node.try_get_context('ami-id'),
            'ami-parameter': self.app.node.try_get_context('ami-parameter'),
            'instance-type': self.app.node.try_get_context('instance-type'),
            'key-pair-name': self.app.node.try_get_context('key-pair-name')
        }
    
    def print_help(self) -> None:
        """設定ヘルプを表示"""
        print(get_configuration_help())
    
    def get_context_value(self, key: str) -> Optional[str]:
        """
        指定されたキーのcontext値を取得
        
        Args:
            key: 取得するcontextキー
            
        Returns:
            Optional[str]: context値、存在しない場合はNone
        """
        return self.app.node.try_get_context(key)
    
    def has_context_value(self, key: str) -> bool:
        """
        指定されたキーのcontext値が存在するかチェック
        
        Args:
            key: チェックするcontextキー
            
        Returns:
            bool: 値が存在する場合True
        """
        value = self.get_context_value(key)
        return value is not None and value != ""
    
    def validate_context_completeness(self) -> tuple[bool, list[str]]:
        """
        必須context値の完全性をチェック
        
        Returns:
            tuple[bool, list[str]]: (完全性, 不足しているキーのリスト)
        """
        missing_keys = []
        
        # インスタンスタイプの必須チェック
        if not self.has_context_value('instance-type'):
            missing_keys.append('instance-type')
        
        # AMI設定の必須チェック（どちらか一つが必要）
        has_ami_id = self.has_context_value('ami-id')
        has_ami_parameter = self.has_context_value('ami-parameter')
        
        if not has_ami_id and not has_ami_parameter:
            missing_keys.append('ami-id または ami-parameter')
        
        is_complete = len(missing_keys) == 0
        return is_complete, missing_keys
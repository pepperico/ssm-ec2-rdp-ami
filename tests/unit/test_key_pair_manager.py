"""
KeyPairManagerのユニットテスト
"""
import pytest
from unittest.mock import Mock, patch
from aws_cdk import Stack, aws_ec2 as ec2
from ssm_ec2_rdp.key_pair_manager import KeyPairManager
from ssm_ec2_rdp.types import KeyPairNotFoundError


class TestKeyPairManager:
    """KeyPairManagerクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_stack = Mock(spec=Stack)
        self.mock_stack.region = "us-west-2"
        self.manager = KeyPairManager(self.mock_stack)
    
    def test_initialization(self):
        """初期化のテスト"""
        assert isinstance(self.manager, KeyPairManager)
        assert self.manager.stack == self.mock_stack
    
    def test_get_key_pair_none_input(self):
        """Key Pair名がNoneの場合のテスト"""
        result = self.manager.get_key_pair(None)
        assert result is None
    
    def test_get_key_pair_empty_string(self):
        """Key Pair名が空文字の場合のテスト"""
        empty_names = ["", "   ", "\t", "\n"]
        
        for name in empty_names:
            result = self.manager.get_key_pair(name)
            assert result is None, f"Failed for: '{name}'"
    
    @patch('aws_cdk.aws_ec2.KeyPair.from_key_pair_name')
    def test_get_key_pair_valid_name(self, mock_from_key_pair_name):
        """有効なKey Pair名での取得テスト"""
        mock_key_pair = Mock(spec=ec2.IKeyPair)
        mock_from_key_pair_name.return_value = mock_key_pair
        
        result = self.manager.get_key_pair("test-key-pair")
        
        assert result == mock_key_pair
        mock_from_key_pair_name.assert_called_once_with(
            self.mock_stack,
            "KeyPair-test-key-pair",
            "test-key-pair"
        )
    
    @patch('aws_cdk.aws_ec2.KeyPair.from_key_pair_name')
    def test_get_key_pair_not_found(self, mock_from_key_pair_name):
        """Key Pairが見つからない場合のテスト"""
        mock_from_key_pair_name.side_effect = Exception("KeyPair not found")
        
        with pytest.raises(KeyPairNotFoundError) as exc_info:
            self.manager.get_key_pair("non-existent-key")
        
        assert "指定されたKey Pair 'non-existent-key' が見つかりません" in str(exc_info.value)
        assert "Key Pairがこのリージョンに存在することを確認してください" in str(exc_info.value)
    
    def test_has_key_pair_none_input(self):
        """has_key_pair: Key Pair名がNoneの場合のテスト"""
        result = self.manager.has_key_pair(None)
        assert result is False
    
    def test_has_key_pair_empty_string(self):
        """has_key_pair: Key Pair名が空文字の場合のテスト"""
        empty_names = ["", "   ", "\t", "\n"]
        
        for name in empty_names:
            result = self.manager.has_key_pair(name)
            assert result is False, f"Failed for: '{name}'"
    
    @patch('aws_cdk.aws_ec2.KeyPair.from_key_pair_name')
    def test_has_key_pair_exists(self, mock_from_key_pair_name):
        """has_key_pair: Key Pairが存在する場合のテスト"""
        mock_key_pair = Mock(spec=ec2.IKeyPair)
        mock_from_key_pair_name.return_value = mock_key_pair
        
        result = self.manager.has_key_pair("existing-key")
        
        assert result is True
        mock_from_key_pair_name.assert_called_once()
    
    @patch('aws_cdk.aws_ec2.KeyPair.from_key_pair_name')
    def test_has_key_pair_not_exists(self, mock_from_key_pair_name):
        """has_key_pair: Key Pairが存在しない場合のテスト"""
        mock_from_key_pair_name.side_effect = KeyPairNotFoundError("Not found")
        
        result = self.manager.has_key_pair("non-existent-key")
        
        assert result is False
    
    def test_validate_key_pair_name_none(self):
        """validate_key_pair_name: Noneの場合のテスト"""
        result = self.manager.validate_key_pair_name(None)
        assert result is True  # Noneは有効（任意項目のため）
    
    def test_validate_key_pair_name_non_string(self):
        """validate_key_pair_name: 文字列以外の場合のテスト"""
        non_strings = [123, [], {}, True]
        
        for value in non_strings:
            result = self.manager.validate_key_pair_name(value)
            assert result is False, f"Failed for: {value}"
    
    def test_validate_key_pair_name_empty_string(self):
        """validate_key_pair_name: 空文字の場合のテスト"""
        empty_names = ["", "   ", "\t", "\n"]
        
        for name in empty_names:
            result = self.manager.validate_key_pair_name(name)
            assert result is False, f"Failed for: '{name}'"
    
    def test_validate_key_pair_name_valid_names(self):
        """validate_key_pair_name: 有効な名前の場合のテスト"""
        valid_names = [
            "test-key",
            "my_key_pair",
            "key123",
            "test.key",
            "a",  # 最短
            "a" * 255  # 最長
        ]
        
        for name in valid_names:
            result = self.manager.validate_key_pair_name(name)
            assert result is True, f"Failed for: '{name}'"
    
    def test_validate_key_pair_name_invalid_names(self):
        """validate_key_pair_name: 無効な名前の場合のテスト"""
        invalid_names = [
            "key with spaces",
            "key@pair",
            "key#pair",
            "key$pair",
            "key%pair",
            "a" * 256,  # 長すぎる
            "key/pair"  # スラッシュ
        ]
        
        for name in invalid_names:
            result = self.manager.validate_key_pair_name(name)
            assert result is False, f"Should fail for: '{name}'"
    
    def test_get_key_pair_info_none(self):
        """get_key_pair_info: Noneの場合のテスト"""
        info = self.manager.get_key_pair_info(None)
        
        expected = {
            'key_pair_name': None,
            'is_specified': False,
            'is_valid_format': True,
            'exists': None,
            'recommended_action': 'Key Pair未指定 - SSM Session Managerでのアクセスを推奨'
        }
        
        assert info == expected
    
    def test_get_key_pair_info_invalid_format(self):
        """get_key_pair_info: 無効な形式の場合のテスト"""
        info = self.manager.get_key_pair_info("invalid key name")
        
        expected = {
            'key_pair_name': "invalid key name",
            'is_specified': True,
            'is_valid_format': False,
            'exists': False,
            'recommended_action': 'Key Pair名の形式が無効です'
        }
        
        assert info == expected
    
    @patch.object(KeyPairManager, 'has_key_pair', return_value=True)
    def test_get_key_pair_info_valid_existing(self, mock_has_key_pair):
        """get_key_pair_info: 有効で存在する場合のテスト"""
        info = self.manager.get_key_pair_info("valid-key")
        
        expected = {
            'key_pair_name': "valid-key",
            'is_specified': True,
            'is_valid_format': True,
            'exists': True,
            'recommended_action': 'Key Pairが利用可能です'
        }
        
        assert info == expected
        mock_has_key_pair.assert_called_once_with("valid-key")
    
    @patch.object(KeyPairManager, 'has_key_pair', return_value=False)
    def test_get_key_pair_info_valid_not_existing(self, mock_has_key_pair):
        """get_key_pair_info: 有効だが存在しない場合のテスト"""
        info = self.manager.get_key_pair_info("valid-key")
        
        expected = {
            'key_pair_name': "valid-key",
            'is_specified': True,
            'is_valid_format': True,
            'exists': False,
            'recommended_action': 'Key Pair "valid-key" が見つかりません'
        }
        
        assert info == expected
    
    def test_suggest_key_pair_alternatives_none(self):
        """suggest_key_pair_alternatives: Noneの場合のテスト"""
        suggestions = self.manager.suggest_key_pair_alternatives(None)
        
        expected = [
            "SSM Session Managerを使用（推奨）",
            "新しいKey Pairを作成してください",
            "既存のKey Pair名を確認してください"
        ]
        
        assert suggestions == expected
    
    def test_suggest_key_pair_alternatives_with_name(self):
        """suggest_key_pair_alternatives: 名前指定の場合のテスト"""
        suggestions = self.manager.suggest_key_pair_alternatives("test-key")
        
        expected = [
            "Key Pair名のスペルを確認: test-key",
            "正しいリージョンでKey Pairが作成されているか確認",
            "AWS EC2コンソールでKey Pairの存在を確認",
            "SSM Session Managerでのアクセスを検討（Key Pair不要）",
            "新しいKey Pairを作成してください"
        ]
        
        assert suggestions == expected
    
    @patch.object(KeyPairManager, 'get_key_pair')
    def test_create_instance_parameters_no_key_pair(self, mock_get_key_pair):
        """create_instance_parameters: Key Pairなしの場合のテスト"""
        mock_get_key_pair.return_value = None
        
        base_params = {'instance_type': 't3.medium', 'vpc': 'test-vpc'}
        result = self.manager.create_instance_parameters(None, base_params)
        
        expected = {'instance_type': 't3.medium', 'vpc': 'test-vpc'}
        assert result == expected
        mock_get_key_pair.assert_called_once_with(None)
    
    @patch.object(KeyPairManager, 'get_key_pair')
    def test_create_instance_parameters_with_key_pair(self, mock_get_key_pair):
        """create_instance_parameters: Key Pairありの場合のテスト"""
        mock_key_pair = Mock(spec=ec2.IKeyPair)
        mock_get_key_pair.return_value = mock_key_pair
        
        base_params = {'instance_type': 't3.medium', 'vpc': 'test-vpc'}
        result = self.manager.create_instance_parameters("test-key", base_params)
        
        expected = {
            'instance_type': 't3.medium',
            'vpc': 'test-vpc',
            'key_pair': mock_key_pair
        }
        assert result == expected
    
    @patch.object(KeyPairManager, 'get_key_pair')
    def test_create_instance_parameters_key_pair_error(self, mock_get_key_pair):
        """create_instance_parameters: Key Pairエラーの場合のテスト"""
        mock_get_key_pair.side_effect = KeyPairNotFoundError("Not found")
        
        base_params = {'instance_type': 't3.medium'}
        
        with pytest.raises(KeyPairNotFoundError):
            self.manager.create_instance_parameters("invalid-key", base_params)
    
    @patch.object(KeyPairManager, 'has_key_pair')
    def test_get_access_methods_no_key_pair(self, mock_has_key_pair):
        """get_access_methods: Key Pairなしの場合のテスト"""
        mock_has_key_pair.return_value = False
        
        methods = self.manager.get_access_methods(None)
        
        assert 'ssm_session_manager' in methods
        assert methods['ssm_session_manager']['available'] is True
        assert methods['ssm_session_manager']['recommended'] is True
        
        assert 'ssh_rdp' in methods
        assert methods['ssh_rdp']['available'] is False
        assert methods['ssh_rdp']['recommended'] is False
    
    @patch.object(KeyPairManager, 'has_key_pair')
    def test_get_access_methods_with_key_pair(self, mock_has_key_pair):
        """get_access_methods: Key Pairありの場合のテスト"""
        mock_has_key_pair.return_value = True
        
        methods = self.manager.get_access_methods("test-key")
        
        assert 'ssm_session_manager' in methods
        assert methods['ssm_session_manager']['available'] is True
        assert methods['ssm_session_manager']['recommended'] is True
        
        assert 'ssh_rdp' in methods
        assert methods['ssh_rdp']['available'] is True
        assert methods['ssh_rdp']['recommended'] is False  # SSMを推奨
        
        mock_has_key_pair.assert_called_once_with("test-key")
    
    def test_is_key_pair_recommended(self):
        """is_key_pair_recommended: セキュリティ推奨のテスト"""
        # SSM Session Managerを推奨するため、常にFalse
        assert self.manager.is_key_pair_recommended(None) is False
        assert self.manager.is_key_pair_recommended("test-key") is False
    
    def test_get_security_recommendations_no_key_pair(self):
        """get_security_recommendations: Key Pairなしの場合のテスト"""
        recommendations = self.manager.get_security_recommendations(None)
        
        expected_base = [
            "SSM Session Managerを主要なアクセス方法として使用する",
            "インスタンスをプライベートサブネットに配置する",
            "必要最小限のセキュリティグループルールを設定する"
        ]
        
        expected_no_key = [
            "Key Pair未指定により、SSH/RDPアクセスが制限されセキュリティが向上"
        ]
        
        for rec in expected_base:
            assert rec in recommendations
        for rec in expected_no_key:
            assert rec in recommendations
    
    def test_get_security_recommendations_with_key_pair(self):
        """get_security_recommendations: Key Pairありの場合のテスト"""
        recommendations = self.manager.get_security_recommendations("test-key")
        
        expected_base = [
            "SSM Session Managerを主要なアクセス方法として使用する",
            "インスタンスをプライベートサブネットに配置する",
            "必要最小限のセキュリティグループルールを設定する"
        ]
        
        expected_with_key = [
            "Key Pairを安全に保管し、共有を避ける",
            "定期的にKey Pairをローテーションする",
            "Key Pairは緊急時のアクセス手段としてのみ使用する"
        ]
        
        for rec in expected_base:
            assert rec in recommendations
        for rec in expected_with_key:
            assert rec in recommendations


class TestKeyPairManagerIntegration:
    """KeyPairManagerの統合テスト"""
    
    def test_comprehensive_workflow(self):
        """包括的なワークフローテスト"""
        mock_stack = Mock(spec=Stack)
        manager = KeyPairManager(mock_stack)
        
        # 1. None での処理
        assert manager.get_key_pair(None) is None
        assert manager.has_key_pair(None) is False
        assert manager.validate_key_pair_name(None) is True
        
        info = manager.get_key_pair_info(None)
        assert info['is_specified'] is False
        assert info['is_valid_format'] is True
        
        # 2. セキュリティ推奨事項
        recommendations = manager.get_security_recommendations(None)
        assert len(recommendations) > 0
        assert any("SSM Session Manager" in rec for rec in recommendations)
        
        # 3. アクセス方法
        methods = manager.get_access_methods(None)
        assert methods['ssm_session_manager']['available'] is True
        assert methods['ssh_rdp']['available'] is False
    
    def test_error_propagation(self):
        """エラー伝播のテスト"""
        mock_stack = Mock(spec=Stack)
        manager = KeyPairManager(mock_stack)
        
        # get_key_pair でのエラー
        with patch('aws_cdk.aws_ec2.KeyPair.from_key_pair_name') as mock_from_key_pair:
            mock_from_key_pair.side_effect = Exception("AWS Error")
            
            with pytest.raises(KeyPairNotFoundError) as exc_info:
                manager.get_key_pair("test-key")
            
            # 元の例外が保持されているかチェック
            assert "指定されたKey Pair 'test-key' が見つかりません" in str(exc_info.value)
            assert exc_info.value.__cause__ is not None
    
    def test_validation_consistency(self):
        """バリデーション整合性のテスト"""
        mock_stack = Mock(spec=Stack)
        manager = KeyPairManager(mock_stack)
        
        # 同じ名前に対して、各メソッドが整合性のある結果を返すか
        test_names = [
            None,
            "",
            "   ",
            "valid-key",
            "invalid key name",
            "key@invalid"
        ]
        
        for name in test_names:
            # validate_key_pair_name の結果
            is_valid_format = manager.validate_key_pair_name(name)
            
            # get_key_pair_info の結果と整合性をチェック
            info = manager.get_key_pair_info(name)
            assert info['is_valid_format'] == is_valid_format, f"Inconsistency for: '{name}'"
"""
InstanceTypeValidatorのユニットテスト
"""
import pytest
from ssm_ec2_rdp.instance_type_validator import InstanceTypeValidator
from ssm_ec2_rdp.types import InvalidValueError


class TestInstanceTypeValidator:
    """InstanceTypeValidatorクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.validator = InstanceTypeValidator()
    
    def test_initialization(self):
        """初期化のテスト"""
        assert isinstance(self.validator, InstanceTypeValidator)
        assert len(self.validator.INSTANCE_FAMILIES) > 0
        assert len(self.validator.INSTANCE_SIZES) > 0
    
    def test_validate_instance_type_valid_types(self):
        """有効なインスタンスタイプの検証テスト"""
        valid_types = [
            't3.micro', 't3.small', 't3.medium', 't3.large', 't3.xlarge',
            'm5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge',
            'c5.large', 'c5.xlarge', 'c5.2xlarge',
            'r5.large', 'r5.xlarge', 'r5.2xlarge',
            'i3.large', 'i3.xlarge',
            'p3.2xlarge', 'p3.8xlarge'
        ]
        
        for instance_type in valid_types:
            result = self.validator.validate_instance_type(instance_type)
            assert result is True, f"Failed for: {instance_type}"
    
    def test_validate_instance_type_empty_string(self):
        """空文字のインスタンスタイプ検証テスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            self.validator.validate_instance_type("")
        
        assert "インスタンスタイプが指定されていません" in str(exc_info.value)
    
    def test_validate_instance_type_none(self):
        """Noneのインスタンスタイプ検証テスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            self.validator.validate_instance_type(None)
        
        assert "インスタンスタイプが指定されていません" in str(exc_info.value)
    
    def test_validate_instance_type_non_string(self):
        """文字列以外のインスタンスタイプ検証テスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            self.validator.validate_instance_type(123)
        
        assert "インスタンスタイプは文字列である必要があります" in str(exc_info.value)
    
    def test_validate_instance_type_invalid_format(self):
        """無効な形式のインスタンスタイプ検証テスト"""
        invalid_formats = [
            'invalid', 't3', 't3.', '.medium', 't3-medium', 'T3.medium',
            't3.medium.extra', '3t.medium', 't$.medium'
        ]
        
        for instance_type in invalid_formats:
            with pytest.raises(InvalidValueError) as exc_info:
                self.validator.validate_instance_type(instance_type)
            
            assert "無効なインスタンスタイプ形式" in str(exc_info.value)
    
    def test_validate_instance_type_invalid_family(self):
        """無効なファミリーのインスタンスタイプ検証テスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            self.validator.validate_instance_type("invalid.medium")
        
        assert "サポートされていないインスタンスファミリー" in str(exc_info.value)
    
    def test_validate_instance_type_invalid_size(self):
        """無効なサイズのインスタンスタイプ検証テスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            self.validator.validate_instance_type("t3.invalid")
        
        assert "サポートされていないインスタンスサイズ" in str(exc_info.value)
    
    def test_is_valid_format_valid_cases(self):
        """有効な形式のテスト"""
        valid_formats = [
            't3.medium', 'm5.large', 'c5.xlarge', 'r5.2xlarge',
            'i3en.large', 'c6gn.medium', 'hpc6a.48xlarge'
        ]
        
        for instance_type in valid_formats:
            assert self.validator._is_valid_format(instance_type) is True
    
    def test_is_valid_format_invalid_cases(self):
        """無効な形式のテスト"""
        invalid_formats = [
            'invalid', 't3', 't3.', '.medium', 't3-medium',
            't3.medium.extra', '3t.medium', 't$.medium'
        ]
        
        for instance_type in invalid_formats:
            assert self.validator._is_valid_format(instance_type) is False
    
    def test_is_valid_family_valid_cases(self):
        """有効なファミリーのテスト"""
        valid_families = ['t3', 'm5', 'c5', 'r5', 'i3', 'p3', 'g4dn', 'hpc6a']
        
        for family in valid_families:
            assert self.validator._is_valid_family(family) is True
    
    def test_is_valid_family_invalid_cases(self):
        """無効なファミリーのテスト"""
        invalid_families = ['invalid', 't99', 'xyz', 'test']
        
        for family in invalid_families:
            assert self.validator._is_valid_family(family) is False
    
    def test_is_valid_size_valid_cases(self):
        """有効なサイズのテスト"""
        valid_sizes = [
            'nano', 'micro', 'small', 'medium', 'large', 'xlarge',
            '2xlarge', '4xlarge', '8xlarge', '16xlarge', '32xlarge'
        ]
        
        for size in valid_sizes:
            assert self.validator._is_valid_size(size) is True
    
    def test_is_valid_size_invalid_cases(self):
        """無効なサイズのテスト"""
        invalid_sizes = ['invalid', 'tiny', 'huge', '1xlarge', '128xlarge']
        
        for size in invalid_sizes:
            assert self.validator._is_valid_size(size) is False
    
    def test_get_family_and_size_valid_cases(self):
        """有効なケースでのファミリー・サイズ分離テスト"""
        test_cases = [
            ('t3.medium', ('t3', 'medium')),
            ('m5.large', ('m5', 'large')),
            ('c5.2xlarge', ('c5', '2xlarge')),
            ('R5.XLARGE', ('r5', 'xlarge'))  # 大文字小文字混在
        ]
        
        for instance_type, expected in test_cases:
            family, size = self.validator.get_family_and_size(instance_type)
            assert (family, size) == expected
    
    def test_get_family_and_size_invalid_cases(self):
        """無効なケースでのファミリー・サイズ分離テスト"""
        invalid_types = ['invalid', 't3', 't3.', '.medium']
        
        for instance_type in invalid_types:
            with pytest.raises(InvalidValueError):
                self.validator.get_family_and_size(instance_type)
    
    def test_suggest_similar_instance_types_valid_input(self):
        """有効な入力での類似インスタンスタイプ提案テスト"""
        suggestions = self.validator.suggest_similar_instance_types('t3.medium', limit=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        assert 't3.medium' not in suggestions  # 元のタイプは除外
        assert all(s.startswith('t3.') for s in suggestions)  # 同じファミリー
    
    def test_suggest_similar_instance_types_invalid_input(self):
        """無効な入力での類似インスタンスタイプ提案テスト"""
        suggestions = self.validator.suggest_similar_instance_types('invalid', limit=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        # デフォルトの人気タイプを提案
        expected_defaults = ['t3.micro', 't3.small', 't3.medium']
        assert suggestions == expected_defaults
    
    def test_is_burstable_instance_true_cases(self):
        """Burstableインスタンス判定（True）のテスト"""
        burstable_types = ['t2.micro', 't3.small', 't3a.medium', 't4g.large']
        
        for instance_type in burstable_types:
            assert self.validator.is_burstable_instance(instance_type) is True
    
    def test_is_burstable_instance_false_cases(self):
        """Burstableインスタンス判定（False）のテスト"""
        non_burstable_types = ['m5.large', 'c5.xlarge', 'r5.2xlarge', 'invalid']
        
        for instance_type in non_burstable_types:
            assert self.validator.is_burstable_instance(instance_type) is False
    
    def test_get_instance_category_various_types(self):
        """様々なインスタンスタイプのカテゴリ取得テスト"""
        test_cases = [
            ('t3.medium', 'Burstable Performance'),
            ('m5.large', 'General Purpose'),
            ('c5.xlarge', 'Compute Optimized'),
            ('r5.large', 'Memory Optimized'),
            ('i3.large', 'Storage Optimized'),
            ('p3.2xlarge', 'Accelerated Computing'),
            ('g4dn.xlarge', 'Accelerated Computing'),
            ('hpc6a.48xlarge', 'High Performance Computing'),
            ('invalid', 'Unknown')
        ]
        
        for instance_type, expected_category in test_cases:
            category = self.validator.get_instance_category(instance_type)
            assert category == expected_category, f"Failed for {instance_type}: got {category}, expected {expected_category}"
    
    def test_validate_and_get_info_valid_instance(self):
        """有効なインスタンスタイプでの詳細情報取得テスト"""
        info = self.validator.validate_and_get_info('t3.medium')
        
        expected_info = {
            'instance_type': 't3.medium',
            'family': 't3',
            'size': 'medium',
            'category': 'Burstable Performance',
            'is_burstable': True,
            'is_valid': True
        }
        
        assert info == expected_info
    
    def test_validate_and_get_info_various_types(self):
        """様々なインスタンスタイプでの詳細情報取得テスト"""
        test_cases = [
            ('m5.large', 'General Purpose', False),
            ('c5.xlarge', 'Compute Optimized', False),
            ('r5.2xlarge', 'Memory Optimized', False),
            ('t4g.small', 'Burstable Performance', True)
        ]
        
        for instance_type, expected_category, expected_burstable in test_cases:
            info = self.validator.validate_and_get_info(instance_type)
            
            assert info['instance_type'] == instance_type
            assert info['category'] == expected_category
            assert info['is_burstable'] == expected_burstable
            assert info['is_valid'] is True
    
    def test_validate_and_get_info_invalid_instance(self):
        """無効なインスタンスタイプでの詳細情報取得エラーテスト"""
        with pytest.raises(InvalidValueError):
            self.validator.validate_and_get_info('invalid.type')
    
    def test_instance_families_completeness(self):
        """インスタンスファミリーリストの完全性テスト"""
        # 主要なファミリーが含まれていることを確認
        major_families = [
            't2', 't3', 't3a', 't4g',  # Burstable
            'm4', 'm5', 'm6i',         # General Purpose
            'c4', 'c5', 'c6i',         # Compute Optimized
            'r4', 'r5', 'r6i',         # Memory Optimized
            'i3', 'i4i',               # Storage Optimized
            'p3', 'g4dn'               # Accelerated Computing
        ]
        
        families_lower = [f.lower() for f in self.validator.INSTANCE_FAMILIES]
        
        for family in major_families:
            assert family in families_lower, f"Major family {family} not found"
    
    def test_instance_sizes_completeness(self):
        """インスタンスサイズリストの完全性テスト"""
        # 主要なサイズが含まれていることを確認
        major_sizes = [
            'nano', 'micro', 'small', 'medium', 'large', 'xlarge',
            '2xlarge', '4xlarge', '8xlarge', '16xlarge'
        ]
        
        sizes_lower = [s.lower() for s in self.validator.INSTANCE_SIZES]
        
        for size in major_sizes:
            assert size in sizes_lower, f"Major size {size} not found"


class TestInstanceTypeValidatorIntegration:
    """InstanceTypeValidatorの統合テスト"""
    
    def test_comprehensive_validation_workflow(self):
        """包括的な検証ワークフローテスト"""
        validator = InstanceTypeValidator()
        
        # 様々なインスタンスタイプでのフルワークフロー
        test_instances = [
            't3.medium',
            'm5.large', 
            'c5.2xlarge',
            'r5.xlarge',
            'i3.large'
        ]
        
        for instance_type in test_instances:
            # 1. 基本検証
            is_valid = validator.validate_instance_type(instance_type)
            assert is_valid is True
            
            # 2. 情報取得
            info = validator.validate_and_get_info(instance_type)
            assert info['is_valid'] is True
            
            # 3. ファミリー・サイズ分離
            family, size = validator.get_family_and_size(instance_type)
            assert info['family'] == family
            assert info['size'] == size
            
            # 4. カテゴリ取得
            category = validator.get_instance_category(instance_type)
            assert info['category'] == category
            
            # 5. Burstable判定
            is_burstable = validator.is_burstable_instance(instance_type)
            assert info['is_burstable'] == is_burstable
    
    def test_error_handling_workflow(self):
        """エラーハンドリングワークフローテスト"""
        validator = InstanceTypeValidator()
        
        # 無効なインスタンスタイプでのエラー処理
        invalid_instances = [
            'invalid.type',
            'unknown.medium',
            't3.invalid',
            'xyz.abc'
        ]
        
        for instance_type in invalid_instances:
            # validate_instance_type でのエラー
            with pytest.raises(InvalidValueError):
                validator.validate_instance_type(instance_type)
            
            # validate_and_get_info でのエラー
            with pytest.raises(InvalidValueError):
                validator.validate_and_get_info(instance_type)
            
            # suggest_similar_instance_types は正常動作
            suggestions = validator.suggest_similar_instance_types(instance_type)
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
    
    def test_case_insensitive_handling(self):
        """大文字小文字の処理テスト"""
        validator = InstanceTypeValidator()
        
        # 同じインスタンスタイプの異なる大文字小文字パターン
        variations = ['t3.medium', 'T3.MEDIUM', 'T3.Medium', 't3.MEDIUM']
        
        for variation in variations:
            # すべて正常に検証される
            assert validator.validate_instance_type(variation) is True
            
            # 正規化された情報が取得される
            info = validator.validate_and_get_info(variation)
            assert info['family'] == 't3'
            assert info['size'] == 'medium'
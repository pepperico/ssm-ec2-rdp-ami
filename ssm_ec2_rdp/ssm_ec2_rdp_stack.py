from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnTag,
    Fn
)
from constructs import Construct
from .types import EC2Configuration, ConfigurationError
from .configuration_manager import ConfigurationManager
from .ami_resolver import AMIResolver
from .instance_type_validator import InstanceTypeValidator
from .key_pair_manager import KeyPairManager
from .user_data_manager import UserDataManager

class SsmEc2RdpStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, 
                 config: EC2Configuration,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 各マネージャーコンポーネントを初期化
        try:
            ami_resolver = AMIResolver(self)
            instance_validator = InstanceTypeValidator()
            key_pair_manager = KeyPairManager(self)
            user_data_manager = UserDataManager()
            
            # 設定の検証
            instance_validator.validate_instance_type(config.instance.instance_type)
            
            # AMI解決 - 設定されたAMI IDを直接使用
            machine_image, ami_info = ami_resolver.resolve_ami(config.ami)
            
            # ユーザーデータ生成
            user_data = user_data_manager.generate_user_data(ami_info)
            
        except ConfigurationError as e:
            # 設定エラーをユーザーに分かりやすく表示
            error_msg = f"設定エラーが発生しました: {str(e)}"
            raise ConfigurationError(error_msg) from e
        except Exception as e:
            # 予期しないエラー
            error_msg = f"スタック作成中に予期しないエラーが発生しました: {str(e)}"
            raise ConfigurationError(error_msg) from e

        # VPCの作成
        vpc = ec2.Vpc(
            self, "SsmEc2RdpVpc",
            max_azs=2,  # 2つのAZを使用
            nat_gateways=0,  # NAT Gatewayは不要（SSM経由でアクセス）
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    name="PrivateIsolated",
                    cidr_mask=24
                )
            ]
        )

        # セキュリティグループの作成
        security_group = ec2.SecurityGroup(
            self, "SsmEc2RdpSecurityGroup",
            vpc=vpc,
            description="Security group for SSM EC2 RDP access",
            allow_all_outbound=True
        )

        # HTTPSアウトバウンドトラフィックを許可（SSM通信用）
        security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS outbound for SSM"
        )

        # EC2インスタンス用のIAMロールの作成
        ec2_role = iam.Role(
            self, "SsmEc2RdpRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="IAM role for SSM EC2 RDP instance"
        )

        # SSM Session Managerアクセスのポリシーを追加
        ec2_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )
        
        # IAM Instance Profileの作成
        instance_profile = iam.CfnInstanceProfile(
            self, "SsmEc2RdpInstanceProfile",
            roles=[ec2_role.role_name]
        )


        # インスタンスタイプを文字列から直接作成
        # EC2.InstanceTypeにはオーバーロードされたコンストラクタがあり、文字列を直接受け取れる
        instance_type = ec2.InstanceType(config.instance.instance_type)

        # サブネットタイプに応じたサブネット選択
        subnet_type_enum = (
            ec2.SubnetType.PUBLIC if config.instance.subnet_type == "public"
            else ec2.SubnetType.PRIVATE_ISOLATED
        )
        selected_subnets = vpc.select_subnets(subnet_type=subnet_type_enum).subnet_ids

        # EC2インスタンス作成（CfnInstanceを使用してAMI IDを直接指定）
        # パブリックサブネット選択時はパブリックIPを自動割り当て
        if config.instance.subnet_type == "public":
            # パブリックサブネット: NetworkInterfacesでパブリックIP自動割り当て設定
            cfn_instance = ec2.CfnInstance(
                self, "SsmEc2RdpInstance",
                image_id=config.ami.ami_id if config.ami.ami_id else "ami-020d982eb32b97ffc",
                instance_type=config.instance.instance_type,
                key_name=config.instance.key_pair_name if config.instance.key_pair_name else None,
                iam_instance_profile=instance_profile.ref,
                user_data=Fn.base64(user_data.render()) if user_data else None,
                network_interfaces=[
                    ec2.CfnInstance.NetworkInterfaceProperty(
                        device_index="0",
                        associate_public_ip_address=True,  # パブリックIP自動割り当て
                        subnet_id=selected_subnets[0],
                        group_set=[security_group.security_group_id]
                    )
                ],
                tags=[
                    CfnTag(key="Name", value="SSM EC2 RDP Instance")
                ]
            )
        else:
            # プライベートサブネット: 従来通りの設定
            cfn_instance = ec2.CfnInstance(
                self, "SsmEc2RdpInstance",
                image_id=config.ami.ami_id if config.ami.ami_id else "ami-020d982eb32b97ffc",
                instance_type=config.instance.instance_type,
                key_name=config.instance.key_pair_name if config.instance.key_pair_name else None,
                subnet_id=selected_subnets[0],
                security_group_ids=[security_group.security_group_id],
                iam_instance_profile=instance_profile.ref,
                user_data=Fn.base64(user_data.render()) if user_data else None,
                tags=[
                    CfnTag(key="Name", value="SSM EC2 RDP Instance")
                ]
            )

        # VPCエンドポイントの作成（プライベートサブネットからSSMサービスへのアクセス用）
        vpc.add_interface_endpoint(
            "SsmVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SSM,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        vpc.add_interface_endpoint(
            "SsmMessagesVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )


        # EC2 Instance Connect Endpoint用のセキュリティグループ
        eice_security_group = ec2.SecurityGroup(
            self, "EiceSecurityGroup",
            vpc=vpc,
            description="Security group for EC2 Instance Connect Endpoint",
            allow_all_outbound=True
        )

        # EICEからEC2インスタンスへのRDPアクセスを許可
        security_group.add_ingress_rule(
            peer=ec2.Peer.security_group_id(eice_security_group.security_group_id),
            connection=ec2.Port.tcp(3389),
            description="RDP access from EC2 Instance Connect Endpoint"
        )

        # EC2 Instance Connect Endpointの作成
        ec2.CfnInstanceConnectEndpoint(
            self, "InstanceConnectEndpoint",
            subnet_id=vpc.isolated_subnets[0].subnet_id,
            security_group_ids=[eice_security_group.security_group_id],
            preserve_client_ip=False,  # クライアントIPを保持しない（推奨）
            tags=[
                {"key": "Name", "value": "EICE-for-RDP"},
                {"key": "Description", "value": "EC2 Instance Connect Endpoint for RDP access"}
            ]
        )

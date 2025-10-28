#!/usr/bin/env python3
"""
快速启动脚本
Quick Start Script
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {sys.version}")
    return True

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def setup_directories():
    """创建必要目录"""
    directories = ["logs", "exchanges"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}")
    
    # 创建 __init__.py 文件
    init_file = Path("exchanges/__init__.py")
    if not init_file.exists():
        init_file.touch()
        print("✅ 创建 exchanges/__init__.py")

def create_env_file():
    """创建环境变量文件"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# 交易机器人环境变量配置
# Trading Bot Environment Variables Configuration

# 币安交易所API配置
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# OKX交易所API配置
OKX_API_KEY=your_okx_api_key_here
OKX_API_SECRET=your_okx_api_secret_here
OKX_PASSPHRASE=your_okx_passphrase_here

# 其他配置
TRADING_ENABLED=true
SANDBOX_MODE=true
"""
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ 创建 .env 文件")
    else:
        print("✅ .env 文件已存在")

def show_next_steps():
    """显示后续步骤"""
    print("\n" + "=" * 60)
    print("🎉 安装完成！")
    print("=" * 60)
    print("\n📋 后续步骤:")
    print("1. 编辑 .env 文件，填入您的交易所API密钥")
    print("2. 根据需要修改 config.yaml 配置文件")
    print("3. 运行测试: python test_bot.py")
    print("4. 启动机器人: python main.py --dry-run")
    print("\n⚠️  重要提醒:")
    print("- 建议先在测试环境(sandbox)中运行")
    print("- 不要投入过多资金，从小额开始")
    print("- 定期检查机器人运行状态")
    print("\n📖 更多信息请查看 README.md")

def main():
    """主函数"""
    print("🚀 自动交易机器人快速安装")
    print("=" * 40)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 安装依赖
    if not install_dependencies():
        return 1
    
    # 创建目录
    setup_directories()
    
    # 创建环境变量文件
    create_env_file()
    
    # 显示后续步骤
    show_next_steps()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 安装被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安装过程中出现错误: {e}")
        sys.exit(1)

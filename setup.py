#!/usr/bin/env python3
"""Setup script to initialize the Fitness Tracker application."""
import sys
import subprocess
import os


def check_python_version():
    """Check if Python version is 3.10 or higher."""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def install_dependencies():
    """Install required Python packages."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    if os.path.exists(".env"):
        print("\n✅ .env file already exists")
        return True
    
    if os.path.exists(".env.example"):
        print("\n📝 Creating .env file from .env.example...")
        try:
            with open(".env.example", "r") as src:
                content = src.read()
            with open(".env", "w") as dst:
                dst.write(content)
            print("✅ .env file created successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("⚠️ .env.example not found, skipping .env creation")
        return True


def check_docker():
    """Check if Docker and Docker Compose are available."""
    print("\n🐋 Checking Docker availability...")
    try:
        subprocess.check_output(["docker", "--version"], stderr=subprocess.STDOUT)
        print("✅ Docker is available")
        try:
            subprocess.check_output(["docker-compose", "--version"], stderr=subprocess.STDOUT)
            print("✅ Docker Compose is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ Docker Compose not found (optional)")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Docker not found (optional for local development)")
        return False


def main():
    """Run setup steps."""
    print("=" * 60)
    print("🏋️ Fitness Tracker - Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment file
    setup_env_file()
    
    # Check Docker
    has_docker = check_docker()
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("=" * 60)
    
    print("\n📚 Next steps:")
    if has_docker:
        print("\n1. Start services with Docker:")
        print("   docker-compose up -d")
        print("\n2. Run CLI commands:")
        print("   docker-compose exec app python -m cli.main --help")
    else:
        print("\n1. Ensure MongoDB and Redis are running locally")
        print("\n2. Run the CLI:")
        print("   python -m cli.main --help")
    
    print("\n3. Example command:")
    print("   python -m cli.main register --username john --email john@example.com")
    print("\n4. View help for any command:")
    print("   python -m cli.main <command> --help")
    print("\n5. Run tests:")
    print("   pytest tests/ -v")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

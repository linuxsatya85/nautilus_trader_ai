#!/usr/bin/env python3
"""Fix the installer verification function"""

# Read the original installer
with open('install.py', 'r') as f:
    content = f.read()

# Replace the problematic verification function
old_function = '''def verify_installation():
    """Verify the installation."""
    print_step("✅", "Verifying installation...")
    
    python_cmd = get_python_command()
    
    # Test import
    test_script = """
import ai_nautilus_trader
print("✅ Package import successful")
print(f"✅ Version: {ai_nautilus_trader.get_version()}")

# Check installation
ai_nautilus_trader.check_installation()
"""
    
    result = run_command(
        f'{python_cmd} -c "{test_script}"',
        capture_output=True
    )
    
    if result.returncode == 0:
        print_success("Installation verification passed")
        print(result.stdout)
    else:
        print_error("Installation verification failed")
        print(result.stderr)
        return False
    
    return True'''

new_function = '''def verify_installation():
    """Verify the installation."""
    print_step("✅", "Verifying installation...")
    
    python_cmd = get_python_command()
    
    # Test basic import first
    print(f"Running: {python_cmd} -c \\"import ai_nautilus_trader; print('✅ Package import successful'); print(f'✅ Version: {{ai_nautilus_trader.get_version()}}')\\""")
    result = run_command(
        f'{python_cmd} -c "import ai_nautilus_trader; print(\'✅ Package import successful\'); print(f\'✅ Version: {{ai_nautilus_trader.get_version()}}\')"',
        capture_output=True
    )
    
    if result.returncode != 0:
        print_error("❌ Package import failed")
        print(result.stderr)
        return False
    
    print(result.stdout)
    
    # Test installation check
    print(f"Running: {python_cmd} -c \\"import ai_nautilus_trader; ai_nautilus_trader.check_installation()\\""")
    result = run_command(
        f'{python_cmd} -c "import ai_nautilus_trader; ai_nautilus_trader.check_installation()"',
        capture_output=True
    )
    
    if result.returncode == 0:
        print_success("✅ Installation verification passed")
        print(result.stdout)
    else:
        print_error("❌ Installation verification failed")
        print(result.stderr)
        return False
    
    return True'''

# Replace the function
fixed_content = content.replace(old_function, new_function)

# Write the fixed installer
with open('install.py', 'w') as f:
    f.write(fixed_content)

print("✅ Installer verification function fixed!")

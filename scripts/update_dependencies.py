import re
import subprocess

# Regular expression pattern to match package names
pattern = r'([^\s<>=~]+)'

# Read existing requirements.txt and store package names in a set
with open('requirements.txt', 'r') as f:
    reqs = {re.match(pattern, line.strip()).group(1).lower().replace("_", "-") for line in f if re.match(pattern, line.strip())}

# Run pip freeze to get currently installed packages
installed_packages = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
installed_packages = installed_packages.stdout.splitlines()

new = []
# Update reqs set with currently installed packages
for line in installed_packages:
    package_name = re.match(pattern, line).group(1)
    if package_name.lower().replace("_", "-") in reqs:
        new.append(line)

# Write updated requirements.txt file
with open('requirements_updated.txt', 'w') as f:
    for package_name in sorted(new):  # Sort the package names alphabetically
        f.write(f"{package_name}\n")

# Optionally, overwrite original requirements.txt with the updated one
import os
os.rename('requirements_updated.txt', 'requirements.txt')

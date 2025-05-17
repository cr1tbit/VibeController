from flask import Flask, jsonify, send_from_directory
import os
import re
import glob

app = Flask(__name__)

def generate_fullimage_manifest(version):
    """Generate manifest JSON for a full image version."""
    return {
        "name": "AntController-fullimage",
        "version": f"v{version}",
        "new_install_skip_erase": True,
        "builds": [
            {
                "chipFamily": "ESP32",
                "parts": [
                    {
                        "path": f"fw/{version}/fullimage.bin",
                        "offset": 0
                    }
                ]
            }
        ]
    }

def generate_fwonly_manifest(version):
    """Generate manifest JSON for firmware-only version."""
    return {
        "name": "AntController-fw",
        "version": f"v{version}",
        "new_install_skip_erase": True,
        "builds": [
            {
                "chipFamily": "ESP32",
                "parts": [
                    {
                        "path": f"fw/{version}/firmware.bin",
                        "offset": 65536
                    }
                ]
            }
        ]
    }

def generate_filesystem_manifest(version):
    """Generate manifest JSON for filesystem-only version."""
    return {
        "name": "AntController-filesystem",
        "version": f"v{version}",
        "new_install_skip_erase": True,
        "builds": [
            {
                "chipFamily": "ESP32",
                "parts": [
                    {
                        "path": f"fw/{version}/filesystem.bin",
                        "offset": 3211264
                    }
                ]
            }
        ]
    }

def check_firmware_exists(version, firmware_type):
    """Check if a specific firmware file exists."""
    if firmware_type == 'fullimage':
        return os.path.exists(os.path.join('fw', version, 'fullimage.bin'))
    elif firmware_type == 'fwonly':
        return os.path.exists(os.path.join('fw', version, 'firmware.bin'))
    elif firmware_type == 'filesystem':
        return os.path.exists(os.path.join('fw', version, 'filesystem.bin'))
    return False

def read_readme_for_version(version):
    """Reads the readme.md file for a specific version if it exists."""
    readme_path = os.path.join('fw', version, 'readme.md')
    if os.path.exists(readme_path):
        try:
            with open(readme_path, 'r') as f:
                # Read only a limited number of lines to avoid large files
                # Or read entirely if preferred, but let's limit for now.
                # For simplicity, reading the first few lines or whole file if small.
                # Let's read the whole file for now, assuming readmes are short.
                content = f.read()
                return content
        except Exception as e:
            print(f"Error reading readme for version {version}: {e}")
            return None
    return None

def get_available_manifests():
    """Get a list of all available firmware versions and their types."""
    if not os.path.exists('fw'):
        print("Debug: 'fw' directory not found.")
        return []
    
    version_data = []
    print(f"Debug: Scanning directories in 'fw': {os.listdir('fw')}")
    for version_dir in os.listdir('fw'):
        version_path = os.path.join('fw', version_dir)
        if not os.path.isdir(version_path):
            print(f"Debug: Skipping non-directory item: {version_dir}")
            continue
            
        # Find the latest modification time for this version based on a .bin file
        bin_files = glob.glob(os.path.join(version_path, '*.bin'))
        latest_mtime = 0
        print(f"Debug: Checking bin files for version {version_dir}: {bin_files}")
        if bin_files:
            try:
                # Get the modification time of the first found .bin file
                # We could iterate through all to find truly latest, but first one is simpler.
                latest_mtime = os.path.getmtime(bin_files[0])
                print(f"Debug: Latest mtime for {version_dir} (from {bin_files[0]}): {latest_mtime}")
            except Exception as e:
                print(f"Error getting modification time for {bin_files[0]}: {e}")

        # Read readme content
        readme_content = read_readme_for_version(version_dir)
        
        # Collect available manifests for this version
        manifests_list = []
        print(f"Debug: Collecting manifests for version: {version_dir}")
        for firmware_type in ['fullimage', 'fwonly', 'filesystem']:
            if check_firmware_exists(version_dir, firmware_type):
                manifests_list.append({
                    'type': firmware_type,
                    'url': f'/antctrl/manifest-{version_dir}-{firmware_type}.json'
                })
                print(f"Debug: Found manifest for {version_dir}-{firmware_type}")
            else:
                print(f"Debug: No manifest found for {version_dir}-{firmware_type}")

        # Only include this version if there's at least one manifest
        if manifests_list:
            version_data.append({
                'version': version_dir,
                'manifests': manifests_list,
                'readme': readme_content,
                'latest_mtime': latest_mtime
            })
            print(f"Debug: Added version {version_dir} to version_data.")
        else:
            print(f"Debug: No manifests found for version {version_dir}, skipping.")
            pass # Skip versions with no manifests
    
    # Sort by latest modification time in descending order
    print("Debug: Sorting version_data by latest modification time.")
    version_data.sort(key=lambda x: x.get('latest_mtime', 0), reverse=True)
    
    print(f"Debug: Final version_data being returned: {version_data}")
    return version_data

@app.route('/manifest-<version>-<type>.json')
def get_manifest(version, type):
    # Determine which manifest type to generate
    if type == 'fullimage':
        manifest = generate_fullimage_manifest(version)
        firmware_path = os.path.join('fw', version, 'fullimage.bin')
    elif type == 'fwonly':
        manifest = generate_fwonly_manifest(version)
        firmware_path = os.path.join('fw', version, 'firmware.bin')
    elif type == 'filesystem':
        manifest = generate_filesystem_manifest(version)
        firmware_path = os.path.join('fw', version, 'filesystem.bin')
    else:
        return jsonify({"error": "Invalid manifest type"}), 400
    
    # Check if firmware file exists
    if not os.path.exists(firmware_path):
        return jsonify({"error": "Firmware not found"}), 404
    
    return jsonify(manifest)

@app.route('/manifests')
def list_manifests():
    """List all available manifest files."""
    available_manifests = get_available_manifests()
    return jsonify({
        'available_manifests': available_manifests
    })

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'index.html')

@app.route('/fw/<version>/<filename>')
def serve_firmware(version, filename):
    """Serve firmware files from the fw directory."""
    # Validate filename to prevent directory traversal
    if not re.match(r'^(fullimage|firmware|filesystem)\.bin$', filename):
        return jsonify({"error": "Invalid filename"}), 400
    
    # Check if the firmware file exists
    firmware_path = os.path.join('fw', version, filename)
    if not os.path.exists(firmware_path):
        return jsonify({"error": "Firmware not found"}), 404
    
    # Serve the file
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'fw', version), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 
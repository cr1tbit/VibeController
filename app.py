from flask import Flask, jsonify, send_from_directory
import os
import re

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

def get_available_manifests():
    """Get a list of all available firmware versions and their types."""
    if not os.path.exists('fw'):
        return []
    
    available_manifests = []
    for version_dir in os.listdir('fw'):
        if not os.path.isdir(os.path.join('fw', version_dir)):
            continue
            
        # Check each firmware type
        for firmware_type in ['fullimage', 'fwonly', 'filesystem']:
            if check_firmware_exists(version_dir, firmware_type):
                available_manifests.append({
                    'version': version_dir,
                    'type': firmware_type,
                    'url': f'/antctrl/manifest-{version_dir}-{firmware_type}.json'
                })
    
    return available_manifests

@app.route('/manifest-<version>-<type>.json')
def get_manifest(version, type):
    # Validate version format (should be numbers only)
    if not re.match(r'^\d+$', version):
        return jsonify({"error": "Invalid version format"}), 400
    
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
    # Validate version format (should be numbers only)
    if not re.match(r'^\d+$', version):
        return jsonify({"error": "Invalid version format"}), 400
    
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
    app.run(debug=False) 
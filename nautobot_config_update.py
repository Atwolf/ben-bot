#!/usr/bin/env python3
import re

# Read current configuration
with open('current_nautobot_config.py', 'r') as f:
    config_content = f.read()

# Find the PLUGINS list and add our plugin
plugins_pattern = r'PLUGINS = \[(.*?)\]'
plugins_match = re.search(plugins_pattern, config_content, re.DOTALL)

if plugins_match:
    current_plugins = plugins_match.group(1)
    # Add our chatbot plugin to the list
    new_plugins = current_plugins.rstrip() + ',\n    "nautobot_chatbot",\n'
    
    # Replace the PLUGINS list
    new_config = re.sub(plugins_pattern, f'PLUGINS = [{new_plugins}]', config_content, flags=re.DOTALL)
    
    # Add our plugin configuration
    plugins_config_pattern = r'PLUGINS_CONFIG = \{(.*?)\}'
    plugins_config_match = re.search(plugins_config_pattern, new_config, re.DOTALL)
    
    if plugins_config_match:
        current_config = plugins_config_match.group(1)
        new_plugin_config = '''    "nautobot_chatbot": {
        "enable_chatbot": True,
        "chatbot_title": "Ben Bot Assistant",
        "max_chat_history": 50,
    },'''
        
        new_config_section = current_config.rstrip() + '\n' + new_plugin_config + '\n'
        new_config = re.sub(plugins_config_pattern, f'PLUGINS_CONFIG = {{{new_config_section}}}', new_config, flags=re.DOTALL)
    
    # Write the updated configuration
    with open('updated_nautobot_config.py', 'w') as f:
        f.write(new_config)
    
    print("Configuration updated successfully!")
else:
    print("Could not find PLUGINS list in configuration!")
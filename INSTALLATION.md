# Installation Guide

## Installing the Nautobot Chatbot App

### Method 1: Install from Source (Recommended for local testing)

1. **Clone or copy the app to your system:**
   ```bash
   # If you have the source code locally
   cd /path/to/ben-bot
   ```

2. **Install the app in development mode:**
   ```bash
   pip install -e .
   ```

3. **Configure Nautobot to use the app:**
   
   Edit your `nautobot_config.py` file (usually located in `/opt/nautobot/nautobot_config.py` or similar):
   
   ```python
   PLUGINS = [
       "nautobot_chatbot",
       # ... your other apps/plugins
   ]
   
   # Optional configuration
   PLUGINS_CONFIG = {
       "nautobot_chatbot": {
           "enable_chatbot": True,
           "chatbot_title": "Ben Bot Assistant",
           "max_chat_history": 50,
       }
   }
   ```

4. **Run database migrations:**
   ```bash
   nautobot-server migrate
   ```

5. **Collect static files:**
   ```bash
   nautobot-server collectstatic --noinput
   ```

6. **Restart your Nautobot service:**
   ```bash
   # If using systemd
   sudo systemctl restart nautobot
   sudo systemctl restart nautobot-worker
   
   # Or if running in development
   nautobot-server runserver
   ```

### Method 2: Install as Package

If you have built a wheel package:

```bash
pip install nautobot-chatbot-1.0.0-py3-none-any.whl
```

Then follow steps 3-6 from Method 1.

## Verification

1. **Check that the app is loaded:**
   ```bash
   nautobot-server shell -c "from django.apps import apps; print([app.name for app in apps.get_app_configs() if 'chatbot' in app.name])"
   ```

2. **Access your Nautobot instance:**
   - Open your browser to `http://localhost:8080` (or your Nautobot URL)
   - Log in with your credentials
   - You should see a floating chat icon in the bottom-right corner
   - You should also see "Chatbot" in the main navigation menu

## Troubleshooting

### Common Issues:

1. **App not appearing in navigation:**
   - Ensure the app is in your `PLUGINS` list
   - Restart the Nautobot service
   - Check the logs for any errors

2. **Static files not loading:**
   - Run `nautobot-server collectstatic --noinput`
   - Ensure your web server can serve static files

3. **Database errors:**
   - Make sure you ran the migrations: `nautobot-server migrate`

4. **Chat overlay not appearing:**
   - Check browser console for JavaScript errors
   - Ensure you're logged in as an authenticated user
   - Verify the middleware is configured correctly

### Log Locations:
- Check Nautobot logs (usually in `/opt/nautobot/logs/` or similar)
- Check your web server logs (nginx, Apache, etc.)

### Debug Mode:
For development, you can enable debug mode in your `nautobot_config.py`:
```python
DEBUG = True
```

Note: Never use DEBUG=True in production!
"""
Shared Resources Module
Contains shared objects like locks that need to be accessed across multiple modules
"""
import threading

# Global lock for config file access
config_lock = threading.Lock()

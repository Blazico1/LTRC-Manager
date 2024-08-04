def load_settings():
    try:
        # Open the settings file
        with open("settings.txt", "r") as file:
            settings = file.readlines()
            
        # Create a dictionary to store the settings
        settings_dict = {}
        
        # Loop through the settings
        for setting in settings:
            # Split the setting into a key and a value
            key, value = setting.split("=")
            
            # Add the setting to the dictionary
            settings_dict[key] = value.strip()
            
        return settings_dict
    
    except FileNotFoundError:
        print("Error: Settings file not found.")
        return {}

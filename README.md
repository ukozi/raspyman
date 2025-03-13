# Raspyman

A modern administration interface for the Retro Aim Server (RAS). This application provides a clean web-based UI for managing user accounts, chat rooms, and directory services on RAS instances.

## Features

- User management (create, suspend, delete users)
- Session monitoring and management
- Chat room administration
- Directory service configuration (categories and keywords)
- Responsive design for desktop and mobile

## Requirements

- Python 3.7 or higher
- [Rio](https://rio.dev/) framework
- HTTPX for API communication

## Installation

1. Clone this repository
2. Create and activate a virtual environment:

```bash
# Create a virtual environment
python -m venv env

# Activate the virtual environment
# On Windows:
env\Scripts\activate
# On macOS/Linux:
source env/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the application with:

```bash
rio run
```

Once the application is running, open your browser and navigate to:

```
http://localhost:8000
```

The Rio framework will display the URL in the terminal output. If port 8000 is already in use, Rio may choose a different port.

By default, the application will connect to a RAS instance at http://localhost:5000. 
You can change the API URL in the settings page after launching the application.

## Development

This project is built with [Rio](https://rio.dev/), a Python framework for building web applications.

## Acknowledgements

Special thanks to the [Retro AIM Server](https://github.com/mk6i/retro-aim-server) project for providing the backend service that makes this administration interface possible.

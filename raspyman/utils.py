from __future__ import annotations

import typing as t
from pathlib import Path
import logging

import httpx
import json
import rio

from . import data_models

# Set up logging
logger = logging.getLogger("raspyman")

# Directory constants
ROOT_DIR = Path(__file__).parent
ASSETS_DIR = ROOT_DIR / "assets"

# API utilities
async def fetch_from_api(session_obj, api_url, endpoint):
    """Fetch data from the RAS API."""
    url = f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            settings = session_obj[data_models.RasApiSettings]
            if not settings.api_url:
                logger.warning("No API URL configured")
                return None
                
            response = await client.get(url)
            response.raise_for_status()
            
            # Attempt to parse as JSON
            data = response.json()
            return data
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {url}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error: {e} - {url}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)} - {url}")
        return None

async def fetch_active_sessions(session_obj):
    """Fetch the count of active sessions from the RAS API."""
    settings = session_obj[data_models.RasApiSettings]
    
    if not settings.api_url:
        logger.warning("No API URL configured")
        return None
    
    try:
        # Use the same endpoint as fetch_sessions
        data = await fetch_from_api(session_obj, settings.api_url, "/session")
        
        if data is None:
            return None
            
        # If we get a dictionary with a sessions list
        if isinstance(data, dict) and "sessions" in data:
            return len(data["sessions"])
        # If we get a list directly (different API format)
        elif isinstance(data, list):
            return len(data)
        # If we get a dictionary with a count field directly
        elif isinstance(data, dict) and "count" in data:
            return data["count"]
        # If it's a direct integer
        elif isinstance(data, int):
            return data
        else:
            # Unexpected format but not an error
            logger.warning(f"Unexpected data format from sessions endpoint: {type(data)}")
            return 0
    except Exception as e:
        logger.error(f"Error fetching active sessions count: {e}")
        return None

async def fetch_sessions(session_obj):
    """
    Fetch all active sessions from the RAS API.
    
    Returns a list of Session objects or None if there was an error.
    """
    settings = session_obj[data_models.RasApiSettings]
    
    if not settings.api_url:
        logger.warning("No API URL configured")
        return None
        
    data = await fetch_from_api(session_obj, settings.api_url, "/session")
    if data is not None:
        if isinstance(data, dict) and "sessions" in data:
            # Convert the API response to Session objects
            return [data_models.Session(
                id=session.get("id", ""),
                screen_name=session.get("screen_name", ""),
                online_seconds=session.get("online_seconds", 0),
                away_message=session.get("away_message", ""),
                idle_seconds=session.get("idle_seconds", 0),
                is_icq=session.get("is_icq", False),
                remote_addr=session.get("remote_addr", ""),
                remote_port=session.get("remote_port", 0),
            ) for session in data["sessions"]]
        # If data is a valid response but doesn't have the expected format,
        # return an empty list to indicate no sessions rather than an error
        if isinstance(data, dict) or isinstance(data, list):
            return []
    return None

async def kick_session(session_obj, session_id):
    """Kick an active session."""
    settings = session_obj[data_models.RasApiSettings]
    
    if not settings.api_url:
        logger.warning("No API URL configured")
        return False
    
    # NOTE: This feature is not available in all versions of RAS
    # It's kept as a placeholder for future compatibility
    logger.info(f"Kick session feature not available in this RAS version for session ID: {session_id}")
    return False

async def fetch_chat_rooms(session_obj):
    """Fetch the list of chat rooms from the RAS API."""
    settings = session_obj[data_models.RasApiSettings]
    
    if not settings.api_url:
        logger.warning("No API URL configured")
        return None
    
    try:
        # Get public chat rooms according to the RAS API spec
        url = f"{settings.api_url.rstrip('/')}/chat/room/public"
        
        async with httpx.AsyncClient(timeout=3.5) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Parse the response as JSON
            data = response.json()
            
            # Check if the data is a list
            if isinstance(data, list):
                # Convert the API response to ChatRoom objects
                chat_rooms = []
                for room in data:
                    # Create a data_models.ChatRoom object
                    chat_room = data_models.ChatRoom(
                        name=room.get("name", ""),
                        create_time=room.get("create_time", ""),
                        participants=room.get("participants", []),
                    )
                    chat_rooms.append(chat_room)
                return chat_rooms
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                return []
                
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching chat rooms: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error fetching chat rooms: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching chat rooms: {e}")
        return None

async def create_chat_room(session_obj, room_name):
    """
    Create a new chat room in the RAS API.
    
    Returns True if successful, False otherwise.
    """
    settings = session_obj[data_models.RasApiSettings]
    
    if not settings.api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{settings.api_url.rstrip('/')}/chat/room/public"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url, 
                json={"name": room_name}
            )
            response.raise_for_status()
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error creating chat room at {url}: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error creating chat room at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating chat room at {url}: {e}")
        return False

async def delete_chat_room(session_obj, room_name):
    """
    Delete a chat room from the RAS API.
    
    Returns True if successful, False otherwise.
    """
    settings = session_obj[data_models.RasApiSettings]
    
    if not settings.api_url:
        logger.warning("No API URL configured")
        return False
        
    # According to the API spec, there's no dedicated endpoint for deleting chat rooms
    # We'll need to implement this based on the actual API design
    # For now, use the expected URL pattern for consistency with the rest of the API
    url = f"{settings.api_url.rstrip('/')}/chat/room/public/{room_name}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url)
            # Note: 204 means success but no content
            return response.status_code in (200, 204)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error deleting chat room at {url}: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error deleting chat room at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting chat room at {url}: {e}")
        return False

async def fetch_directory_categories(session_obj):
    """
    Fetch all directory categories from the RAS API.
    
    Returns a list of Category objects or None if there was an error.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return None
        
    try:
        # Get categories according to the RAS API spec
        url = f"{api_url.rstrip('/')}/directory/category"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                # Convert the API response to Category objects
                return [data_models.Category(
                    id=category.get("id", 0),
                    name=category.get("name", ""),
                ) for category in data]
            return []
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching categories: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error fetching categories: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching categories: {e}")
        return None

async def create_directory_category(session_obj, category_name):
    """
    Create a new directory category in the RAS API.
    
    Returns True if successful, False otherwise.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{api_url.rstrip('/')}/directory/category"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url, 
                json={"name": category_name}
            )
            response.raise_for_status()
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error creating category at {url}: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error creating category at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating category at {url}: {e}")
        return False

async def delete_directory_category(session_obj, category_id):
    """
    Delete a directory category from the RAS API.
    
    Returns True if successful, False otherwise.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{api_url.rstrip('/')}/directory/category/{category_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url)
            # Note: 204 means success but no content
            return response.status_code in (200, 204)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error deleting category at {url}: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error deleting category at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting category at {url}: {e}")
        return False

async def fetch_directory_keywords(session_obj, category_id=None):
    """
    Fetch directory keywords from the RAS API.
    
    If category_id is provided, fetches keywords for that category,
    otherwise fetches all keywords across all categories.
    
    Returns a list of Keyword objects or None if there was an error.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return None
    
    try:
        # Start with an empty list to collect keywords
        all_keywords = []
        
        # First try the special "all keywords" endpoint - category ID 0
        if category_id is None:
            url = f"{api_url.rstrip('/')}/directory/category/0/keyword"
            logger.info(f"Fetching all keywords from special endpoint: {url}")
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    logger.info(f"All keywords response: {data}")
                    if isinstance(data, list):
                        logger.info(f"Found {len(data)} total keywords")
                        all_keywords.extend(data)
                        # If we got keywords, we can return early
                        if all_keywords:
                            # Convert the API response to Keyword objects
                            keywords = []
                            for keyword in all_keywords:
                                # Handle potential format differences between endpoints
                                if isinstance(keyword, dict):
                                    # Use category_id if available, otherwise use parent field for backwards compatibility
                                    category_id_value = keyword.get("category_id", keyword.get("parent", 0))
                                    keywords.append(data_models.Keyword(
                                        id=keyword.get("id", 0),
                                        name=keyword.get("name", ""),
                                        category_id=category_id_value,
                                    ))
                            
                            logger.info(f"Returning {len(keywords)} keywords from all-keywords endpoint")
                            return keywords
            except Exception as e:
                logger.error(f"Error fetching from all-keywords endpoint: {e}")
                # Continue with specific category fetching as fallback
        
        # If a specific category ID is provided, fetch only keywords for that category
        if category_id is not None:
            url = f"{api_url.rstrip('/')}/directory/category/{category_id}/keyword"
            logger.info(f"Fetching keywords for specific category ID: {category_id}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Response for category {category_id}: {data}")
                if isinstance(data, list):
                    # For keywords fetched by category, we know their category_id
                    for item in data:
                        if isinstance(item, dict):
                            # Make sure each item has the category_id
                            item_with_category = item.copy()
                            # Set the category_id if it's not already in the API response
                            # ALWAYS set the category_id for consistency, regardless of whether it's in the API response
                            item_with_category["category_id"] = category_id
                            all_keywords.append(item_with_category)
                            logger.info(f"Added keyword '{item_with_category.get('name')}' with forced category_id {category_id}")
        else:
            # Otherwise, we need to first get all categories
            categories = await fetch_directory_categories(session_obj)
            if categories:
                logger.info(f"Found {len(categories)} categories, fetching keywords for each")
                # For each category, fetch its keywords
                for category in categories:
                    url = f"{api_url.rstrip('/')}/directory/category/{category.id}/keyword"
                    logger.info(f"Fetching keywords for category {category.id} ({category.name})")
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.get(url)
                            response.raise_for_status()
                            data = response.json()
                            logger.info(f"API response for category {category.id}: {data}")
                            if isinstance(data, list):
                                logger.info(f"Adding {len(data)} keywords from category {category.id}")
                                # Add the category ID to each keyword
                                for item in data:
                                    if isinstance(item, dict):
                                        item_with_category = item.copy()
                                        # Set the category_id if it's not already in the API response
                                        # ALWAYS set the category_id for consistency, regardless of whether it's in the API response
                                        item_with_category["category_id"] = category.id
                                        all_keywords.append(item_with_category)
                                        logger.info(f"Added keyword '{item_with_category.get('name')}' with forced category_id {category.id}")
                            else:
                                logger.warning(f"Unexpected data format for category {category.id}: {type(data)}")
                    except Exception as e:
                        logger.error(f"Error fetching keywords for category {category.id}: {e}")
                        # Continue with other categories even if one fails
                        continue
            else:
                logger.info("No categories found, cannot fetch keywords")
        
        # Convert the API response to Keyword objects
        keywords = []
        for keyword in all_keywords:
            # Handle potential format differences between endpoints
            if isinstance(keyword, dict):
                # Use category_id if available, otherwise use parent field for backwards compatibility
                category_id_value = keyword.get("category_id", keyword.get("parent", 0))
                keywords.append(data_models.Keyword(
                    id=keyword.get("id", 0),
                    name=keyword.get("name", ""),
                    category_id=category_id_value,
                ))
                logger.info(f"Created Keyword object: id={keyword.get('id', 0)}, name={keyword.get('name', '')}, category_id={category_id_value}")
        
        logger.info(f"Returning {len(keywords)} keywords")
        # Debug the keywords list with category_id
        logger.info(f"Keywords with category IDs: {[(k.name, k.category_id) for k in keywords]}")
        
        return keywords  # Return empty list if no keywords found (not None)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching keywords: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error fetching keywords: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching keywords: {e}")
        return None

async def create_directory_keyword(session_obj, keyword_name, parent_category_id):
    """
    Create a new directory keyword in the RAS API.
    
    Args:
        session_obj: The session object
        keyword_name: The name of the keyword to create
        parent_category_id: The ID of the parent category (renamed to category_id in the API)
    
    Returns:
        True if successful, False otherwise.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{api_url.rstrip('/')}/directory/keyword"
    logger.info(f"Creating keyword '{keyword_name}' with category ID: {parent_category_id}")
    logger.info(f"POST URL: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"Sending request data: {{'name': '{keyword_name}', 'category_id': {parent_category_id}}}")
            response = await client.post(
                url, 
                json={"name": keyword_name, "category_id": parent_category_id}
            )
            response.raise_for_status()
            logger.info(f"Keyword creation response: {response.status_code}")
            if response.text:
                logger.info(f"Response body: {response.text}")
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error creating keyword: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error creating keyword: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating keyword: {e}")
        return False

async def delete_directory_keyword(session_obj, keyword_id):
    """
    Delete a directory keyword from the RAS API.
    
    Returns True if successful, False otherwise.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{api_url.rstrip('/')}/directory/keyword/{keyword_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url)
            # Note: 204 means success but no content
            return response.status_code in (200, 204)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error deleting keyword at {url}: {e.response.status_code}")
        logger.error(f"Response content: {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error deleting keyword at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting keyword at {url}: {e}")
        return False

async def fetch_total_users(session_obj):
    """Fetch total users from the RAS API."""
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return None
        
    data = await fetch_from_api(session_obj, api_url, "/user")
    if data is not None and isinstance(data, list):
        # Now properly handles empty lists by returning 0
        return len(data)
    return None

# User CRUD operations
async def fetch_users(session_obj):
    """
    Fetch all users from the RAS API.
    
    Returns a list of User objects or None if there was an error.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return None
        
    data = await fetch_from_api(session_obj, api_url, "/user")
    # Check if the response is valid (can be an empty list)
    if data is not None:
        if isinstance(data, list):
            # Convert the API response to User objects
            return [data_models.User(
                id=user.get("id", ""),
                screen_name=user.get("screen_name", ""),
                is_icq=user.get("is_icq", False),
                suspended_status=user.get("suspended_status", None),
            ) for user in data]
        else:
            # Invalid response format
            logger.warning(f"Invalid response format when fetching users: {type(data)}")
    return None

async def fetch_user_details(session_obj, screen_name):
    """
    Fetch detailed information for a specific user.
    
    Returns a User object with all available details or None if there was an error.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return None
        
    data = await fetch_from_api(session_obj, api_url, f"/user/{screen_name}/account")
    if data and isinstance(data, dict):
        # Convert the API response to a User object
        return data_models.User(
            id=data.get("id", ""),
            screen_name=data.get("screen_name", ""),
            is_icq=data.get("is_icq", False),
            suspended_status=data.get("suspended_status", None),
            profile=data.get("profile", None),
            email_address=data.get("email_address", None),
            confirmed=data.get("confirmed", False),
        )
    return None

async def create_user(session_obj, screen_name, password):
    """
    Create a new user in the RAS API.
    
    Returns True if successful, False otherwise.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{api_url.rstrip('/')}/user"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url, 
                json={"screen_name": screen_name, "password": password}
            )
            response.raise_for_status()
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error creating user at {url}: {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error creating user at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating user at {url}: {e}")
        return False

async def update_user_status(session_obj, screen_name, suspended_status):
    """
    Update a user's suspended status in the RAS API.
    
    Returns True if successful, False otherwise.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{api_url.rstrip('/')}/user/{screen_name}/account"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.patch(
                url, 
                json={"suspended_status": suspended_status}
            )
            # Raise exception for 4xx/5xx status codes
            response.raise_for_status()
            # Note: 204 means success but no content
            return response.status_code in (200, 204)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error updating user at {url}: {e.response.status_code}")
        try:
            logger.error(f"Response content: {e.response.text}")
        except:
            pass
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error updating user at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating user at {url}: {e}")
        return False

async def delete_user(session_obj, screen_name):
    """
    Delete a user from the RAS API.
    
    Returns True if successful, False otherwise.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{api_url.rstrip('/')}/user"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Use request() method which allows body with DELETE
            response = await client.request(
                "DELETE",
                url,
                json={"screen_name": screen_name}
            )
            # Note: 204 means success but no content
            return response.status_code in (200, 204)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error deleting user at {url}: {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error deleting user at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting user at {url}: {e}")
        return False

async def reset_user_password(session_obj, screen_name, new_password):
    """
    Reset a user's password in the RAS API.
    
    Returns True if successful, False otherwise.
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return False
        
    url = f"{api_url.rstrip('/')}/user/password"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.put(
                url, 
                json={"screen_name": screen_name, "password": new_password}
            )
            # Note: 204 means success but no content
            return response.status_code in (200, 204)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error resetting password at {url}: {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error resetting password at {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error resetting password at {url}: {e}")
        return False

async def direct_kick_user(session_obj, screen_name):
    """
    Stub for directly terminating a user's session in the RAS API by screen name.
    This functionality is not available in the current RAS version.
    
    Args:
        session_obj: The rio session object
        screen_name: The screen name of the user to kick
    
    Always returns False since the feature is not supported.
    """
    logger.info(f"DEBUG: Direct kick user feature not available in this RAS version for user: {screen_name}")
    return False

async def fetch_version_info(session_obj):
    """
    Fetch version information from the RAS API.
    
    Returns a dictionary with version information or None if there was an error.
    The dictionary contains:
    - version: The release version number
    - commit: The latest git commit hash in this build
    - date: The build date and timestamp in RFC3339 format
    """
    api_url = session_obj[data_models.RasApiSettings].api_url
    if not api_url:
        logger.warning("No API URL configured")
        return None
        
    data = await fetch_from_api(session_obj, api_url, "/version")
    if data is not None and isinstance(data, dict):
        # Return the version information dictionary
        return {
            "version": data.get("version", "Unknown"),
            "commit": data.get("commit", "Unknown"),
            "date": data.get("date", "Unknown")
        }
    return None
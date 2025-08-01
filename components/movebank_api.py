"""
Movebank API Client Component
Provides functionality to access and retrieve animal tracking data from Movebank
Adapted from ctmmweb's approach: https://github.com/ctmm-initiative/ctmmweb
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import hashlib
import time
from io import StringIO
import csv


class MoveBank:
    """
    Enhanced Python wrapper for accessing the Movebank API with carnivore-specific functionality.
    Adapted from ctmmweb's approach to ensure proper authentication and data handling.
    """
    
    BASE_URL = "https://www.movebank.org/movebank/service/direct-read"
    
    def __init__(self, username=None, password=None, cache_dir='./data/cache'):
        """
        Initialize the MoveBank API client.
        
        Args:
            username (str, optional): Movebank username for authenticated access.
            password (str, optional): Movebank password for authenticated access.
            cache_dir (str, optional): Directory for caching API responses.
        """
        self.username = username
        self.password = password
        
        # Set up caching directory
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Track studies that require license acceptance
        self.license_required_studies = {}
        self.accepted_licenses = set()
    
    def authenticate(self, username=None, password=None):
        """
        Set or update authentication credentials.
        
        Args:
            username (str): Movebank username
            password (str): Movebank password
            
        Returns:
            bool: True if authentication succeeds, False otherwise
        """
        if username:
            self.username = username
        if password:
            self.password = password
        
        # Test authentication by attempting to list studies
        try:
            result = self._request("study")
            return result['status'] == "Success"
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
            
    def _request(self, entity_type, **params):
        """
        Make a request to Movebank API, following ctmmweb's approach.
        
        Args:
            entity_type (str): Entity type for the request (study, event, etc.)
            **params: Additional parameters for the request
            
        Returns:
            dict: Dictionary with status and response content
        """
        url = f"{self.BASE_URL}?entity_type={entity_type}"
        
        # Add any additional parameters to the URL
        for key, value in params.items():
            url += f"&{key}={value}"
        
        # Use headers for authentication instead of HTTPBasicAuth
        headers = {}
        if self.username and self.password:
            headers['user'] = self.username
            headers['password'] = self.password
            
        # Make the request
        try:
            response = requests.get(url, headers=headers)
            status = "Success" if response.status_code == 200 else "Error"
            
            # Check if the response contains HTML (error message)
            if '<html' in response.text[:100].lower():
                status = "Error"
                print(f"Movebank API error: Response contains HTML instead of data")
                
            return {
                'status': status,
                'res_cont': response.text,
                'response': response
            }
        except Exception as e:
            print(f"Request error: {e}")
            return {'status': 'Error', 'res_cont': str(e), 'response': None}
    
    def get_studies(self, carnivore_only=False, include_private=True):
        """
        Get list of available studies from Movebank.
        
        Args:
            carnivore_only (bool): If True, filter for carnivore studies based on taxon_ids
            include_private (bool): Whether to include private studies (requires login)
            
        Returns:
            pandas.DataFrame: DataFrame containing study information
        """
        cache_key = f"studies_carnivore_{carnivore_only}_private_{include_private}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.csv")
        
        # Check cache first (valid for 24 hours)
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
            try:
                return pd.read_csv(cache_file)
            except Exception as e:
                print(f"Error reading cached studies: {e}")
                # Continue to fetch fresh data
        
        # Make request to get studies
        result = self._request("study")
        
        if result['status'] != "Success":
            print("Failed to retrieve studies from Movebank")
            return pd.DataFrame()
            
        # Parse CSV response
        try:
            df = pd.read_csv(StringIO(result['res_cont']))
            
            # Filter for carnivore studies if requested
            if carnivore_only and 'taxon_ids' in df.columns:
                carnivore_taxa = ['Carnivora', '3700031', 'Felidae', 'Canidae', 'Ursidae', 'Mustelidae',
                                'Mephitidae', 'Procyonidae', 'Viverridae', 'Hyaenidae']
                
                mask = df['taxon_ids'].fillna('').apply(
                    lambda x: any(taxon.lower() in str(x).lower() for taxon in carnivore_taxa)
                )
                df = df[mask]
            
            # Include/exclude private studies
            if 'i_can_see_data' in df.columns:
                if not include_private:
                    df = df[df['i_can_see_data'] == 'true']
            
            # Save to cache
            df.to_csv(cache_file, index=False)
            
            return df
        except Exception as e:
            print(f"Error parsing studies data: {e}")
            return pd.DataFrame()
    
    def get_study_details(self, study_id):
        """
        Get detailed information about a specific study.
        
        Args:
            study_id (int or str): Movebank study ID
            
        Returns:
            dict: Study details or empty dict if retrieval fails
        """
        cache_key = f"study_details_{study_id}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Check cache first
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cached study details: {e}")
                # Continue to fetch fresh data
        
        # Make request to get study details
        result = self._request("study", study_id=study_id)
        
        if result['status'] != "Success":
            print(f"Failed to retrieve study details for study ID {study_id}")
            return {}
        
        try:
            # Parse CSV response to dict
            content = result['res_cont']
            lines = content.strip().split('\n')
            
            if len(lines) < 2:  # Need at least header and one row
                return {}
                
            # Parse CSV properly accounting for quoted fields
            reader = csv.reader(StringIO(content))
            headers = next(reader)
            values = next(reader, [])
            
            # Create dictionary from headers and values
            study_details = {}
            for i, header in enumerate(headers):
                if i < len(values):
                    key = header.strip()
                    study_details[key] = values[i].strip()
            
            # Save to cache
            with open(cache_file, 'w') as f:
                json.dump(study_details, f)
            
            return study_details
        except Exception as e:
            print(f"Error parsing study details: {e}")
            return {}
    
    def check_license_terms(self, study_id):
        """
        Check if a study requires license acceptance.
        
        Args:
            study_id (int or str): Movebank study ID
            
        Returns:
            tuple: (license_required, license_text)
        """
        # Try to get minimal data - if it returns a license text instead of data, we need to accept it
        result = self._request("event", study_id=study_id, attributes="timestamp")
        content = result['res_cont']
        
        # Count commas in first line to determine if it's license text
        first_line = content.split('\n')[0] if content else ""
        comma_count = first_line.count(',')
        
        if comma_count <= 1 and "license terms" in content.lower():
            self.license_required_studies[study_id] = content
            return True, content
        
        return False, ""
    
    def accept_license_terms(self, study_id):
        """
        Mark a study's license terms as accepted.
        
        Args:
            study_id (int): Movebank study ID
            
        Returns:
            bool: Success status
        """
        if study_id not in self.license_required_studies:
            # Check if we need license acceptance first
            license_required, _ = self.check_license_terms(study_id)
            if not license_required:
                return True
        
        self.accepted_licenses.add(study_id)
        return True
    
    def get_individuals(self, study_id):
        """
        Get list of individuals (animals) in a study.
        
        Args:
            study_id (int or str): Movebank study ID
            
        Returns:
            pandas.DataFrame: DataFrame with individual information or empty DataFrame if retrieval fails
        """
        cache_key = f"individuals_{study_id}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.csv")
        
        # Check cache first
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
            try:
                return pd.read_csv(cache_file)
            except Exception as e:
                print(f"Error reading cached individuals data: {e}")
                # Continue to fetch fresh data
        
        # If license required but not accepted, return empty DataFrame
        if study_id in self.license_required_studies and study_id not in self.accepted_licenses:
            print(f"License agreement required for study ID {study_id}")
            return pd.DataFrame()
        
        # Get individual data by requesting a minimal set of tracking data
        result = self._request("event", study_id=study_id, attributes="individual_id,individual_local_identifier")
        
        if result['status'] != "Success":
            print(f"Failed to retrieve individuals for study ID {study_id}")
            return pd.DataFrame()
        
        try:
            # Parse CSV response directly using pandas
            df = pd.read_csv(StringIO(result['res_cont']))
            
            # Get unique individuals
            individuals_df = df[['individual_id', 'individual_local_identifier']].drop_duplicates()
            
            # Save to cache
            individuals_df.to_csv(cache_file, index=False)
            
            return individuals_df
        except Exception as e:
            print(f"Error parsing individuals data: {e}")
            return pd.DataFrame()
    
    def get_tracking_data(self, study_id, individuals=None, start_date=None, end_date=None, attributes="all"):
        """
        Get tracking data for specific individuals within a date range.
        
        Args:
            study_id (int or str): Movebank study ID
            individuals (list): List of individual IDs to include (None for all)
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            attributes (str): Comma-separated list of attributes to retrieve or 'all'
            
        Returns:
            pandas.DataFrame: DataFrame with tracking data or empty DataFrame if retrieval fails
        """
        # Generate cache key based on parameters
        params_str = f"{study_id}_{individuals}_{start_date}_{end_date}_{attributes}"
        cache_key = hashlib.md5(params_str.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"tracking_{cache_key}.csv")
        
        # Check cache first
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
            try:
                return pd.read_csv(cache_file)
            except Exception as e:
                print(f"Error reading cached tracking data: {e}")
                # Continue to fetch fresh data
        
        # Check license acceptance
        if study_id in self.license_required_studies and study_id not in self.accepted_licenses:
            print(f"License agreement required for study ID {study_id}")
            return pd.DataFrame()
            
        # Prepare request parameters
        request_params = {
            "study_id": study_id,
            "attributes": attributes
        }
        
        # Add individuals if specified
        if individuals:
            if isinstance(individuals, list):
                request_params["individual_id"] = ",".join(str(i) for i in individuals)
            else:
                request_params["individual_id"] = str(individuals)
        
        # Add date filters if specified
        if start_date:
            # Format for Movebank: YYYY-MM-DD HH:MM:SS
            if ' ' not in start_date:
                start_date += ' 00:00:00'
            request_params["timestamp_start"] = start_date
        
        if end_date:
            if ' ' not in end_date:
                end_date += ' 23:59:59'
            request_params["timestamp_end"] = end_date
        
        # Make the request
        result = self._request("event", **request_params)
        
        if result['status'] != "Success":
            print(f"Failed to retrieve tracking data for study ID {study_id}")
            return pd.DataFrame()
        
        try:
            # Parse CSV response directly using pandas
            df = pd.read_csv(StringIO(result['res_cont']))
            
            # Convert timestamp to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter out marked outliers if any
            if 'visible' in df.columns:
                df = df[df['visible'] != 'false']
                
            # Save to cache
            df.to_csv(cache_file, index=False)
            return df
        except Exception as e:
            print(f"Error parsing tracking data: {e}")
            return pd.DataFrame()
        
    def get_environmental_data(self, study_id, individuals=None, start_date=None, end_date=None):
        """
        Get environmental data associated with tracking locations.
        
        Args:
            study_id (int or str): Movebank study ID
            individuals (list): List of individual IDs to include (None for all)
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            pandas.DataFrame: DataFrame with environmental data or empty DataFrame if retrieval fails
        """
        # Request environmental variables along with location data
        env_attributes = "timestamp,location_lat,location_long,height_above_ellipsoid,study_specific_measurement"
        
        # Use our improved tracking data method with environmental attributes
        return self.get_tracking_data(study_id, individuals, start_date, end_date, env_attributes)
    # This class now uses the _request method instead of _get_cache_path and _make_request
    
    def search_studies(self, query, include_private=False):
        """
        Search for studies by name or description.
        
        Args:
            query (str): Search query.
            include_private (bool): Whether to include private studies (requires auth).
            
        Returns:
            pandas.DataFrame: DataFrame containing matching studies or empty DataFrame if retrieval fails.
        """
        # Generate cache key based on parameters
        cache_key = f"search_{query}_{include_private}"
        cache_key = hashlib.md5(cache_key.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"search_{cache_key}.csv")
        
        # Check cache first
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
            try:
                return pd.read_csv(cache_file)
            except Exception as e:
                print(f"Error reading cached search results: {e}")
                # Continue to fetch fresh data
        
        # Get all studies first
        result = self._request("study")
        
        if result['status'] != "Success":
            print("Failed to retrieve studies from Movebank")
            return pd.DataFrame()
        
        try:
            # Parse CSV response
            df = pd.read_csv(StringIO(result['res_cont']))
            
            # Filter by search query
            if query and not df.empty:
                query = query.lower()
                mask = df['name'].fillna('').str.lower().str.contains(query) | \
                      df['study_objective'].fillna('').str.lower().str.contains(query)
                df = df[mask]
            
            # Include/exclude private studies
            if not include_private and 'i_can_see_data' in df.columns:
                df = df[df['i_can_see_data'] == 'true']
            
            # Save to cache
            df.to_csv(cache_file, index=False)
            
            return df
        except Exception as e:
            print(f"Error parsing studies data: {e}")
            return pd.DataFrame()
    
    def get_carnivore_studies(self):
        """
        Get a list of carnivore-related studies.
        
        Returns:
            pandas.DataFrame: DataFrame containing carnivore studies or empty DataFrame if retrieval fails.
        """
        # Check for cached results
        cache_file = os.path.join(self.cache_dir, "carnivore_studies.csv")
        
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
            try:
                return pd.read_csv(cache_file)
            except Exception as e:
                print(f"Error reading cached carnivore studies: {e}")
                # Continue to fetch fresh data
        
        # Get studies with carnivore-related taxon IDs
        carnivore_studies = self.get_studies(carnivore_only=True)
        
        # Search for common carnivore terms if we want additional studies
        carnivore_terms = ["carnivore", "predator", "wolf", "lion", "tiger", "bear", "leopard", 
                          "jaguar", "cougar", "puma", "cheetah", "hyena", "fox", "coyote"]
        
        all_studies = [carnivore_studies]
        for term in carnivore_terms:
            studies = self.search_studies(term)
            if not studies.empty:
                all_studies.append(studies)
        
        # Combine results and remove duplicates
        if all_studies:
            try:
                combined_studies = pd.concat(all_studies, ignore_index=True)
                # Remove duplicates based on study ID
                if 'id' in combined_studies.columns:
                    combined_studies = combined_studies.drop_duplicates(subset=["id"])
                
                # Save to cache
                combined_studies.to_csv(cache_file, index=False)
                
                return combined_studies
            except Exception as e:
                print(f"Error combining carnivore studies: {e}")
        
        return pd.DataFrame()
        
    # The get_study_details method has already been implemented above
    # with the ctmmweb-style approach.
        
    def import_movebank_csv(self, file_path, cache_data=True):
        """
        Import tracking data from a CSV file exported from Movebank.
        
        Args:
            file_path (str): Path to the CSV file downloaded from Movebank
            cache_data (bool): Whether to cache the imported data for future use
            
        Returns:
            pandas.DataFrame: DataFrame with tracking data or empty DataFrame if import fails
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return pd.DataFrame()
            
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Basic validation to check if this looks like Movebank data
            required_columns = ['individual_id', 'timestamp', 'location_lat', 'location_long']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"Warning: CSV file is missing expected Movebank columns: {', '.join(missing_columns)}")
                print("This may not be a valid Movebank export or it might be using different column names.")
            
            # Convert timestamp to datetime if present
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter out outliers if marked
            if 'visible' in df.columns:
                df = df[df['visible'] != 'false']
                
            # Determine study name and ID from filename or from data
            study_name = "Imported Data"
            study_id = "imported"
            
            # Try to get study name and ID from the file
            if 'study_id' in df.columns and not df['study_id'].empty:
                study_id = str(df['study_id'].iloc[0])
                
            if 'study_name' in df.columns and not df['study_name'].empty:
                study_name = df['study_name'].iloc[0]
            else:
                # Extract from filename if possible
                base_name = os.path.basename(file_path)
                name_part = os.path.splitext(base_name)[0]
                if name_part:
                    study_name = name_part
            
            # Cache the data if requested
            if cache_data:
                cache_key = hashlib.md5(f"imported_{study_id}_{study_name}".encode()).hexdigest()
                cache_file = os.path.join(self.cache_dir, f"imported_{cache_key}.csv")
                df.to_csv(cache_file, index=False)
                
                # Also create a study info file
                study_info = {
                    'id': study_id,
                    'name': study_name,
                    'source': 'imported',
                    'import_file': file_path,
                    'import_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with open(os.path.join(self.cache_dir, f"imported_study_{cache_key}.json"), 'w') as f:
                    json.dump(study_info, f)
            
            return df
            
        except Exception as e:
            print(f"Error importing Movebank CSV: {e}")
            return pd.DataFrame()
        
    def get_individuals(self, study_id):
        """
        Get individual animals from a study.
        
        Args:
            study_id (int): The study ID to retrieve individuals from.
            
        Returns:
            pandas.DataFrame: DataFrame containing individual animals information.
        """
        params = {
            "entity_type": "individual",
            "study_id": study_id,
            "format": "csv"
        }
        
        response = self._make_request("", params)
        if response:
            try:
                individuals = pd.read_csv(pd.StringIO(response))
                return individuals
            except Exception as e:
                print(f"Error parsing individuals: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
        
    def get_event_data(self, study_id, individual_ids=None, start_time=None, end_time=None,
                      sensor_type=None, attributes=None, force_refresh=False):
        """
        Get event (location) data from a study with enhanced filtering.
        
        Args:
            study_id (int): The study ID to retrieve data from.
            individual_ids (list, optional): List of individual IDs to filter by.
            start_time (datetime, optional): Start time for filtering data.
            end_time (datetime, optional): End time for filtering data.
            sensor_type (str/list, optional): Sensor type(s) to filter by.
            attributes (list, optional): Specific attributes to retrieve.
            force_refresh (bool, optional): If True, bypass cache and fetch fresh data.
            
        Returns:
            pandas.DataFrame: DataFrame containing movement data.
        """
        params = {
            "entity_type": "event",
            "study_id": study_id,
            "format": "csv"
        }
        
        # Add filters if provided
        if individual_ids:
            if isinstance(individual_ids, list):
                params["individual_id"] = ",".join(map(str, individual_ids))
            else:
                params["individual_id"] = str(individual_ids)
                
        if start_time:
            if isinstance(start_time, str):
                params["timestamp_start"] = start_time
            else:
                params["timestamp_start"] = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
            
        if end_time:
            if isinstance(end_time, str):
                params["timestamp_end"] = end_time
            else:
                params["timestamp_end"] = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                
        if sensor_type:
            if isinstance(sensor_type, list):
                params["sensor_type_id"] = ",".join(map(str, sensor_type))
            else:
                params["sensor_type_id"] = str(sensor_type)
                
        if attributes:
            params["attributes"] = ",".join(attributes)
            
        response = self._make_request("", params, force_refresh=force_refresh)
        if response:
            try:
                events = pd.read_csv(pd.StringIO(response))
                
                # Convert timestamp to datetime
                if 'timestamp' in events.columns:
                    events['timestamp'] = pd.to_datetime(events['timestamp'])
                    
                return events
            except Exception as e:
                print(f"Error parsing event data: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
        
    def get_reference_data(self, study_id, sensor_type_id=None):
        """
        Get reference (non-location) data from a study.
        
        Args:
            study_id (int): The study ID to retrieve data from.
            sensor_type_id (int, optional): Sensor type ID to filter by.
            
        Returns:
            pandas.DataFrame: DataFrame containing reference data.
        """
        params = {
            "entity_type": "event",
            "study_id": study_id,
            "format": "csv",
            "event_type": "reference"
        }
        
        if sensor_type_id:
            params["sensor_type_id"] = sensor_type_id
            
        response = self._make_request("", params)
        if response:
            try:
                events = pd.read_csv(pd.StringIO(response))
                return events
            except Exception as e:
                print(f"Error parsing reference data: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
        
    def accept_license_terms(self, study_id):
        """
        Accept the license terms for a study.
        
        Args:
            study_id (int): The study ID to accept license terms for.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.auth:
            print("Authentication required to accept license terms")
            return False
            
        params = {
            "entity_type": "study",
            "study_id": study_id,
            "accept-license": "true"
        }
        
        response = self._make_request("", params)
        return response is not None
    
    def get_deployment_info(self, study_id, individual_id=None):
        """
        Get deployment information for tracking devices.
        
        Args:
            study_id (int): The study ID to retrieve data from.
            individual_id (int, optional): Individual ID to filter by.
            
        Returns:
            pandas.DataFrame: DataFrame containing deployment information.
        """
        params = {
            "entity_type": "deployment",
            "study_id": study_id,
            "format": "csv"
        }
        
        if individual_id:
            params["individual_id"] = individual_id
            
        response = self._make_request("", params)
        if response:
            try:
                deployments = pd.read_csv(pd.StringIO(response))
                return deployments
            except Exception as e:
                print(f"Error parsing deployment info: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
        
    def get_tag_info(self, study_id, tag_id=None):
        """
        Get information about tags/devices used in a study.
        
        Args:
            study_id (int): The study ID to retrieve data from.
            tag_id (int, optional): Tag ID to filter by.
            
        Returns:
            pandas.DataFrame: DataFrame containing tag information.
        """
        params = {
            "entity_type": "tag",
            "study_id": study_id,
            "format": "csv"
        }
        
        if tag_id:
            params["tag_id"] = tag_id
            
        response = self._make_request("", params)
        if response:
            try:
                tags = pd.read_csv(pd.StringIO(response))
                return tags
            except Exception as e:
                print(f"Error parsing tag info: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

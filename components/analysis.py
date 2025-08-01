"""
Analysis Component
Provides functionality for calculating carnivore movement and behavioral metrics
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from scipy.spatial import ConvexHull
from sklearn.neighbors import KernelDensity
from scipy.stats import gaussian_kde
from scipy.spatial.distance import pdist, squareform
import matplotlib.path as mpath
import math
from datetime import datetime, timedelta
import pytz

# Earth radius in meters
EARTH_RADIUS = 6371000


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.
    
    Args:
        lat1, lon1: Coordinates of first point (in decimal degrees)
        lat2, lon2: Coordinates of second point (in decimal degrees)
        
    Returns:
        Distance in meters between the two points
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    # Distance in meters
    distance = EARTH_RADIUS * c
    
    return distance


def calculate_distances(df):
    """
    Calculate distances between consecutive points in a GPS dataframe.
    
    Args:
        df: DataFrame containing GPS points with 'location-lat', 'location-long', and 'timestamp' columns
        
    Returns:
        DataFrame with added 'distance_to_prev' column
    """
    if df.empty or len(df) < 2:
        return df
    
    # Ensure the dataframe is sorted by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Extract coordinates
    lats = df['location-lat'].values
    lons = df['location-long'].values
    
    # Calculate distances (first point has distance 0)
    distances = np.zeros(len(df))
    for i in range(1, len(df)):
        distances[i] = haversine_distance(lats[i-1], lons[i-1], lats[i], lons[i])
    
    # Add distance column
    df_with_dist = df.copy()
    df_with_dist['distance_to_prev'] = distances
    
    return df_with_dist


def calculate_daily_distance(df, by_individual=True):
    """
    Calculate total distance traveled per day for each individual.
    
    Args:
        df: DataFrame containing GPS points with 'location-lat', 'location-long', 
            'timestamp', and 'individual-local-identifier' columns
        by_individual: If True, calculate separately for each individual
        
    Returns:
        DataFrame with daily distances
    """
    if df.empty:
        return pd.DataFrame()
    
    # Ensure the dataframe has a distance column
    if 'distance_to_prev' not in df.columns:
        df = calculate_distances(df)
    
    # Convert timestamp to date
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    # Group by date (and individual if specified) and sum distances
    if by_individual and 'individual-local-identifier' in df.columns:
        daily_distance = df.groupby(['individual-local-identifier', 'date'])['distance_to_prev'].sum().reset_index()
        daily_distance.rename(columns={'distance_to_prev': 'daily_distance'}, inplace=True)
    else:
        daily_distance = df.groupby('date')['distance_to_prev'].sum().reset_index()
        daily_distance.rename(columns={'distance_to_prev': 'daily_distance'}, inplace=True)
    
    return daily_distance


def calculate_net_displacement(df):
    """
    Calculate net squared displacement (NSD) from the first point for each individual.
    
    Args:
        df: DataFrame containing GPS points with 'location-lat', 'location-long', 
            'timestamp', and 'individual-local-identifier' columns
            
    Returns:
        DataFrame with NSD values
    """
    if df.empty:
        return pd.DataFrame()
    
    result_dfs = []
    
    # Process each individual separately if individual ID column exists
    if 'individual-local-identifier' in df.columns:
        for individual, group in df.groupby('individual-local-identifier'):
            if len(group) < 2:
                continue
                
            # Sort by timestamp
            group = group.sort_values('timestamp').reset_index(drop=True)
            
            # Get first point coordinates
            first_lat = group.iloc[0]['location-lat']
            first_lon = group.iloc[0]['location-long']
            
            # Calculate NSD for each point
            nsd_values = []
            for _, row in group.iterrows():
                distance = haversine_distance(first_lat, first_lon, 
                                             row['location-lat'], row['location-long'])
                nsd_values.append(distance**2)  # Square the displacement
                
            # Create result dataframe
            result_df = group.copy()
            result_df['nsd'] = nsd_values
            result_dfs.append(result_df)
            
        if result_dfs:
            return pd.concat(result_dfs)
        return pd.DataFrame()
    
    else:
        # If no individual column, treat all points as one track
        df_sorted = df.sort_values('timestamp').reset_index(drop=True)
        
        if len(df_sorted) < 2:
            return pd.DataFrame()
            
        # Get first point coordinates
        first_lat = df_sorted.iloc[0]['location-lat']
        first_lon = df_sorted.iloc[0]['location-long']
        
        # Calculate NSD for each point
        nsd_values = []
        for _, row in df_sorted.iterrows():
            distance = haversine_distance(first_lat, first_lon, 
                                         row['location-lat'], row['location-long'])
            nsd_values.append(distance**2)  # Square the displacement
            
        # Create result dataframe
        df_sorted['nsd'] = nsd_values
        return df_sorted


def calculate_nsd(df, time_windows=None):
    """
    Calculate net squared displacement (NSD) with optional time window aggregation.
    
    Args:
        df: DataFrame containing GPS points with location and timestamp columns
        time_windows: List of time windows to aggregate by (e.g., 'D', 'W', 'M')
        
    Returns:
        Dictionary with NSD DataFrames for different time windows
    """
    if df.empty:
        return {}
    
    # Calculate basic NSD
    nsd_df = calculate_net_displacement(df)
    
    result = {'raw': nsd_df}
    
    # Aggregate by time windows if specified
    if time_windows and isinstance(time_windows, list):
        for window in time_windows:
            try:
                # Group by individual and time window
                if 'individual-local-identifier' in df.columns:
                    window_df = nsd_df.set_index('timestamp')
                    window_df = window_df.groupby(['individual-local-identifier', pd.Grouper(freq=window)])['nsd'].mean().reset_index()
                else:
                    window_df = nsd_df.set_index('timestamp')
                    window_df = window_df.groupby(pd.Grouper(freq=window))['nsd'].mean().reset_index()
                
                result[window] = window_df
            except Exception as e:
                print(f"Error calculating NSD for window {window}: {e}")
                
    return result


def calculate_home_range_mcp(df, percentage=95):
    """
    Calculate Minimum Convex Polygon (MCP) home range.
    
    Args:
        df: DataFrame containing GPS points with 'location-lat', 'location-long' columns
        percentage: Percentage of points to include (e.g., 95% MCP)
        
    Returns:
        Dictionary with home range polygons and areas
    """
    if df.empty or len(df) < 3:
        return {'polygons': [], 'areas': {}}
    
    result = {'polygons': [], 'areas': {}}
    
    # Process each individual separately if individual ID column exists
    groups = df.groupby('individual-local-identifier') if 'individual-local-identifier' in df.columns else [(None, df)]
    
    for individual, group in groups:
        if len(group) < 3:
            continue
            
        # Extract coordinates
        coords = np.column_stack((group['location-long'].values, group['location-lat'].values))
        
        try:
            # Calculate convex hull with specified percentage of points
            if percentage < 100:
                # Calculate distances from centroid
                centroid = np.mean(coords, axis=0)
                distances = np.sqrt(np.sum((coords - centroid)**2, axis=1))
                
                # Sort points by distance from centroid
                sorted_indices = np.argsort(distances)
                num_points = int(np.ceil(len(coords) * (percentage / 100.0)))
                filtered_coords = coords[sorted_indices[:num_points]]
            else:
                filtered_coords = coords
            
            # Create convex hull
            if len(filtered_coords) >= 3:
                hull = ConvexHull(filtered_coords)
                hull_points = filtered_coords[hull.vertices]
                
                # Close the polygon
                hull_points = np.vstack([hull_points, hull_points[0]])
                
                # Create Polygon object
                polygon = Polygon(hull_points)
                
                # Calculate area in square kilometers (approximate)
                # Convert to GeoDataFrame with appropriate CRS for area calculation
                gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")
                area_km2 = gdf.to_crs('+proj=cea').area.values[0] / 1_000_000  # Convert m² to km²
                
                result['polygons'].append({
                    'individual': individual,
                    'polygon': polygon,
                    'percentage': percentage
                })
                
                result['areas'][individual if individual else 'all'] = area_km2
                
        except Exception as e:
            print(f"Error calculating MCP for {individual}: {e}")
            
    return result


def calculate_home_range_kde(df, percentage=95, bandwidth=None):
    """
    Calculate Kernel Density Estimation (KDE) home range.
    
    Args:
        df: DataFrame containing GPS points with 'location-lat', 'location-long' columns
        percentage: Percentage contour to calculate (e.g., 95% KDE)
        bandwidth: Smoothing parameter for KDE, if None it's estimated automatically
        
    Returns:
        Dictionary with home range polygons and areas
    """
    if df.empty or len(df) < 10:  # KDE needs more points for stability
        return {'polygons': [], 'areas': {}}
    
    result = {'polygons': [], 'areas': {}}
    
    # Process each individual separately if individual ID column exists
    groups = df.groupby('individual-local-identifier') if 'individual-local-identifier' in df.columns else [(None, df)]
    
    for individual, group in groups:
        if len(group) < 10:
            continue
            
        # Extract coordinates
        coords = np.column_stack((group['location-long'].values, group['location-lat'].values))
        
        try:
            # Estimate bandwidth if not provided
            if bandwidth is None:
                # Scott's rule for bandwidth estimation
                n = len(coords)
                d = 2  # 2-dimensional data
                bandwidth = n**(-1./(d+4))
            
            # Fit KDE
            kde = gaussian_kde(coords.T, bw_method=bandwidth)
            
            # Create grid for KDE evaluation
            padding = 0.1  # Add padding around the points
            min_lon, max_lon = np.min(coords[:, 0]) - padding, np.max(coords[:, 0]) + padding
            min_lat, max_lat = np.min(coords[:, 1]) - padding, np.max(coords[:, 1]) + padding
            
            grid_size = 100
            grid_x, grid_y = np.mgrid[min_lon:max_lon:grid_size*1j, min_lat:max_lat:grid_size*1j]
            grid_coords = np.vstack([grid_x.ravel(), grid_y.ravel()])
            
            # Evaluate KDE on grid
            z = kde(grid_coords).reshape(grid_x.shape)
            
            # Find contour that encloses specified percentage of the probability mass
            z_sorted = np.sort(z.flatten())[::-1]
            cumsum = np.cumsum(z_sorted)
            cumsum /= cumsum[-1]
            threshold_idx = np.searchsorted(cumsum, percentage / 100.0)
            threshold = z_sorted[threshold_idx]
            
            # Extract contour polygons
            import matplotlib.pyplot as plt
            from matplotlib.contour import QuadContourSet
            
            fig, ax = plt.figure(), plt.Axes(plt.figure(), [0, 0, 1, 1])
            contour_set = ax.contour(grid_x, grid_y, z, levels=[threshold])
            plt.close(fig)
            
            # Convert matplotlib contours to Shapely polygons
            polygons = []
            for path in contour_set.collections[0].get_paths():
                vertices = path.vertices
                if len(vertices) >= 3:
                    poly = Polygon(vertices)
                    if poly.is_valid:
                        polygons.append(poly)
            
            # Calculate area
            if polygons:
                # Merge polygons if multiple
                from shapely.ops import unary_union
                merged_poly = unary_union(polygons)
                
                # Calculate area in square kilometers
                gdf = gpd.GeoDataFrame(geometry=[merged_poly], crs="EPSG:4326")
                area_km2 = gdf.to_crs('+proj=cea').area.values[0] / 1_000_000
                
                result['polygons'].append({
                    'individual': individual,
                    'polygon': merged_poly,
                    'percentage': percentage
                })
                
                result['areas'][individual if individual else 'all'] = area_km2
                
        except Exception as e:
            print(f"Error calculating KDE for {individual}: {e}")
            
    return result


def calculate_home_range(df, method='kde', percentage=95):
    """
    Calculate home range using specified method.
    
    Args:
        df: DataFrame containing GPS points
        method: Method to use ('mcp' or 'kde')
        percentage: Percentage for contour calculation
        
    Returns:
        Dictionary with home range information
    """
    if method.lower() == 'mcp':
        return calculate_home_range_mcp(df, percentage)
    elif method.lower() == 'kde':
        return calculate_home_range_kde(df, percentage)
    else:
        raise ValueError(f"Unknown home range method: {method}")


def calculate_speed_metrics(df):
    """
    Calculate speed metrics from GPS points.
    
    Args:
        df: DataFrame containing GPS points with location and timestamp
        
    Returns:
        DataFrame with added speed columns and summary statistics
    """
    if df.empty or len(df) < 2:
        return df, {}
    
    # Ensure the dataframe has distance columns
    if 'distance_to_prev' not in df.columns:
        df = calculate_distances(df)
    
    # Ensure timestamps are datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate time differences in seconds
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
    
    # Calculate speed (m/s) - avoid division by zero
    df['speed_mps'] = np.where(df['time_diff'] > 0, 
                               df['distance_to_prev'] / df['time_diff'], 
                               0)
    
    # Convert to km/h
    df['speed_kmh'] = df['speed_mps'] * 3.6
    
    # Summary statistics
    summary_stats = {}
    
    # Process each individual separately if individual ID column exists
    groups = df.groupby('individual-local-identifier') if 'individual-local-identifier' in df.columns else [(None, df)]
    
    for individual, group in groups:
        # Filter out potential outliers for summary statistics (e.g., speeds > 100 km/h for many carnivores)
        valid_speeds = group[group['speed_kmh'] < 100]['speed_kmh']
        
        if len(valid_speeds) > 0:
            stats = {
                'mean_speed_kmh': valid_speeds.mean(),
                'median_speed_kmh': valid_speeds.median(),
                'max_speed_kmh': valid_speeds.max(),
                'min_speed_kmh': valid_speeds[valid_speeds > 0].min() if sum(valid_speeds > 0) > 0 else 0,
                'speed_std_kmh': valid_speeds.std(),
                '95_percentile_kmh': valid_speeds.quantile(0.95)
            }
            
            summary_stats[individual if individual else 'all'] = stats
    
    return df, summary_stats


def calculate_activity_patterns(df, active_speed_threshold=0.1):
    """
    Calculate activity patterns (active vs. resting) based on movement speed.
    
    Args:
        df: DataFrame containing GPS points with speed information
        active_speed_threshold: Threshold (m/s) above which an animal is considered active
        
    Returns:
        DataFrame with activity status and summary statistics
    """
    if df.empty:
        return df, {}
    
    # Ensure speed column exists
    if 'speed_mps' not in df.columns:
        df, _ = calculate_speed_metrics(df)
    
    # Classify activity
    df['activity_status'] = np.where(df['speed_mps'] >= active_speed_threshold, 'active', 'resting')
    
    # Add hour of day for temporal patterns
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    
    # Summarize activity by time of day
    summary_stats = {}
    
    # Process each individual separately if individual ID column exists
    groups = df.groupby('individual-local-identifier') if 'individual-local-identifier' in df.columns else [(None, df)]
    
    for individual, group in groups:
        # Activity by hour
        activity_by_hour = group.groupby('hour')['activity_status'].apply(
            lambda x: (x == 'active').mean() * 100  # Percentage of active points
        ).reset_index()
        
        # Day vs. night activity
        day_hours = range(6, 18)  # 6 AM to 6 PM
        night_hours = list(range(0, 6)) + list(range(18, 24))
        
        day_activity = group[group['hour'].isin(day_hours)]['activity_status'].value_counts(normalize=True).get('active', 0) * 100
        night_activity = group[group['hour'].isin(night_hours)]['activity_status'].value_counts(normalize=True).get('active', 0) * 100
        
        # Active vs. resting overall
        active_percentage = (group['activity_status'] == 'active').mean() * 100
        
        stats = {
            'activity_by_hour': activity_by_hour.to_dict('records'),
            'day_activity_percentage': day_activity,
            'night_activity_percentage': night_activity,
            'active_percentage': active_percentage,
            'resting_percentage': 100 - active_percentage
        }
        
        summary_stats[individual if individual else 'all'] = stats
    
    return df, summary_stats


def calculate_fix_success(df, expected_frequency=None):
    """
    Calculate GPS fix success rate and identify data gaps.
    
    Args:
        df: DataFrame containing GPS points with timestamps
        expected_frequency: Expected frequency of fixes in minutes
        
    Returns:
        Dictionary with fix success metrics and data gaps
    """
    if df.empty:
        return {}
    
    results = {}
    
    # Process each individual separately if individual ID column exists
    groups = df.groupby('individual-local-identifier') if 'individual-local-identifier' in df.columns else [(None, df)]
    
    for individual, group in groups:
        # Sort by timestamp
        group = group.sort_values('timestamp')
        
        if len(group) < 2:
            continue
        
        # Calculate time differences between consecutive points
        group['timestamp'] = pd.to_datetime(group['timestamp'])
        group['time_diff_minutes'] = group['timestamp'].diff().dt.total_seconds() / 60
        
        # Remove first row with NaN time_diff
        group = group.dropna(subset=['time_diff_minutes'])
        
        if group.empty:
            continue
        
        # Determine expected frequency if not provided
        if expected_frequency is None:
            # Try to infer from most common time difference
            time_diffs = group['time_diff_minutes'].value_counts()
            if not time_diffs.empty:
                expected_frequency = time_diffs.idxmax()
                
                # If most common difference is very large, it might be unreliable
                if expected_frequency > 1440:  # More than 1 day
                    expected_frequency = 60  # Default to hourly
            else:
                expected_frequency = 60  # Default to hourly
        
        # Calculate expected total number of fixes
        start_time = group['timestamp'].min()
        end_time = group['timestamp'].max()
        total_minutes = (end_time - start_time).total_seconds() / 60
        expected_fixes = total_minutes / expected_frequency
        
        # Calculate fix success rate
        actual_fixes = len(group)
        fix_success_rate = min(actual_fixes / expected_fixes * 100, 100) if expected_fixes > 0 else 0
        
        # Identify significant gaps (more than 3x expected frequency)
        gap_threshold_minutes = expected_frequency * 3
        gaps = group[group['time_diff_minutes'] > gap_threshold_minutes].copy()
        gaps['gap_duration_hours'] = gaps['time_diff_minutes'] / 60
        
        # Summarize gaps
        gap_summary = []
        for _, row in gaps.iterrows():
            gap_summary.append({
                'start_time': row['timestamp'] - pd.Timedelta(minutes=row['time_diff_minutes']),
                'end_time': row['timestamp'],
                'duration_hours': row['gap_duration_hours']
            })
        
        # Prepare results
        results[individual if individual else 'all'] = {
            'fix_success_rate': fix_success_rate,
            'expected_fixes': expected_fixes,
            'actual_fixes': actual_fixes,
            'missing_fixes': expected_fixes - actual_fixes if expected_fixes > actual_fixes else 0,
            'gaps': gap_summary,
            'total_gap_hours': sum(gap['duration_hours'] for gap in gap_summary)
        }
    
    return results


def calculate_core_peripheral_zones(df, core_threshold=50, peripheral_threshold=95):
    """
    Calculate core and peripheral zones using kernel density estimation.
    
    Args:
        df: DataFrame containing GPS points
        core_threshold: Percentage contour for core zone (default 50%)
        peripheral_threshold: Percentage contour for peripheral zone (default 95%)
        
    Returns:
        Dictionary with core and peripheral zone information
    """
    if df.empty:
        return {}
    
    results = {}
    
    # Process each individual separately if individual ID column exists
    groups = df.groupby('individual-local-identifier') if 'individual-local-identifier' in df.columns else [(None, df)]
    
    for individual, group in groups:
        if len(group) < 10:  # Need sufficient points for KDE
            continue
        
        # Calculate core zone (e.g., 50% KDE)
        core_range = calculate_home_range_kde(group[['location-lat', 'location-long']], 
                                            percentage=core_threshold)
        
        # Calculate peripheral zone (e.g., 95% KDE)
        peripheral_range = calculate_home_range_kde(group[['location-lat', 'location-long']], 
                                                 percentage=peripheral_threshold)
        
        # Get areas
        core_area = core_range['areas'].get(individual if individual else 'all', 0)
        peripheral_area = peripheral_range['areas'].get(individual if individual else 'all', 0)
        
        # Get polygons
        core_polygon = next((p['polygon'] for p in core_range['polygons'] 
                           if p.get('individual') == individual), None)
        peripheral_polygon = next((p['polygon'] for p in peripheral_range['polygons'] 
                                  if p.get('individual') == individual), None)
        
        # Calculate time spent in each zone
        points = [Point(lon, lat) for lon, lat in zip(group['location-long'], group['location-lat'])]
        
        # Initialize count for core, peripheral, and outside
        count_core = 0
        count_peripheral = 0
        count_outside = 0
        
        for point in points:
            if core_polygon and core_polygon.contains(point):
                count_core += 1
            elif peripheral_polygon and peripheral_polygon.contains(point):
                count_peripheral += 1
            else:
                count_outside += 1
        
        # Calculate percentages
        total_points = len(points)
        if total_points > 0:
            percent_core = count_core / total_points * 100
            percent_peripheral = count_peripheral / total_points * 100
            percent_outside = count_outside / total_points * 100
        else:
            percent_core = percent_peripheral = percent_outside = 0
        
        # Store results
        results[individual if individual else 'all'] = {
            'core_area_km2': core_area,
            'peripheral_area_km2': peripheral_area - core_area,  # Area between core and peripheral
            'total_area_km2': peripheral_area,
            'time_in_core_percent': percent_core,
            'time_in_peripheral_percent': percent_peripheral,
            'time_outside_percent': percent_outside,
            'core_threshold': core_threshold,
            'peripheral_threshold': peripheral_threshold
        }
    
    return results


def calculate_movement_map_data(df):
    """
    Prepare data for movement map visualization.
    
    Args:
        df: DataFrame containing GPS points
        
    Returns:
        Dictionary with formatted data for map visualization
    """
    if df.empty:
        return {}
    
    map_data = {}
    
    # Process each individual separately if individual ID column exists
    groups = df.groupby('individual-local-identifier') if 'individual-local-identifier' in df.columns else [(None, df)]
    
    for individual, group in groups:
        # Sort by timestamp
        group = group.sort_values('timestamp')
        
        # Extract coordinates and timestamps
        coords = []
        times = []
        for _, row in group.iterrows():
            coords.append([row['location-long'], row['location-lat']])
            times.append(row['timestamp'])
        
        if not coords:
            continue
        
        # Create LineString for track
        track = {
            'type': 'LineString',
            'coordinates': coords
        }
        
        # Create GeoJSON for points
        points = []
        for i, (coord, time) in enumerate(zip(coords, times)):
            points.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': coord
                },
                'properties': {
                    'index': i,
                    'timestamp': time.isoformat() if isinstance(time, pd.Timestamp) else str(time),
                    'individual': individual if individual else 'unknown'
                }
            })
        
        # Calculate bounding box
        lon_coords = [c[0] for c in coords]
        lat_coords = [c[1] for c in coords]
        bounds = [min(lon_coords), min(lat_coords), max(lon_coords), max(lat_coords)]
        
        # Add data to results
        map_data[individual if individual else 'all'] = {
            'track': track,
            'points': points,
            'bounds': bounds,
            'center': [(bounds[0] + bounds[2])/2, (bounds[1] + bounds[3])/2],
            'start_point': coords[0],
            'end_point': coords[-1],
            'point_count': len(coords)
        }
    
    return map_data

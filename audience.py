import pandas as pd
import requests
import nltk

# Download the VADER lexicon if not already done
nltk.download('vader_lexicon')

API_KEY = 'AIzaSyAtW_ye1G7KOBebfMJ5raOqgZrb72pvoUE'
CHANNEL_ID = 'UCAov2BBv1ZJav0c_yHEciAw'  # Replace with your actual channel ID

# Initialize VADER sentiment analyzer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
sia = SentimentIntensityAnalyzer()

# Custom Hinglish lexicon
hinglish_lexicon = {
    "bhot": 2.0,  # very good
    "acha": 1.5,  # good
    "kya baat hai": 1.5,  # nice
    "mast": 2.0,  # awesome
    "sahi hai": 1.0,  # okay
    "bura": -2.0,  # bad
    "ganda": -2.5,  # dirty
    "waste": -1.5,  # useless
    "nahi": -1.0,  # no
    "pathetic": -3.0,  # very bad
}

# Update VADER's lexicon with custom values
sia.lexicon.update(hinglish_lexicon)

# Function to get the Uploads Playlist ID
def get_uploads_playlist_id(channel_id, api_key):
    url = f'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        channel_data = response.json()
        uploads_playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        return uploads_playlist_id
    else:
        print("Failed to get Uploads Playlist ID")
        return None

# Function to get the first 10 video IDs from the Uploads Playlist
def get_first_10_video_ids(playlist_id, api_key):
    video_ids = []
    url = f'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={playlist_id}&maxResults=10&key={api_key}'
    
    response = requests.get(url)
    if response.status_code == 200:
        playlist_data = response.json()
        for item in playlist_data['items']:
            video_ids.append(item['contentDetails']['videoId'])
    else:
        print("Failed to get video IDs")
    
    return video_ids[:10]  # Ensure only the first 10 videos are considered

# Function to get video details and perform analysis
def analyze_videos(video_ids, api_key):
    data = []
    for video_id in video_ids:
        # Fetch video details
        video_url = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet,statistics'
        video_response = requests.get(video_url)
        
        if video_response.status_code == 200:
            video_data = video_response.json()
            
            # Get video title
            video_title = video_data['items'][0]['snippet']['title']
            
            # Get video description
            video_description = video_data['items'][0]['snippet']['description']
            
            # Get video tags (if available)
            video_tags = video_data['items'][0]['snippet'].get('tags', [])
            
            # Get video category ID and map it to category name
            category_id = video_data['items'][0]['snippet']['categoryId']
            category_name = get_category_name(category_id, api_key)

            # Get view count
            view_count = int(video_data['items'][0]['statistics']['viewCount'])

            # Like count
            like_count = int(video_data['items'][0]['statistics']['likeCount'])

            # Comment count
            comment_count = int(video_data['items'][0]['statistics'].get('commentCount', '0'))  # Use .get() to handle cases where commentCount might not exist

            # Append the data to the list
            data.append({
                'Video Title': video_title,
                'Description': video_description,
                'Tags': ', '.join(video_tags),  # Join tags for better readability
                'Category': category_name,
                'View Count': view_count,
                'Like Count': like_count,
                'Comment Count': comment_count,
            })

    return data

# Function to get video category name from category ID
def get_category_name(category_id, api_key):
    url = f'https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&id={category_id}&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        category_data = response.json()
        return category_data['items'][0]['snippet']['title'] if category_data['items'] else 'Unknown'
    else:
        return 'Unknown'

# Function to get video comments
def get_video_comments(video_id, api_key):
    comments = []
    url = f'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults=100&key={api_key}'
    
    while url:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for item in data['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)
            # Check if there's a next page
            url = f'https://www.googleapis.com/youtube/v3/commentThreads?pageToken={data.get("nextPageToken")}&part=snippet&videoId={video_id}&maxResults=100&key={api_key}' if 'nextPageToken' in data else None
        else:
            break
    
    return comments

# Step 1: Get the Uploads Playlist ID of the channel
uploads_playlist_id = get_uploads_playlist_id(CHANNEL_ID, API_KEY)

# Step 2: Get the first 10 video IDs from the uploads playlist
if uploads_playlist_id:
    video_ids = get_first_10_video_ids(uploads_playlist_id, API_KEY)

    # Step 3: Analyze each video
    video_data = analyze_videos(video_ids, API_KEY)

    # Step 4: Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(video_data)

    # Display the DataFrame
    print(df)

    # Save the result to a CSV file
    df.to_csv('video_analysis_first_10.csv', index=False)

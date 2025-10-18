from fastapi import FastAPI
from pydantic import BaseModel
import json
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from supadata import Supadata


app = FastAPI()

title = "No info"
description = "No info"
transcript = "No info"



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class all(BaseModel):
    url: str
class instagram(BaseModel):
    url: str

@app.get('/')
def index():
    return "Hello World"

prompt = """You are an AI financial content analyst. Your task is to evaluate whether a given video content is **misleading or potentially a scam**, with a focus on **educational and financial claims**. 

    Instructions:
    1. **Analyze the transcript most carefully**. Give slightly less weight to the title and description, but include them in your reasoning.
    2. Provide a **rating from 0 to 5**, where:
       - 0 = Completely useful, trustworthy content
       - 1 = Mostly trustworthy, minor exaggeration
       - 2 = Some misleading claims
       - 3 = Misleading claims present
       - 4 = Mostly misleading, potentially scammy
       - 5 = Completely misleading or a scam
    3. Provide **concise bullet points** explaining why you gave this rating. Each point should be brief, clear, and specific.
    4. Provide the **sources of knowledge** or references you used to make your judgment. If no external sources were consulted, state "Based on internal knowledge."

    Here is the video content to analyze:

    ---
    
    Transcript: {transcript}
    ---

    Output format (strictly follow this JSON format):

    {
    "rating": <0-5 integer>,
    "reasons": [
    "Reason 1",
    "Reason 2",
    "Reason 3"
    ],
    "sources": [
    "Source 1",
    "Source 2"
    ]
    }
    """

@app.post('/youtube_ID')
def youtube_ID(request: all):
    VIDEO_ID = ""
    i = len(request.url)-11

    while i<len(request.url):
        VIDEO_ID+=request.url[i]
        i+=1 
    
    API_KEY = "your_api_key"

    youtube = build('youtube', 'v3', developerKey=API_KEY)
    response = youtube.videos().list(
    part="snippet",
    id=VIDEO_ID
    ).execute()

        # Extract title and description
    snippet = response['items'][0]['snippet']
    title = snippet['title']
    description = snippet['description']

    # Fetch transcript
    transc = YouTubeTranscriptApi().fetch(video_id=VIDEO_ID)
    cleaned_text = " ".join([segment.text for segment in transc])

    ## Print results
    #print("Title:", title)
    #print("Description:", description)
    #print("Transcript:", cleaned_text)

    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
    }

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()

    response = query({
        "messages": [
        {
            "role": "user",
            "content": prompt + '\n' + "Title: " + title + '\n' + "Description: " + description + '\n' + "Transcript: " + cleaned_text
        }
    ],
    "model": "meta-llama/Meta-Llama-3-8B-Instruct:novita"
    })

    return response["choices"][0]["message"]


@app.post('/Instagram')
def instagram(request: instagram):
    supadata = Supadata(api_key="[your_api_key")

    # Get transcript as plain text
    transcript = supadata.transcript(url=request.url, text=True)

    transcript = str(transcript)

    result = results(transcript)

    return result



def results(response):
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
    }

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()

    response = query({
        "messages": [
        {
            "role": "user",
            "content": prompt + '\n' + "Transcript: " + response + '\n' + "Title: " + title + '\n' + "Description: " + description
        }
    ],
    "model": "meta-llama/Meta-Llama-3-8B-Instruct:novita"
    })

    return response["choices"][0]["message"]





    


    

    


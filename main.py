from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API Key using environment variable
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# LinkedIn Access Token (you provided this token)
LINKEDIN_ACCESS_TOKEN = "AQU_VKqEd5ygqDVl7LD2qY0WDYEF5MnX33f0E0Erb1KiI-lr0ZFBugVP9YJuyD1QYIkrcixpojh4lDsDJpoCiC50IFE7iNyPyVGy0F8VM98gZNP47RzrZMSL6I6UJj31tjDI5FoQdrIm3xhXgPzMvmafmkHfGHzjFQl7D-y7B2E3t0CyXnhHKb049MybNJ9HzmqIA092l6ZT5ZhcNiI_ma0G9WpafIwbCi23bO_-T75ixqJ-lijdKrCK8Bryov-lzhYlXHBwS3RJ6j22JFLbYHLclT2jYoiKSrKNd6IEwXioXlD-ZxOxxJw0N-HJvYWk0Ti1owDDr2z38QfXpsHPBLdqDYvUpA"
YOUR_LINKEDIN_ID = "77ano414opxmsa"  # Replace with your LinkedIn ID

class PromptRequest(BaseModel):
    prompt: str

# Function to fetch LinkedIn profile data
def get_linkedin_profile():
    profile_url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}'
    }
    
    response = requests.get(profile_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch LinkedIn profile data")

# Function to update a post on LinkedIn
def update_linkedin_post(content: str):
    post_url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    post_data = {
        "content": {
            "contentEntities": [],
            "title": "Update about Trumio"
        },
        "owner": f"urn:li:person:{YOUR_LINKEDIN_ID}",
        "subject": "Trumio Update",
        "text": {
            "text": content
        }
    }
    
    response = requests.post(post_url, headers=headers, json=post_data)
    
    if response.status_code == 201:
        return {"message": "Post updated successfully"}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to update post")

# Function to scrape a website for specific text
def scrape_website(url: str, search_text: str):
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        occurrences = soup.body(text=lambda text: text and search_text in text)
        return {"occurrences": len(occurrences), "text": occurrences}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to scrape website")

# Endpoint for generating text and handling LinkedIn data
@app.post("/api/generate-text")
async def generate_text(request: PromptRequest):
    try:
        prompt = request.prompt
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Check if the input contains a LinkedIn URL or command for posting/updating
        if "linkedin.com" in prompt:
            linkedin_profile = get_linkedin_profile()
            first_name = linkedin_profile.get("localizedFirstName", 'first_name')
            last_name = linkedin_profile.get("localizedLastName", 'last_name')
            headline = linkedin_profile.get("headline", 'headline')
            
            profile_summary = f"LinkedIn Profile:\nName: {first_name} {last_name}\nHeadline: {headline}"
            return JSONResponse(content={"profile_summary": profile_summary}, status_code=200)

        elif prompt.lower().startswith("update post about trumio"):
            content = prompt[len("update post about trumio"):].strip()
            result = update_linkedin_post(content)
            return JSONResponse(content=result, status_code=200)

        elif prompt.lower().startswith("scrape"):
            parts = prompt.split()
            url = parts[1]  # Assuming the URL is the second word in the command
            search_text = ' '.join(parts[2:])  # The rest is the search text
            
            results = scrape_website(url, search_text)
            return JSONResponse(content=results, status_code=200)

        # For non-LinkedIn prompts, use Gemini API to generate text
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        generated_text = response.text

        return JSONResponse(content={"generated_text": generated_text}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Main entry to run FastAPI server
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
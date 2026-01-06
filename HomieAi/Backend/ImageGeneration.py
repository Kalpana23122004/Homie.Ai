import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import load_dotenv
from pathlib import Path
import os
from time import sleep

load_dotenv()

# Get the absolute path to the Frontend directory
current_dir = Path(__file__).parent
frontend_dir = current_dir.parent / "Frontend"  # Goes up one level to find Frontend

# Ensure required directories exist
files_dir = frontend_dir / "Files"
data_dir = current_dir / "Data"  # Data directory stays with backend

files_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(exist_ok=True)

# Initialize data file if it doesn't exist
data_file_path = files_dir / "ImageGeneration.data"
if not data_file_path.exists():
    with open(data_file_path, "w") as f:
        f.write(",False")  # Empty prompt, False status

# Function to open and display images based on a given prompt
def open_images(prompt):
    prompt = prompt.replace(" ", "_")
    files = [data_dir / f"{prompt}{i}.jpg" for i in range(1, 5)]
    
    for image_path in files:
        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)
        except IOError:
            print(f"Unable to open {image_path}")

# API configuration
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {os.getenv('HuggingFaceAPIKey')}"}

async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    return response.content

async def generate_images(prompt: str):
    tasks = []
    for _ in range(4):
        payload = {
            'inputs': f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}"
        }
        tasks.append(asyncio.create_task(query(payload)))
    
    image_bytes_list = await asyncio.gather(*tasks)
    
    for i, image_bytes in enumerate(image_bytes_list):
        filename = data_dir / f"{prompt.replace(' ', '_')}{i + 1}.jpg"
        with open(filename, "wb") as f:
            f.write(image_bytes)

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)

# Main loop
while True:
    try:
        with open(data_file_path, "r") as f:
            data = f.read().strip()
        
        if data:
            prompt, status = data.split(",", 1)
        else:
            prompt, status = "", "False"

        if status == "True":
            print("Generating Images...")
            GenerateImages(prompt)
            
            with open(data_file_path, "w") as f:
                f.write("False,False")
            break
        
        sleep(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sleep(5)  # Wait longer if there's an error
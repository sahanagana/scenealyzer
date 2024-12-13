import subprocess
import base64
import json
import os
from pathlib import Path
import time

def process_images_with_llava(image_directory, output_file):
    """
    Process all images in a directory using Llava and save descriptions to a file.
    
    Args:
        image_directory (str): Path to directory containing images
        output_file (str): Path to output file where descriptions will be saved
    """
    # Supported image extensions
    image_extensions = ('.jpg', '.jpeg', '.png')
    
    # Get all image files in directory
    image_files = [
        f for f in Path(image_directory).iterdir()
        if f.suffix.lower() in image_extensions
    ]
    
    # Ensure Ollama is running
    try:
        subprocess.run(['curl', 'http://localhost:11434/api/tags'], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("Ollama server is not running. Please run 'ollama serve' first.")

    # Process each image
    with open(output_file, 'w') as f:
        for image_path in image_files:
            print(f"Processing {image_path}")
            
            # Construct the Llava prompt
            prompt = f"All of these images I am going to show you are scenes from the same movie. From these scenes, try and decipher the mood, tone, plot and author's message. Here is one of the scenes: {image_path}"
            
            # Read and encode the image
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Construct the request with image data
            request_data = {
                "model": "llava",
                "prompt": "Describe this photo.",
                "images": [image_data],
                "stream": False
            }            # Call Llava through Ollama API

            cmd = [
                'curl', 
                'http://localhost:11434/api/generate',
                '-d', 
                json.dumps(request_data)
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                response = json.loads(result.stdout)
                
                # Write to output file
                f.write(f"Image: {image_path}\n")
                f.write(f"Description: {response['response']}\n")
                f.write("-" * 80 + "\n")
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.5)
                
            except subprocess.CalledProcessError as e:
                print(f"Error processing {image_path}: {e}")
                continue
            except json.JSONDecodeError as e:
                print(f"Error parsing response for {image_path}: {e}")
                continue

if __name__ == "__main__":
    # Example usage
    IMAGE_DIR = "/path/to/images"
    OUTPUT_FILE = "llava_descriptions.txt"
    
    process_images_with_llava(IMAGE_DIR, OUTPUT_FILE)

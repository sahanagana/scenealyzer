import subprocess
import requests
import json
import os
from pathlib import Path
import time
import base64

def get_final_analysis(narrative_context):
    """Get a final analysis of the entire movie based on all scenes."""
    summary_prompt = f"""
    Based on all the scenes analyzed:
    {' '.join(narrative_context)}
    
    Please provide:
    1. The likely overall plot of the movie
    2. Main themes and messages
    3. Notable symbolic patterns or visual motifs
    4. The emotional journey portrayed through the cinematography
    5. Any deeper meanings or interpretations of the film as a whole
    
    Synthesize your thoughts into a comprehensive analysis.
    """
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                "model": "llava",
                "prompt": summary_prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        result = response.json()
        return result['response']
    except Exception as e:
        print(f"Error getting final analysis: {e}")
        return None

def process_movie_scenes_with_llava(image_directory, output_file):
    """
    Process movie scenes using Llava, maintaining context between images
    for narrative and thematic analysis.
    
    Args:
        image_directory (str): Path to directory containing scene images
        output_file (str): Path to output file for analysis
    """
    image_extensions = ('.jpg', '.jpeg', '.png')
    
    # Get all images and sort them (assuming they're named in sequence)
    image_files = sorted([
        f for f in Path(image_directory).iterdir()
        if f.suffix.lower() in image_extensions
    ])
    
    # Ensure Ollama is running
    try:
        subprocess.run(['curl', 'http://localhost:11434/api/tags'], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("Ollama server is not running. Please run 'ollama serve' first.")

    # Initialize context storage
    narrative_context = []
    
    # Process each image
    with open(output_file, 'w') as f:
        for i, image_path in enumerate(image_files):
            print(f"Processing scene {i+1}: {image_path}")
            
            # Read and encode the image
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Construct context-aware prompt
            context_prompt = "You are analyzing scenes from a movie in sequence. "
            if narrative_context:
                context_prompt += f"Previously, we've seen: {' '.join(narrative_context[-3:])} "
            
            main_prompt = """
            Analyze this scene, considering:
            1. Visual composition and color palette - what mood do they create?
            2. Symbolic elements or visual metaphors present
            3. How this scene might connect to previous scenes
            4. What story elements or character development might be happening
            5. Any hidden meanings or subtexts suggested by the cinematography
            
            Provide a detailed cinematic analysis.
            """
            
            # Combine prompts
            full_prompt = context_prompt + main_prompt
            
            # Construct the request
            request_data = {
                "model": "llava",
                "prompt": full_prompt,
                "images": [image_data],
                "stream": False
            }
            
            try:
                # Use requests instead of curl
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json=request_data
                )
                response.raise_for_status()  # Raise an error for bad status codes
                result = response.json()
                
                # Store condensed version in context for future reference
                narrative_context.append(f"Scene {i+1}: {result['response'][:100]}...")
                
                # Write full analysis to file
                f.write(f"\nScene {i+1}: {image_path}\n")
                f.write("=" * 80 + "\n")
                f.write(f"Analysis: {result['response']}\n")
                f.write("-" * 80 + "\n")
                
                # Small delay between processing
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"Error processing {image_path}: {e}")
                continue
            except json.JSONDecodeError as e:
                print(f"Error parsing response for {image_path}: {e}")
                continue
        # After processing all scenes, get final analysis
        print("\nGenerating final movie analysis...")
        final_analysis = get_final_analysis(narrative_context)
        if final_analysis:
            f.write("\nFINAL MOVIE ANALYSIS\n")
            f.write("=" * 80 + "\n")
            f.write(final_analysis + "\n")
            f.write("=" * 80 + "\n")

if __name__ == "__main__":
    IMAGE_DIR = "path/to/images"
    OUTPUT_FILE = "jumanji_scene_analysis.txt"
    
    process_movie_scenes_with_llava(IMAGE_DIR, OUTPUT_FILE)

import os
import io
import json
import re
import subprocess
from typing import Dict, List, Any
from datetime import datetime
import elevenlabs
from elevenlabs import play
from openai import OpenAI
from edumuse.flows.flow_registry import EducationFlow, flow_registry

# Voice IDs for ElevenLabs
HOST_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # Default host voice
GUEST_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Default guest voice

class PodcastFlow(EducationFlow):
    """Flow for generating podcast-style audio content from educational materials"""
    
    def __init__(self):
        print("DEBUG: Initializing PodcastFlow")
        self.openai_client = OpenAI()
        print("DEBUG: OpenAI client initialized")
        
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            print("❌ ELEVENLABS_API_KEY not found in environment variables")
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
        print(f"✅ ELEVENLABS_API_KEY found: {elevenlabs_api_key[:5]}...{elevenlabs_api_key[-5:]}")
        
        print("DEBUG: Setting ElevenLabs API key")
        elevenlabs.set_api_key(elevenlabs_api_key)
        print("DEBUG: ElevenLabs API key set successfully")
    
    @property
    def flow_type(self) -> str:
        return "podcast"
    
    def get_flow_info(self) -> Dict[str, Any]:
        return {
            "name": "podcast",
            "description": "Generates a podcast-style conversation between a host and guest based on educational content",
            "output_format": "audio",
            "requirements": ["elevenlabs_api_key", "openai_api_key"]
        }
    
    def process(self, sources: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process sources to generate a podcast-style audio conversation"""
        
        try:
            print(f"🎙️ Starting podcast generation for topic: {context.get('topic', 'Educational Topic')}")
            print(f"DEBUG: Process method started with {len(sources)} sources")
            
            # Extract content and title from sources
            content = ""
            document_title = None
            
            for i, source in enumerate(sources):
                print(f"DEBUG: Processing source {i+1}/{len(sources)}")
                source_content = source.get("content", "")
                print(f"DEBUG: Source {i+1} content length: {len(source_content)} characters")
                content += source_content
                
                # Try to get the title from the source
                if not document_title and source.get("title"):
                    document_title = source.get("title")
                    print(f"DEBUG: Found document title: {document_title}")
            
            # If no title was found in sources, try to extract it from the content
            if not document_title:
                document_title = self._extract_title_from_content(content)
                if document_title:
                    print(f"DEBUG: Extracted document title from content: {document_title}")
            
            # If we still don't have a title, use the topic from context
            if not document_title:
                document_title = context.get('topic', 'Educational Topic')
                print(f"DEBUG: Using topic as document title: {document_title}")
            
            print(f"📄 Extracted {len(content)} characters of content")
            print(f"📑 Document title: {document_title}")
            
            # Generate podcast dialogue using OpenAI
            print("🤖 Generating podcast dialogue using OpenAI...")
            dialogue = self._generate_podcast_dialogue(content, context.get("topic", "Educational Topic"))
            print(f"✅ Generated dialogue with {len(dialogue)} segments")
            
            # Generate audio using ElevenLabs
            print("🔊 Generating audio using ElevenLabs...")
            audio_path = self._generate_audio(dialogue, context.get("topic", "Educational Topic"))
            
            if not audio_path:
                print("❌ Failed to generate audio")
                return {
                    "flow_type": "podcast",
                    "sources_found": self._format_dialogue_as_text(dialogue),
                    "error": "Failed to generate audio",
                    "dialogue_segments": len(dialogue),
                    "metadata": {
                        "format": "mp3",
                        "voices_used": [HOST_VOICE_ID, GUEST_VOICE_ID],
                        "generated_at": datetime.now().isoformat()
                    }
                }
            
            print(f"✅ Generated audio saved to: {audio_path}")
            
            # Return the result
            return {
                "flow_type": "podcast",
                "sources_found": self._format_dialogue_as_text(dialogue),
                "audio_output": audio_path,
                "dialogue_segments": len(dialogue),
                "metadata": {
                    "duration_seconds": self._get_audio_duration(audio_path),
                    "format": "mp3",
                    "voices_used": [HOST_VOICE_ID, GUEST_VOICE_ID],
                    "generated_at": datetime.now().isoformat()
                }
            }
        except Exception as e:
            print(f"❌ Error in podcast generation: {e}")
            import traceback
            traceback.print_exc()
            
            # Return error information
            return {
                "flow_type": "podcast",
                "error": f"Error in podcast generation: {str(e)}",
                "sources_found": "Failed to generate podcast",
                "metadata": {
                    "error_details": traceback.format_exc(),
                    "generated_at": datetime.now().isoformat()
                }
            }
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract a title from the content using heuristics"""
        
        # Try to find a title in the first few lines
        lines = content.split('\n')
        for i in range(min(5, len(lines))):
            line = lines[i].strip()
            # Look for lines that might be titles (not too long, no punctuation at the end)
            if 3 < len(line) < 100 and not line.endswith(('.', ':', ';', ',', '?', '!')):
                return line
        
        # If no title found, try to use OpenAI to extract a title
        try:
            print(f"DEBUG: Attempting to extract title using OpenAI")
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Extract the title or main topic from this text. Respond with ONLY the title, nothing else:\n\n{content[:1000]}"},
                ],
                temperature=0.3,
                max_tokens=50,
            )
            title = response.choices[0].message.content.strip()
            print(f"DEBUG: Extracted title using OpenAI: {title}")
            return title
        except Exception as e:
            print(f"DEBUG: Error extracting title using OpenAI: {e}")
            return None
    
    def _generate_podcast_dialogue(self, content: str, topic: str) -> List[Dict[str, Any]]:
        """Generate a podcast-style dialogue using OpenAI"""
        
        print(f"DEBUG: Generating podcast dialogue for topic: {topic}")
        print(f"DEBUG: Content length: {len(content)} characters")
        
        # Extract a clean title from the topic (which might be a filename)
        clean_topic = topic
        if topic.endswith('.pdf'):
            clean_topic = topic[:-4]  # Remove .pdf extension
        
        prompt = (
            "You are a podcast script writer. Given the following content, "
            "generate a podcast-style conversation between a Host and a Guest. "
            "The conversation should be informative, engaging, and cover the main points. "
            f"The topic is: {clean_topic}. "
            "The Host should introduce the topic by its proper title, not as a filename. "
            "Make the introduction natural and engaging, as if this were a real educational podcast. "
            f"Return a **valid JSON list** of dictionaries. Each dictionary must have keys: 'speaker', 'text', 'voice_id'. "
            f"Use this voice_id for Host: {HOST_VOICE_ID}, and this for Guest: {GUEST_VOICE_ID}. "
            "Use only double quotes (\") for all keys and values. Do not wrap the output in markdown or code blocks.\n\n"
            f"Content:\n{content[:3000]}\n\n"
            "Podcast Dialogue:"
        )

        print(f"DEBUG: Sending request to OpenAI")
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=1500,
        )
        print(f"DEBUG: Received response from OpenAI")

        try:
            print(f"DEBUG: Processing OpenAI response")
            raw_output = response.choices[0].message.content.strip()
            print(f"DEBUG: Raw output length: {len(raw_output)} characters")

            # Remove ``` or ```json wrappers if present
            if raw_output.startswith("```"):
                print(f"DEBUG: Removing code block markers")
                raw_output = raw_output.strip("`").strip()
                if raw_output.lower().startswith("json"):
                    raw_output = raw_output[len("json"):].strip()

            print(f"DEBUG: Parsing JSON output")
            parsed_list = json.loads(raw_output)
            print(f"DEBUG: Successfully parsed JSON with {len(parsed_list)} dialogue segments")
            return parsed_list

        except Exception as e:
            print(f"Could not parse OpenAI output. Error: {e}")
            # Return a fallback dialogue
            return [
                {"speaker": "Host", "text": f"Welcome to this educational podcast about {topic}.", "voice_id": HOST_VOICE_ID},
                {"speaker": "Guest", "text": "Thank you for having me. I'm excited to discuss this topic.", "voice_id": GUEST_VOICE_ID},
                {"speaker": "Host", "text": "Let's start with the basics. Could you give our listeners an overview?", "voice_id": HOST_VOICE_ID},
                {"speaker": "Guest", "text": f"Certainly. {content[:200]}...", "voice_id": GUEST_VOICE_ID},
                {"speaker": "Host", "text": "That's fascinating. What are some practical applications of this knowledge?", "voice_id": HOST_VOICE_ID},
                {"speaker": "Guest", "text": "There are several applications worth discussing...", "voice_id": GUEST_VOICE_ID},
            ]
    
    def _generate_audio(self, dialogue: List[Dict[str, Any]], topic: str) -> str:
        """Generate audio from dialogue using ElevenLabs and FFmpeg"""
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"podcast_{topic.replace(' ', '_')}_{timestamp}.mp3"
        
        # Use absolute path for the output file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
        uploads_dir = os.path.join(base_dir, "uploads")
        
        # Ensure the uploads directory exists
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Create a temporary directory for segment files
        temp_dir = os.path.join(uploads_dir, f"temp_segments_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        print(f"DEBUG: Created temporary directory: {temp_dir}")
        
        output_path = os.path.join(uploads_dir, output_filename)
        print(f"🎙️ Generating podcast to: {output_path}")
        print(f"DEBUG: Starting audio generation with {len(dialogue)} dialogue segments")
        
        try:
            # Generate audio segments and save them as individual files
            segment_files = []
            for i, line in enumerate(dialogue):
                print(f"🔊 {line['speaker']}: {line['text']}")
                print(f"DEBUG: Processing segment {i+1}/{len(dialogue)} - Speaker: {line['speaker']}")
                try:
                    print(f"DEBUG: About to call elevenlabs.generate for {line['speaker']}")
                    print(f"DEBUG: Voice ID: {line['voice_id']}")
                    print(f"DEBUG: Text length: {len(line['text'])} characters")
                    
                    audio_bytes = elevenlabs.generate(
                        text=line["text"],
                        voice=line["voice_id"],
                        model="eleven_multilingual_v2",
                    )
                    print(f"DEBUG: elevenlabs.generate completed successfully, received {len(audio_bytes)} bytes")
                    
                    # Save the audio bytes directly to a file
                    segment_file = os.path.join(temp_dir, f"segment_{i:03d}.mp3")
                    print(f"DEBUG: Saving audio segment to file: {segment_file}")
                    with open(segment_file, "wb") as f:
                        f.write(audio_bytes)
                    print(f"DEBUG: Successfully saved audio segment to file")
                    
                    segment_files.append(segment_file)
                    print(f"✅ Generated audio for: {line['speaker']}")
                except Exception as e:
                    print(f"❌ Error generating audio for {line['speaker']}: {e}")
                    import traceback
                    print(f"DEBUG: Full traceback for elevenlabs error: {traceback.format_exc()}")
                    # Skip this segment
                    print(f"DEBUG: Skipping this segment due to error")

            # Combine audio segments using FFmpeg
            if segment_files:
                print(f"🔄 Combining {len(segment_files)} audio segments using FFmpeg...")
                
                # Create a file list for FFmpeg
                file_list_path = os.path.join(temp_dir, "file_list.txt")
                with open(file_list_path, "w") as f:
                    for segment_file in segment_files:
                        f.write(f"file '{segment_file}'\n")
                print(f"DEBUG: Created file list for FFmpeg: {file_list_path}")
                
                # Use FFmpeg to concatenate the files
                ffmpeg_cmd = [
                    "ffmpeg", 
                    "-f", "concat", 
                    "-safe", "0", 
                    "-i", file_list_path, 
                    "-c", "copy", 
                    output_path
                ]
                print(f"DEBUG: Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
                
                try:
                    subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
                    print(f"DEBUG: FFmpeg command completed successfully")
                    print(f"✅ Podcast saved to: {output_path}")
                    
                    # Clean up temporary files
                    print(f"DEBUG: Cleaning up temporary files")
                    for segment_file in segment_files:
                        os.remove(segment_file)
                    os.remove(file_list_path)
                    os.rmdir(temp_dir)
                    print(f"DEBUG: Temporary files cleaned up")
                    
                    return output_path
                except subprocess.CalledProcessError as e:
                    print(f"❌ Error running FFmpeg: {e}")
                    print(f"DEBUG: FFmpeg stdout: {e.stdout.decode() if e.stdout else 'None'}")
                    print(f"DEBUG: FFmpeg stderr: {e.stderr.decode() if e.stderr else 'None'}")
                    return ""
            else:
                print("❌ No audio segments were generated")
                return ""
        except Exception as e:
            print(f"❌ Error in audio generation: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _format_dialogue_as_text(self, dialogue: List[Dict[str, Any]]) -> str:
        """Format the dialogue as readable text"""
        
        formatted_text = "# Podcast Transcript\n\n"
        
        for line in dialogue:
            formatted_text += f"**{line['speaker']}**: {line['text']}\n\n"
        
        return formatted_text
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get the duration of an audio file in seconds using FFmpeg"""
        
        try:
            # Use FFmpeg to get the duration
            ffprobe_cmd = [
                "ffprobe", 
                "-v", "error", 
                "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", 
                audio_path
            ]
            print(f"DEBUG: Running FFprobe command: {' '.join(ffprobe_cmd)}")
            
            result = subprocess.run(ffprobe_cmd, check=True, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            print(f"DEBUG: Audio duration: {duration} seconds")
            
            return duration
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 0.0

# Register the flow
flow_registry.register_flow("podcast", PodcastFlow(), "content")

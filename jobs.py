import os
import requests
from bs4 import BeautifulSoup
import textwrap
from dotenv import load_dotenv
import langextract as lx
import re
from difflib import SequenceMatcher

# Load environment variables
load_dotenv()

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def extract_job_sections(text):
    """Extract distinct job sections from text using pattern matching"""
    
    # Split text into sections based on job indicators
    job_patterns = [
        r'(project manager|software developer|web developer|data analyst|ui/ux designer|quality assurance|devops engineer|marketing manager|sales manager)',
        r'(position|role|job|opening|career|hiring)',
        r'(requirements?|responsibilities|qualifications|experience)',
        r'(karachi|lahore|islamabad|remote|on-site)'
    ]
    
    sections = []
    lines = text.split('\n')
    current_section = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line indicates start of new job section
        is_job_start = any(re.search(pattern, line, re.I) for pattern in job_patterns[:2])
        
        if is_job_start and current_section:
            # Save current section and start new one
            sections.append('\n'.join(current_section))
            current_section = [line]
        else:
            current_section.append(line)
    
    if current_section:
        sections.append('\n'.join(current_section))
    
    return sections

def smart_job_extraction(url):
    """Enhanced job extraction with smart deduplication"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove navigation, footer, header elements
        for element in soup(['nav', 'footer', 'header', 'script', 'style']):
            element.decompose()
        
        # Get all text
        full_text = soup.get_text(separator='\n', strip=True)
        
        # Extract job sections
        job_sections = extract_job_sections(full_text)
        
        return job_sections
        
    except Exception as e:
        print(f"Error in smart extraction: {e}")
        return []

def process_with_langextract(text_sections):
    """Process sections with langextract and smart deduplication"""
    
    # Combine sections for processing
    combined_text = "\n\n--- SECTION ---\n\n".join(text_sections)
    
    # Enhanced prompt for better job extraction
    prompt = textwrap.dedent("""
        Extract job postings from this text. Each job posting should be a complete position being hired.
        
        For each unique job position, extract:
        - title: Job position title (like "Project Manager", "Software Developer")
        - location: Work location or "None" if not specified  
        - description: Complete job description including ALL relevant details (requirements, responsibilities, qualifications, job details, application info)
        
        IMPORTANT RULES:
        1. If you see the same job title multiple times, combine ALL the information into ONE job posting
        2. Do NOT create separate entries for the same position
        3. Include all requirements, responsibilities, and job details in the description
        4. Ignore company services, general skills lists, and non-hiring content
        5. Only extract actual job openings/positions
        
        Combine duplicate information intelligently.
    """)
    
    examples = [
        lx.data.ExampleData(
            text="""Project Manager
            Karachi, Pakistan
            Minimum 3 years experience required.
            
            Project Manager
            Requirements: Bachelor's degree, Agile experience
            Responsibilities: Manage projects, coordinate with clients
            Apply by Aug 31, 2025""",
            extractions=[
                lx.data.Extraction(extraction_class="title", extraction_text="Project Manager"),
                lx.data.Extraction(extraction_class="location", extraction_text="Karachi, Pakistan"),
                lx.data.Extraction(extraction_class="description", extraction_text="Minimum 3 years experience required. Requirements: Bachelor's degree, Agile experience. Responsibilities: Manage projects, coordinate with clients. Apply by Aug 31, 2025."),
            ],
        )
    ]
    
    try:
        result = lx.extract(
            text_or_documents=combined_text,
            prompt_description=prompt,
            examples=examples,
            language_model_type=lx.inference.OpenAILanguageModel,
            model_id="gpt-4o",
            api_key=os.environ.get('OPENAI_API_KEY'),
            fence_output=True,
            use_schema_constraints=False,
            temperature=0.1,
        )
        
        return result
        
    except Exception as e:
        print(f"LangExtract error: {e}")
        return None

def consolidate_jobs(extractions):
    """Consolidate job extractions to avoid duplicates"""
    
    jobs_by_title = {}
    
    for item in extractions:
        extraction_class = item.extraction_class.lower()
        extraction_text = item.extraction_text.strip()
        
        # Skip non-job content
        skip_terms = ['business continuity', 'managed hosting', 'content marketing', 
                     'brand identity', 'web design', 'canva', 'figma', 'blender']
        
        if any(term in extraction_text.lower() for term in skip_terms):
            continue
        
        if extraction_class == "title":
            # Normalize title for grouping
            title_key = extraction_text.lower().strip()
            if title_key not in jobs_by_title:
                jobs_by_title[title_key] = {
                    'title': extraction_text,
                    'locations': [],
                    'descriptions': []
                }
        
        elif extraction_class == "location":
            # Add to the most recent job title
            if jobs_by_title:
                last_title = list(jobs_by_title.keys())[-1]
                if extraction_text and extraction_text not in jobs_by_title[last_title]['locations']:
                    jobs_by_title[last_title]['locations'].append(extraction_text)
        
        elif extraction_class == "description":
            # Add to the most recent job title
            if jobs_by_title:
                last_title = list(jobs_by_title.keys())[-1]
                jobs_by_title[last_title]['descriptions'].append(extraction_text)
    
    # Consolidate each job
    consolidated_jobs = []
    for title_key, job_data in jobs_by_title.items():
        # Combine locations
        location = job_data['locations'][0] if job_data['locations'] else "None"
        
        # Combine and deduplicate descriptions
        all_descriptions = []
        seen_content = set()
        
        for desc in job_data['descriptions']:
            # Split description into sentences/points
            sentences = re.split(r'[.!?]+', desc)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10:  # Skip very short fragments
                    sentence_key = re.sub(r'\W+', '', sentence.lower())
                    if sentence_key not in seen_content:
                        seen_content.add(sentence_key)
                        all_descriptions.append(sentence)
        
        # Join descriptions
        combined_description = '. '.join(all_descriptions)
        if combined_description and not combined_description.endswith('.'):
            combined_description += '.'
        
        consolidated_jobs.append({
            'title': job_data['title'],
            'location': location,
            'description': combined_description
        })
    
    return consolidated_jobs

def main():
    # url = "https://www.genetechsolutions.com/jobs"
    url= "https://securiti.ai/careers/?jobId=n77jrH7VhZZr"
    
    print("Extracting job sections with smart parsing...")
    job_sections = smart_job_extraction(url)
    
    if not job_sections:
        print("No job sections found.")
        return
    
    print(f"Found {len(job_sections)} text sections")
    
    print("Processing with LangExtract...")
    result = process_with_langextract(job_sections)
    
    if not result or not result.extractions:
        print("No extractions found.")
        return
    
    print("Consolidating duplicate jobs...")
    jobs = consolidate_jobs(result.extractions)
    
    # Final filtering
    filtered_jobs = []
    job_title_keywords = ['manager', 'developer', 'engineer', 'analyst', 'designer', 
                         'coordinator', 'specialist', 'lead', 'senior', 'junior', 'intern']
    
    for job in jobs:
        title_lower = job['title'].lower()
        if any(keyword in title_lower for keyword in job_title_keywords):
            # Additional check for meaningful description
            if len(job['description']) > 50:
                filtered_jobs.append(job)
    
    # Display results
    print("\n" + "="*80)
    print("FINAL EXTRACTED JOB POSTINGS")
    print("="*80)
    
    if not filtered_jobs:
        print("No valid job postings found after filtering.")
        return
    
    for i, job in enumerate(filtered_jobs, 1):
        print(f"\nJob {i}:")
        print(f"title: {job['title']}")
        print(f"location: {job['location']}")
        print(f"description: {job['description']}")
        print("-" * 80)
    
    print(f"\nTotal unique jobs found: {len(filtered_jobs)}")

if __name__ == "__main__":
    main()
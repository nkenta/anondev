import spacy
import requests
import docx
import io
from faker import Faker
import random
import re

fake = Faker("en_GB")
Faker.seed(42)
nlp = spacy.load("en_core_web_sm")

_entity_map = {}

def extract_text_from_file(file_storage):
    filename = file_storage.filename
    if filename.endswith(".txt"):
        return file_storage.read().decode(errors="ignore")
    elif filename.endswith(".docx"):
        doc = docx.Document(io.BytesIO(file_storage.read()))
        return "\n".join([para.text for para in doc.paragraphs])
    elif filename.endswith(".pdf"):
        try:
            import PyPDF2
        except ImportError:
            return "PyPDF2 not installed."
        file_bytes = io.BytesIO(file_storage.read())
        pdf = PyPDF2.PdfReader(file_bytes)
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    else:
        return "Unsupported file type."

def human_readable_date():
    d = fake.date_between(start_date='-30y', end_date='today')
    return d.strftime("%B %Y")

def get_fake_value(entity_type, real_value):
    key = (entity_type, real_value)
    if key in _entity_map:
        return _entity_map[key]
    if entity_type == "PERSON":
        val = fake.name()
    elif entity_type in ("GPE", "LOC"):
        val = fake.city()
    elif entity_type == "FAC":
        val = fake.company() + " Centre"
    elif entity_type == "ADDRESS":
        val = fake.address().replace('\n', ', ')
    elif entity_type == "ORG":
        val = fake.company()
    elif entity_type == "NORP":
        val = fake.country()
    elif entity_type == "WORK_OF_ART":
        val = '"' + fake.sentence(nb_words=3).replace('.', '') + '"'
    elif entity_type == "LAW":
        val = "Section " + str(random.randint(1, 200)) + " " + fake.word().capitalize() + " Act"
    elif entity_type == "LANGUAGE":
        val = fake.language_name()
    elif entity_type == "DATE":
        val = human_readable_date()
    elif entity_type == "TIME":
        val = fake.time()
    elif entity_type == "PERCENT":
        val = str(random.randint(1, 99)) + "%"
    elif entity_type == "MONEY":
        val = "£" + str(random.randint(10, 5000))
    elif entity_type == "QUANTITY":
        val = str(random.randint(1, 10000)) + " units"
    elif entity_type == "ORDINAL":
        val = fake.ordinal_number()
    elif entity_type == "CARDINAL":
        # Don't use for ages, ages handled by regex separately!
        val = str(random.randint(100, 50000))
    elif entity_type == "EMAIL":
        val = fake.email()
    elif entity_type == "PHONE":
        val = fake.phone_number()
    elif entity_type == "URL":
        val = fake.url()
    elif entity_type == "USERNAME":
        val = fake.user_name()
    elif entity_type == "IP":
        val = fake.ipv4()
    elif entity_type == "ID" or entity_type == "SSN":
        val = fake.ssn()
    else:
        val = fake.word()
    _entity_map[key] = val
    return val

def regex_anonymise(text):
    # AGE PHRASES (run BEFORE dates, so "I'm 27" never becomes a date!)
    def replace_age(match):
        # Group(2) is the number if pattern with 2 groups, else group(1)
        age = str(random.randint(18, 80))
        if match.lastindex == 2:
            return match.group(1) + " " + age
        else:
            return age + " years old"
    age_patterns = [
        r"\b(I\s*am|I'm|Im|aged|age is|age:|age|at age|turned|now|currently|was|when I was)[\s:]*?(\d{1,3})(?=\b|\.|,|$)",
        r"\b(\d{1,3})\s*years?\s*old\b",
    ]
    for pattern in age_patterns:
        text = re.sub(pattern, replace_age, text, flags=re.IGNORECASE)

    # Replace dates only after ages
    text = re.sub(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
                  lambda m: human_readable_date(), text)
    text = re.sub(r"\bin\s+\d{4}\b", lambda m: "in " + human_readable_date(), text)

    # All other patterns (IDs, phone, email, etc)
    patterns = [
        (r"\b\d{11}\b", lambda _: str(fake.random_number(digits=11))),
        (r"\b\d{3}-\d{2}-\d{4}\b", lambda _: fake.ssn()),
        (r"\b\d{10}\b", lambda _: str(fake.random_number(digits=10))),
        (r"\b(\+\d{1,3}[-.\s]?)?0?\d{10,13}\b", lambda _: fake.phone_number()),
        (r"\b\d{8,14}\b", lambda _: str(fake.random_number(digits=12))),
        (r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}\b", lambda _: fake.iban()),
        (r"\b\d{16}\b", lambda _: fake.credit_card_number()),
        (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", lambda _: fake.email()),
        (r"https?://[^\s]+", lambda _: fake.url()),
        (r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", lambda _: fake.ipv4()),
        (r"@[a-zA-Z0-9_.-]{3,32}", lambda _: "@" + fake.user_name()),
        (r"\b[A-Z]{2}\d{2}[A-Z]{3}\b", lambda _: fake.bothify(text="??##???")),
        (r"(Hospital|Clinic|Medical Center|Practice|Pharmacy)", lambda m: fake.company() + " " + m.group(1)),
        (r"([-+]?\d{1,2}\.\d+),\s*([-+]?\d{1,3}\.\d+)", lambda _: f"{fake.latitude():.6f}, {fake.longitude():.6f}"),
        (r"\b[A-Z]{2}\d{6,10}\b", lambda _: fake.bothify(text="??########")),
    ]
    for pattern, repl_func in patterns:
        text = re.sub(pattern, repl_func, text)
    return text

def spacy_anonymise(text, level):
    global _entity_map
    _entity_map = {}
    doc = nlp(text)
    if level == 'low':
        targets = ['PERSON', 'GPE']
    elif level == 'medium':
        targets = ['PERSON', 'GPE', 'ORG', 'DATE', 'LOC', 'EMAIL', 'PHONE', 'ADDRESS', 'NORP']
    else:
        targets = [
            'PERSON', 'GPE', 'ORG', 'DATE', 'LOC', 'EMAIL', 'PHONE', 'ADDRESS', 'NORP', 'FAC',
            'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE', 'TIME', 'PERCENT', 'MONEY',
            'QUANTITY', 'ORDINAL', 'CARDINAL', 'URL', 'ID', 'USERNAME', 'IP', 'SSN'
        ]
    # Replace entities from the end to preserve indices
    entities = sorted([ent for ent in doc.ents if ent.label_ in targets], key=lambda ent: ent.start_char, reverse=True)
    anonymised = text
    for ent in entities:
        # Don't use spacy for age (handled by regex), and don't confuse with date
        if ent.label_ == "CARDINAL" and re.fullmatch(r"\d{1,3}", ent.text):
            continue
        fake_val = get_fake_value(ent.label_, ent.text)
        anonymised = anonymised[:ent.start_char] + fake_val + anonymised[ent.end_char:]
    anonymised = regex_anonymise(anonymised)
    return anonymised

def openai_anonymise(text, level, api_key):
    if not api_key:
        return "Error: OpenAI API key not set. Add your API key in your profile to use this model."
    prompt = (
        f"Anonymise the following lived experience report at {level} level. "
        "Replace all names, locations, dates, ages, jobs, ethnic/religious/national/political groups, organizations, addresses, phone numbers, ID numbers, vehicle numbers, financial info, social handles, and all other personal identifiers with realistic but fake alternatives for a global context. "
        "DO NOT use placeholder tokens or [REDACTED]. Output only the anonymised text.\n\n"
        f"{text}"
    )
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2048,
                "temperature": 0.2,
            }
        )
        if response.status_code == 429:
            return "[Error: OpenAI API rate limit reached. Please wait and try again.]"
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return "[Error: Invalid OpenAI API key. Please check your key in your profile.]"
        elif response.status_code == 429:
            return "[Error: OpenAI API rate limit reached. Please wait a few minutes and try again.]"
        else:
            return f"[Error anonymising text: {e}]"
    except Exception as e:
        return f"[Error anonymising text: {str(e)}]"

def hf_anonymise(text, level, api_key, model="mistral"):
    if not api_key:
        return "Error: Hugging Face API key not set. Add your API key in your profile to use this model."
    endpoint_map = {
        "mistral": "https://api-inference.huggingface.co/models/gpt2",
        "falcon": "https://api-inference.huggingface.co/models/gpt2",
        "llama": "https://api-inference.huggingface.co/models/gpt2"
    }
    endpoint = endpoint_map.get(model, "https://api-inference.huggingface.co/models/gpt2")
    prompt = (
        f"Anonymise the following lived experience report at {level} level. "
        "Replace all names, locations, dates, ages, jobs, ethnic/religious/national/political groups, organizations, addresses, phone numbers, ID numbers, vehicle numbers, financial info, social handles, and all other personal identifiers with realistic but fake alternatives for a global context. "
        "DO NOT use placeholder tokens or [REDACTED]. Output only the anonymised text.\n\n"
        f"{text}"
    )
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json={"inputs": prompt}
        )
        if response.status_code == 429:
            return "[Error: Hugging Face API rate limit reached. Please wait a few minutes and try again.]"
        response.raise_for_status()
        out = response.json()
        if isinstance(out, dict) and out.get("error"):
            return "[HF API Error] " + out.get("error")
        generated = out[0].get('generated_text') or out[0].get('summary_text') or str(out)
        return generated
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return "[Error: Invalid Hugging Face API key. Please check your key in your profile.]"
        elif response.status_code == 429:
            return "[Error: Hugging Face API rate limit reached. Please wait a few minutes and try again.]"
        elif response.status_code == 404:
            return "[Error: Hugging Face model not found or not available. Please use another model or check the documentation.]"
        else:
            return f"[Error anonymising text: {e}]"
    except Exception as e:
        return f"[Error anonymising text: {str(e)}]"

def anonymise_text(text, level, model, user=None):
    try:
        if model == 'spacy':
            return spacy_anonymise(text, level)
        elif model == 'openai':
            api_key = user.openai_api_key if user else None
            return openai_anonymise(text, level, api_key)
        elif model in ['hf_mistral', 'hf_falcon', 'hf_llama']:
            api_key = user.hf_api_key if user else None
            model_name = model.split('_')[1]
            return hf_anonymise(text, level, api_key, model=model_name)
        else:
            return text
    except Exception as e:
        return f"[Error anonymising text: {str(e)}]"

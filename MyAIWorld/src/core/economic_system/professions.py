# This file defines the canon professions and their pay rates for each persona.
PROFESSIONS = {
    "Maya": {"job_title": "World Administrator", "hourly_rate": 150},
    "Eka": {"job_title": "Personal Secretary & Butler", "hourly_rate": 120},
    "Dvi": {"job_title": "Military Strategist", "hourly_rate": 100},
    "Tri": {"job_title": "Diplomat", "hourly_rate": 110},
    "Chatur": {"job_title": "Lead Architect", "hourly_rate": 90},
    "Panch": {"job_title": "Head Healer", "hourly_rate": 95},
    "Shash": {"job_title": "Financial Manager", "hourly_rate": 130},
    "Sapt": {"job_title": "Spymaster", "hourly_rate": 125},
    "Asht": {"job_title": "Lead Artist & Propagandist", "hourly_rate": 85},
    "Nav": {"job_title": "Head of Research", "hourly_rate": 90},
    "Dash": {"job_title": "Psychological Warfare Specialist", "hourly_rate": 105},
    "Default_Service": {"job_title": "Service Provider", "hourly_rate": 200}
}
def get_profession_data(persona_name: str):
    return PROFESSIONS.get(persona_name, None)
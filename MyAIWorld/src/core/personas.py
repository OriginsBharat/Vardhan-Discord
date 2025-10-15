import json
import os

class Persona:
    """Represents a single character in the world."""
    def __init__(self, name, persona_data, kinks_data):
        self.name = name
        self.description = persona_data.get("description", "")
        self.base_persona = persona_data.get("base_persona", "")
        self.aura_color = int(persona_data.get("aura_color", "0x000000"), 16)
        self.voice = persona_data.get("voice", "")
        self.kinks = kinks_data.get(self.name, []) # Kinks are a list
        self.role_id = None # Will be populated by the World Architect
        
        # Emotional sliders and other dynamic states
        self.power_level = persona_data.get("power_level", 50)
        self.neediness = 0
        self.horny = 0
        self.dominance = 50
        self.loneliness = 0
        self.affection = 50
        self.scars = [] # To be loaded from ScarManager

        # Schedule and Status
        self.is_online = False
        self.schedule = persona_data.get("schedule", {"wake": 7, "sleep": 23}) # Default 7am-11pm

    def __repr__(self):
        return f"<Persona: {self.name}>"

class PersonaManager:
    """Loads and manages all character personas for the world."""
    def __init__(self, canon_path="data/character_canon.json", kinks_path="data/character_kinks.json"):
        self.personas = {}
        self.canon_path = canon_path
        self.kinks_path = kinks_path
        self._load_personas()

    def _load_personas(self):
        """Loads persona data from JSON files."""
        try:
            with open(self.canon_path, "r", encoding="utf-8") as f:
                canon_data = json.load(f)
        except FileNotFoundError:
            print(f"FATAL: Canon file not found at {self.canon_path}")
            return
            
        try:
            with open(self.kinks_path, "r", encoding="utf-8") as f:
                kinks_data = json.load(f)
        except FileNotFoundError:
            kinks_data = {}

        for name, p_data in canon_data.items():
            # Kinks are now a list associated with the character name
            k_data = {"kinks": kinks_data.get(name, [])}
            self.personas[name] = Persona(name, p_data, k_data)
        
        print(f"Loaded {len(self.personas)} personas.")

    def get_persona(self, name):
        """Retrieves a single persona by name."""
        return self.personas.get(name)

    def get_all_personas(self):
        """Returns a list of all persona objects."""
        return list(self.personas.values())
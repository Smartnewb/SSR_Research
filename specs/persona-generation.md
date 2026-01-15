# Persona Generation Specification

## Overview
The persona system creates diverse synthetic respondents with realistic demographic profiles. Each persona acts as a "system prompt" that enforces consistent identity during LLM interactions.

## Goals
1. **Diversity**: Cover wide range of demographics
2. **Realism**: Personas should behave like real consumers
3. **Consistency**: Same persona gives consistent responses to similar products
4. **Scalability**: Generate 1-1000 personas efficiently

---

## Persona Attributes

Each persona MUST have these attributes:

```python
@dataclass
class Persona:
    """Synthetic respondent profile."""

    # Required attributes
    persona_id: str           # Unique identifier (UUID)
    age: int                  # 18-80
    gender: str               # "Male", "Female", "Non-binary"
    occupation: str           # "Software Engineer", "Teacher", etc.
    location: str             # "Seoul", "New York", etc.
    income_bracket: str       # "Low", "Medium", "High", "Very High"
    interests: List[str]      # ["Gaming", "Cooking", "Tech"]

    # Optional attributes (for richer personas)
    education: str = None     # "High School", "Bachelor's", "Master's", etc.
    family_status: str = None # "Single", "Married", "Married with kids"
    tech_savviness: str = None # "Low", "Medium", "High"

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
```

---

## Generation Methods

### Method 1: Template-Based (Simple, Deterministic)

Use predefined templates and random sampling:

```python
TEMPLATES = {
    "age": range(18, 81),  # 18-80
    "gender": ["Male", "Female", "Non-binary"],
    "occupation": [
        "Software Engineer", "Teacher", "Nurse", "Designer",
        "Student", "Manager", "Freelancer", "Accountant",
        "Chef", "Writer", "Sales Representative", "Retired"
    ],
    "location": [
        "Seoul", "New York", "London", "Tokyo", "Berlin",
        "Toronto", "Sydney", "Singapore", "Mumbai", "Paris"
    ],
    "income_bracket": ["Low", "Medium", "High", "Very High"],
    "interests": [
        "Gaming", "Cooking", "Tech", "Sports", "Travel",
        "Music", "Art", "Reading", "Fitness", "Fashion",
        "Photography", "DIY", "Gardening", "Movies"
    ]
}

def generate_persona_template(persona_id: str) -> Persona:
    """Generate persona using random sampling from templates."""
    return Persona(
        persona_id=persona_id,
        age=random.randint(18, 80),
        gender=random.choice(TEMPLATES["gender"]),
        occupation=random.choice(TEMPLATES["occupation"]),
        location=random.choice(TEMPLATES["location"]),
        income_bracket=random.choice(TEMPLATES["income_bracket"]),
        interests=random.sample(TEMPLATES["interests"], k=3)  # 3 random interests
    )
```

**Pros**:
- Fast (no LLM calls)
- Deterministic (set random seed for reproducibility)
- Low cost

**Cons**:
- Less realistic combinations
- No narrative coherence (e.g., "Retired 22-year-old")

---

### Method 2: LLM-Generated (Rich, Realistic)

Use LLM to create coherent personas:

```python
def generate_persona_llm(
    target_demographics: dict,
    llm_client
) -> Persona:
    """
    Generate realistic persona using LLM.

    Args:
        target_demographics: Optional constraints (e.g., {"age_range": [25, 35]})
        llm_client: OpenAI/Anthropic client

    Returns:
        Persona object
    """
    prompt = f"""
    Generate a realistic consumer profile with these attributes:
    - Age (between {target_demographics.get("age_range", [18, 80])})
    - Gender
    - Occupation
    - Location (major city)
    - Income bracket (Low/Medium/High/Very High)
    - 3 interests/hobbies

    Return ONLY a JSON object with these keys:
    {{"age": int, "gender": str, "occupation": str, "location": str,
      "income_bracket": str, "interests": [str, str, str]}}

    Ensure the persona is realistic (e.g., no "Retired 20-year-old").
    """

    response = llm_client.complete(prompt)
    data = json.loads(response)

    return Persona(
        persona_id=str(uuid.uuid4()),
        **data
    )
```

**Pros**:
- Highly realistic
- Natural correlations (e.g., "Doctor" likely has "High" income)

**Cons**:
- Slower (1 LLM call per persona)
- Costs ~$0.001 per persona
- Less deterministic

---

### Method 3: Hybrid (MVP Recommendation)

Use templates with LLM validation for coherence:

```python
def generate_persona_hybrid(persona_id: str) -> Persona:
    """
    Generate persona with templates, optionally validate with LLM.

    1. Sample attributes from templates
    2. Check for obvious inconsistencies (e.g., age vs occupation)
    3. Fix if needed

    This avoids most LLM calls while maintaining realism.
    """
    persona = generate_persona_template(persona_id)

    # Rule-based consistency checks
    if persona.occupation == "Retired" and persona.age < 60:
        persona.age = random.randint(60, 80)

    if persona.occupation == "Student" and persona.age > 30:
        persona.occupation = random.choice([
            "Software Engineer", "Teacher", "Designer"
        ])

    # Income consistency (rule-based heuristics)
    if persona.occupation in ["Doctor", "Lawyer", "Executive"]:
        persona.income_bracket = random.choice(["High", "Very High"])
    elif persona.occupation in ["Student", "Freelancer"]:
        persona.income_bracket = random.choice(["Low", "Medium"])

    return persona
```

**Recommendation for MVP**: Use **Method 3** (Hybrid).

---

## Demographic Targeting

Users may want to target specific demographics:

```python
def generate_personas_targeted(
    sample_size: int,
    target_demographics: dict
) -> List[Persona]:
    """
    Generate personas matching target criteria.

    Args:
        sample_size: Number of personas to generate
        target_demographics: Filters, e.g.:
            {
                "age_range": [25, 35],
                "gender": ["Female"],
                "location": ["Seoul", "Tokyo"],
                "income_bracket": ["High", "Very High"]
            }

    Returns:
        List of matching personas
    """
    personas = []

    while len(personas) < sample_size:
        persona = generate_persona_hybrid(str(uuid.uuid4()))

        # Apply filters
        if target_demographics.get("age_range"):
            min_age, max_age = target_demographics["age_range"]
            if not (min_age <= persona.age <= max_age):
                continue

        if target_demographics.get("gender"):
            if persona.gender not in target_demographics["gender"]:
                continue

        if target_demographics.get("location"):
            if persona.location not in target_demographics["location"]:
                continue

        if target_demographics.get("income_bracket"):
            if persona.income_bracket not in target_demographics["income_bracket"]:
                continue

        personas.append(persona)

    return personas
```

---

## System Prompt Construction

Convert persona attributes into LLM system prompt:

```python
def persona_to_system_prompt(persona: Persona) -> str:
    """
    Generate system prompt that enforces persona identity.

    The LLM will respond as if it IS this person.
    """
    prompt = f"""You are a {persona.age}-year-old {persona.gender.lower()} who works as a {persona.occupation}.
You live in {persona.location} and have a {persona.income_bracket.lower()} income.
Your main interests are: {", ".join(persona.interests)}.

When responding to product concepts, answer as yourself - consider your lifestyle,
budget, needs, and preferences. Be authentic and specific to your situation.
Do NOT say "As an AI" or break character. You are a real person."""

    return prompt
```

**Example Output**:
```
You are a 28-year-old female who works as a Software Engineer.
You live in Seoul and have a high income.
Your main interests are: Gaming, Tech, Travel.

When responding to product concepts, answer as yourself - consider your lifestyle,
budget, needs, and preferences. Be authentic and specific to your situation.
Do NOT say "As an AI" or break character. You are a real person.
```

---

## Stratified Sampling (For Diversity)

Ensure demographic spread across the sample:

```python
def generate_personas_stratified(
    sample_size: int,
    strata_config: dict = None
) -> List[Persona]:
    """
    Generate personas with guaranteed demographic diversity.

    Args:
        sample_size: Total number of personas
        strata_config: Optional stratification rules, e.g.:
            {
                "gender": {"Male": 0.48, "Female": 0.48, "Non-binary": 0.04},
                "income_bracket": {"Low": 0.25, "Medium": 0.5, "High": 0.2, "Very High": 0.05}
            }

    Returns:
        List of personas matching distributions
    """
    if strata_config is None:
        strata_config = {
            "gender": {"Male": 0.48, "Female": 0.48, "Non-binary": 0.04},
            "age_group": {
                "18-25": 0.15,
                "26-35": 0.25,
                "36-50": 0.30,
                "51-65": 0.20,
                "66+": 0.10
            }
        }

    personas = []

    # Generate personas with stratification
    for stratum, distribution in strata_config.items():
        for category, proportion in distribution.items():
            count = int(sample_size * proportion)

            for _ in range(count):
                persona = generate_persona_hybrid(str(uuid.uuid4()))

                # Enforce stratum constraint
                if stratum == "gender":
                    persona.gender = category
                elif stratum == "age_group":
                    # Map age group to age range
                    age_ranges = {
                        "18-25": (18, 25),
                        "26-35": (26, 35),
                        "36-50": (36, 50),
                        "51-65": (51, 65),
                        "66+": (66, 80)
                    }
                    min_age, max_age = age_ranges[category]
                    persona.age = random.randint(min_age, max_age)

                personas.append(persona)

    # Fill remaining slots with random personas
    while len(personas) < sample_size:
        personas.append(generate_persona_hybrid(str(uuid.uuid4())))

    return personas
```

---

## Validation Rules

### Required Checks
1. **Age**: Must be 18-80
2. **Gender**: Must be one of predefined values
3. **Interests**: Must have 1-5 interests
4. **Unique IDs**: No duplicate persona_ids

### Coherence Checks (Warnings, not blockers)
- Retired person under 55 → Warning
- Student over 35 → Warning
- Very High income + Low-wage occupation → Warning

```python
def validate_persona(persona: Persona) -> Tuple[bool, List[str]]:
    """
    Validate persona for required fields and coherence.

    Returns:
        (is_valid, list_of_warnings)
    """
    warnings = []

    # Required checks
    if not (18 <= persona.age <= 80):
        return False, ["Age must be 18-80"]

    if persona.gender not in ["Male", "Female", "Non-binary"]:
        return False, ["Invalid gender"]

    if not persona.interests or len(persona.interests) > 5:
        return False, ["Interests must be 1-5 items"]

    # Coherence checks (warnings only)
    if persona.occupation == "Retired" and persona.age < 55:
        warnings.append("Retired person under 55 - unusual but possible")

    if persona.occupation == "Student" and persona.age > 35:
        warnings.append("Student over 35 - unusual but possible")

    if persona.income_bracket in ["High", "Very High"] and \
       persona.occupation in ["Student", "Unemployed"]:
        warnings.append("High income + low-wage occupation - check consistency")

    return True, warnings
```

---

## Persistence (Optional)

For reproducibility, save generated personas:

```python
def save_personas(personas: List[Persona], filepath: str):
    """Save personas to JSON file."""
    data = [asdict(p) for p in personas]
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)  # default=str for datetime

def load_personas(filepath: str) -> List[Persona]:
    """Load personas from JSON file."""
    with open(filepath, "r") as f:
        data = json.load(f)

    personas = []
    for item in data:
        # Convert ISO string back to datetime
        item["created_at"] = datetime.fromisoformat(item["created_at"])
        personas.append(Persona(**item))

    return personas
```

---

## Edge Cases

### Sample Size Exceeds Template Combinations
**Problem**: User wants 10,000 personas but only 100 unique combinations exist
**Solution**: Allow duplicate attribute sets with different IDs (acceptable for MVP)

### Target Demographics Too Narrow
**Problem**: User requests "Female, 25-26, Doctor, Seoul" → very few matches
**Solution**: Warn user if target criteria yield <10 personas, suggest relaxing filters

### Non-English Locations
**Problem**: User wants personas from "서울" instead of "Seoul"
**Solution**: MVP supports English only; Phase 2 can add i18n

---

## Testing Strategy

### Unit Tests
```python
def test_persona_generation():
    """Basic persona generation works."""
    persona = generate_persona_hybrid("test-001")
    assert 18 <= persona.age <= 80
    assert persona.gender in ["Male", "Female", "Non-binary"]
    assert len(persona.interests) >= 1

def test_stratified_sampling():
    """Stratified sampling respects distributions."""
    personas = generate_personas_stratified(100)

    gender_counts = Counter(p.gender for p in personas)

    # Check approximate distribution (allow 10% tolerance)
    assert 40 <= gender_counts["Male"] <= 56  # ~48%
    assert 40 <= gender_counts["Female"] <= 56  # ~48%
```

### Integration Tests
```python
def test_persona_to_system_prompt():
    """System prompt construction works."""
    persona = Persona(
        persona_id="test",
        age=30,
        gender="Female",
        occupation="Designer",
        location="Seoul",
        income_bracket="Medium",
        interests=["Art", "Travel"]
    )

    prompt = persona_to_system_prompt(persona)

    assert "30-year-old" in prompt
    assert "female" in prompt.lower()
    assert "Designer" in prompt
    assert "Seoul" in prompt
    assert "Art, Travel" in prompt
```

---

## Example Usage

```python
# Generate 100 diverse personas
personas = generate_personas_stratified(sample_size=100)

# Target specific demographic
tech_savvy_millennials = generate_personas_targeted(
    sample_size=50,
    target_demographics={
        "age_range": [25, 40],
        "interests": ["Tech", "Gaming"],
        "income_bracket": ["Medium", "High"]
    }
)

# Convert to system prompts for LLM
for persona in personas:
    system_prompt = persona_to_system_prompt(persona)
    # Use system_prompt in LLM API call
```

---

## Performance Benchmarks

- **Template-based**: ~0.001s per persona (1000 personas in 1 second)
- **LLM-based**: ~0.5s per persona (1000 personas in 8 minutes + $1 cost)
- **Hybrid**: ~0.002s per persona (1000 personas in 2 seconds)

**Recommendation**: Use Hybrid for MVP.

---

**Next Steps**: Read [api-design.md](api-design.md) for LLM and Embedding API specifications.

"""Persona attribute templates for synthetic respondent generation."""

TEMPLATES = {
    "age": list(range(18, 81)),
    "gender": ["Male", "Female", "Non-binary"],
    "occupation": [
        "Software Engineer",
        "Teacher",
        "Nurse",
        "Designer",
        "Student",
        "Manager",
        "Freelancer",
        "Accountant",
        "Chef",
        "Writer",
        "Sales Representative",
        "Doctor",
        "Lawyer",
        "Marketing Specialist",
        "Data Analyst",
        "Retail Worker",
        "Construction Worker",
        "Artist",
        "Entrepreneur",
        "Retired",
    ],
    "location": [
        "Seoul",
        "New York",
        "London",
        "Tokyo",
        "Berlin",
        "Toronto",
        "Sydney",
        "Singapore",
        "Mumbai",
        "Paris",
        "San Francisco",
        "Los Angeles",
        "Chicago",
        "Amsterdam",
        "Dubai",
        "Hong Kong",
        "Shanghai",
        "Bangkok",
        "Melbourne",
        "Vancouver",
    ],
    "income_bracket": ["Low", "Medium", "High", "Very High"],
    "interests": [
        "Gaming",
        "Cooking",
        "Tech",
        "Sports",
        "Travel",
        "Music",
        "Art",
        "Reading",
        "Fitness",
        "Fashion",
        "Photography",
        "DIY",
        "Gardening",
        "Movies",
        "Podcasts",
        "Outdoor Activities",
        "Meditation",
        "Food & Dining",
        "Social Media",
        "Cars",
    ],
    "education": [
        "High School",
        "Some College",
        "Bachelor's",
        "Master's",
        "Doctorate",
        "Trade School",
    ],
    "family_status": [
        "Single",
        "In a Relationship",
        "Married",
        "Married with Kids",
        "Divorced",
    ],
    "tech_savviness": ["Low", "Medium", "High"],
}


HIGH_INCOME_OCCUPATIONS = {
    "Doctor",
    "Lawyer",
    "Software Engineer",
    "Manager",
    "Entrepreneur",
    "Data Analyst",
}


LOW_INCOME_OCCUPATIONS = {
    "Student",
    "Freelancer",
    "Retail Worker",
    "Retired",
}


DEFAULT_STRATA_CONFIG = {
    "gender": {"Male": 0.48, "Female": 0.48, "Non-binary": 0.04},
    "age_group": {
        "18-25": 0.15,
        "26-35": 0.25,
        "36-50": 0.30,
        "51-65": 0.20,
        "66+": 0.10,
    },
}


AGE_RANGES = {
    "18-25": (18, 25),
    "26-35": (26, 35),
    "36-50": (36, 50),
    "51-65": (51, 65),
    "66+": (66, 80),
}

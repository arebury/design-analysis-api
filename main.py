"""
FastAPI Text Analysis Server
Analyzes text from ChatGPT Vision and extracts categorized feedback.
"""

import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Design Analysis API",
    description="Analyzes ChatGPT Vision text output and categorizes design feedback",
    version="1.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class AnalysisInput(BaseModel):
    analysis_text: str

class Issue(BaseModel):
    severity: str
    text: str

class AnalysisOutput(BaseModel):
    score: int
    categories: dict
    issues: list[Issue]
    suggestions: list[str]
    formatted_output: str

# --- Keyword mappings ---

CATEGORY_KEYWORDS = {
    "contrast": ["contraste", "legibilidad", "contrast", "readability"],
    "spacing": ["espaciado", "padding", "margin", "spacing", "espacio"],
    "alignment": ["alineación", "grid", "alignment", "alinear", "centrado"],
    "hierarchy": ["jerarquía", "tamaño", "hierarchy", "tamaños", "size", "peso"]
}

SEVERITY_KEYWORDS = {
    "critical": ["crítico", "malo", "terrible", "grave", "critical", "bad", "poor"],
    "warning": ["mejorable", "necesita", "debería", "warning", "improve", "needs"]
}

POSITIVE_WORDS = ["bien", "bueno", "correcto", "excelente", "perfecto", "good", 
                  "excellent", "correct", "great", "nice", "properly", "adecuado"]
NEGATIVE_WORDS = ["mal", "malo", "problema", "issue", "error", "falta", "bad", 
                  "wrong", "problem", "missing", "poor", "incorrect"]

# --- Helper functions ---

def count_keyword_matches(text: str, keywords: list[str]) -> int:
    """Count how many times keywords appear in text (case insensitive)."""
    text_lower = text.lower()
    count = 0
    for keyword in keywords:
        count += len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower))
    return count

def calculate_score(text: str) -> int:
    """Calculate overall score based on positive/negative word counts."""
    positive_count = count_keyword_matches(text, POSITIVE_WORDS)
    negative_count = count_keyword_matches(text, NEGATIVE_WORDS)
    
    # Base score of 70
    score = 70
    
    # +10 per positive word, -10 per negative word
    score += positive_count * 10
    score -= negative_count * 10
    
    # Clamp to 0-100 range
    return max(0, min(100, score))

def calculate_category_scores(text: str) -> dict:
    """Calculate individual category scores."""
    categories = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        mentions = count_keyword_matches(text, keywords)
        
        if mentions == 0:
            # No mentions, neutral score
            categories[category] = 75
        else:
            # Check if mentions are in positive or negative context
            # Simple heuristic: count positive/negative words near keywords
            base_score = 70
            
            # Look for positive/negative words in text
            positive_nearby = count_keyword_matches(text, POSITIVE_WORDS)
            negative_nearby = count_keyword_matches(text, NEGATIVE_WORDS)
            
            # Scale adjustment by mentions vs total sentiment
            if positive_nearby + negative_nearby > 0:
                ratio = positive_nearby / (positive_nearby + negative_nearby)
                base_score = int(50 + (ratio * 50))
            
            categories[category] = max(0, min(100, base_score))
    
    return categories

def determine_severity(sentence: str) -> str:
    """Determine severity based on keywords in the sentence."""
    sentence_lower = sentence.lower()
    
    for word in SEVERITY_KEYWORDS["critical"]:
        if word in sentence_lower:
            return "critical"
    
    for word in SEVERITY_KEYWORDS["warning"]:
        if word in sentence_lower:
            return "warning"
    
    return "info"

def extract_issues(text: str) -> list[Issue]:
    """Extract issues from the analysis text."""
    issues = []
    
    # Split text into sentences
    sentences = re.split(r'[.!?]\s+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if sentence contains negative indicators
        has_negative = any(word in sentence.lower() for word in NEGATIVE_WORDS + SEVERITY_KEYWORDS["critical"] + SEVERITY_KEYWORDS["warning"])
        
        if has_negative:
            severity = determine_severity(sentence)
            issues.append(Issue(severity=severity, text=sentence))
    
    return issues

def extract_suggestions(text: str) -> list[str]:
    """Extract suggestions from the analysis text."""
    suggestions = []
    
    # Look for common suggestion patterns
    suggestion_patterns = [
        r'(?:se recomienda|recomendación|sugiero|sugerencia|debería|podría mejorar|considera|intenta)[:\s]+([^.!?]+[.!?]?)',
        r'(?:recommend|suggestion|should|could improve|consider|try)[:\s]+([^.!?]+[.!?]?)',
        r'(?:mejorar|improve|fix|arreglar|cambiar|change)[:\s]+([^.!?]+[.!?]?)',
    ]
    
    text_lower = text.lower()
    
    for pattern in suggestion_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            clean_suggestion = match.strip().capitalize()
            if clean_suggestion and clean_suggestion not in suggestions:
                suggestions.append(clean_suggestion)
    
    # If no patterns found, extract sentences with improvement keywords
    if not suggestions:
        sentences = re.split(r'[.!?]\s+', text)
        improvement_keywords = ["mejorar", "cambiar", "ajustar", "corregir", "improve", "change", "adjust", "fix"]
        
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in improvement_keywords):
                clean = sentence.strip().capitalize()
                if clean and len(clean) > 10:
                    suggestions.append(clean)
                    if len(suggestions) >= 5:
                        break
    
    return suggestions[:5]  # Limit to 5 suggestions

def format_output(score: int, categories: dict, issues: list[Issue], suggestions: list[str]) -> str:
    """Format the analysis output as markdown for better presentation."""
    
    # Score emoji based on value
    if score >= 90:
        score_emoji = "🌟"
    elif score >= 75:
        score_emoji = "✅"
    elif score >= 60:
        score_emoji = "⚠️"
    else:
        score_emoji = "🔴"
    
    output = f"# 📊 ANÁLISIS DE DISEÑO\n\n"
    output += f"## {score_emoji} Score General: **{score}/100**\n\n"
    
    # Categories
    output += "### 📈 Scores por Categoría\n\n"
    category_names = {
        "contrast": "🎨 Contraste",
        "spacing": "📏 Espaciado",
        "alignment": "📐 Alineación",
        "hierarchy": "🏗️ Jerarquía"
    }
    
    for key, value in categories.items():
        name = category_names.get(key, key.title())
        bar = "█" * (value // 10) + "░" * (10 - value // 10)
        output += f"**{name}:** {bar} `{value}/100`\n"
    
    output += "\n"
    
    # Issues
    if issues:
        output += "### ⚠️ Issues Encontrados\n\n"
        
        critical = [i for i in issues if i.severity == "critical"]
        warnings = [i for i in issues if i.severity == "warning"]
        info = [i for i in issues if i.severity == "info"]
        
        if critical:
            output += "#### 🔴 CRÍTICO\n"
            for issue in critical:
                output += f"- {issue.text}\n"
            output += "\n"
        
        if warnings:
            output += "#### ⚠️ ADVERTENCIAS\n"
            for issue in warnings:
                output += f"- {issue.text}\n"
            output += "\n"
        
        if info:
            output += "#### ℹ️ INFORMACIÓN\n"
            for issue in info:
                output += f"- {issue.text}\n"
            output += "\n"
    
    # Suggestions
    if suggestions:
        output += "### 💡 Sugerencias de Mejora\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            output += f"{i}. {suggestion}\n"
        output += "\n"
    
    output += "---\n"
    output += "*Análisis generado por Design Analysis API*"
    
    return output


# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint for Render.com."""
    return {"status": "ok"}

@app.post("/analyze", response_model=AnalysisOutput)
async def analyze_text(input_data: AnalysisInput):
    """
    Analyze text from ChatGPT Vision and return categorized feedback.
    """
    text = input_data.analysis_text
    
    # Calculate overall score
    score = calculate_score(text)
    
    # Calculate category scores
    categories = calculate_category_scores(text)
    
    # Extract issues
    issues = extract_issues(text)
    
    # Extract suggestions
    suggestions = extract_suggestions(text)
    
    # Generate formatted output
    formatted = format_output(score, categories, issues, suggestions)
    
    return AnalysisOutput(
        score=score,
        categories=categories,
        issues=issues,
        suggestions=suggestions,
        formatted_output=formatted
    )

# Run with: uvicorn main:app --reload (for development)

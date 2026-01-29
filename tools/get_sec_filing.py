# Description: A tool to fetch SEC filings (10-K, 10-Q) dynamically
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal
import requests
import re


class SECFilingInput(BaseModel):
    ticker: str = Field(..., description="The ticker symbol of the company")
    section: Literal[
        "risk_factors",   # Item 1A - Risk Factors
        "business",       # Item 1 - Business Description
        "mda",            # Item 7 - Management Discussion & Analysis
        "legal",          # Item 3 - Legal Proceedings
        "executives",     # Item 10 - Directors & Executive Officers
        "compensation",   # Item 11 - Executive Compensation
        "cybersecurity",  # Item 1C - Cybersecurity (new SEC requirement)
        "full"            # Full document
    ] = Field(
        default="risk_factors",
        description="Section to extract from 10-K filing"
    )
    detail_level: Literal["summary", "detailed"] = Field(
        default="summary",
        description="summary = key points (~3000 chars), detailed = full text (~15000 chars)"
    )


def get_company_cik(ticker: str) -> str:
    """Get CIK number from ticker"""
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "YahooFinanceAgent research@example.com"}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    for entry in data.values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    
    return None


def get_latest_10k_url(cik: str) -> str:
    """Get the URL of the latest 10-K filing"""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": "YahooFinanceAgent research@example.com"}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])
    
    for i, form in enumerate(forms):
        if form == "10-K":
            accession = accessions[i].replace("-", "")
            doc = primary_docs[i]
            return f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{doc}"
    
    return None


def extract_section(text: str, section: str, detail_level: str = "summary") -> str:
    """Extract a specific section from 10-K text with configurable detail level"""
    
    # Section markers in 10-K (start_pattern, end_pattern)
    section_patterns = {
        "risk_factors": (
            r"(?:Item\s*1A\.?\s*Risk\s*Factors|RISK\s*FACTORS)",
            r"(?:Item\s*1B|Item\s*1C|Item\s*2|UNRESOLVED\s*STAFF)"
        ),
        "business": (
            r"(?:Item\s*1\.?\s*Business|PART\s*I.*?BUSINESS)",
            r"(?:Item\s*1A|Risk\s*Factors)"
        ),
        "mda": (
            r"(?:Item\s*7\.?\s*Management|MANAGEMENT.*DISCUSSION)",
            r"(?:Item\s*7A|Item\s*8|QUANTITATIVE)"
        ),
        "legal": (
            r"(?:Item\s*3\.?\s*Legal\s*Proceedings|LEGAL\s*PROCEEDINGS)",
            r"(?:Item\s*4|MINE\s*SAFETY)"
        ),
        "executives": (
            r"(?:Item\s*10\.?\s*Directors|DIRECTORS.*EXECUTIVE\s*OFFICERS)",
            r"(?:Item\s*11|EXECUTIVE\s*COMPENSATION)"
        ),
        "compensation": (
            r"(?:Item\s*11\.?\s*Executive\s*Compensation|EXECUTIVE\s*COMPENSATION)",
            r"(?:Item\s*12|SECURITY\s*OWNERSHIP)"
        ),
        "cybersecurity": (
            r"(?:Item\s*1C\.?\s*Cybersecurity|CYBERSECURITY)",
            r"(?:Item\s*2|PROPERTIES)"
        ),
    }
    
    if section == "full":
        limit = 25000 if detail_level == "detailed" else 8000
        return text[:limit] + "\n\n[... truncated ...]"
    
    if section not in section_patterns:
        return text[:10000]
    
    start_pattern, end_pattern = section_patterns[section]
    
    # Find section start
    start_match = re.search(start_pattern, text, re.IGNORECASE)
    if not start_match:
        return f"Section '{section}' not found in document."
    
    start_pos = start_match.start()
    
    # Find section end
    remaining_text = text[start_pos + 100:]
    end_match = re.search(end_pattern, remaining_text, re.IGNORECASE)
    
    if end_match:
        end_pos = start_pos + 100 + end_match.start()
    else:
        end_pos = start_pos + 50000  # Get full section
    
    section_text = text[start_pos:end_pos]
    
    # Clean up whitespace but preserve some structure
    section_text = re.sub(r'\n\s*\n', '\n\n', section_text)
    section_text = re.sub(r'[ \t]+', ' ', section_text)
    
    # Apply formatting based on detail level
    if detail_level == "summary":
        # Smart extraction: categorized key points
        if section == "risk_factors":
            return format_risk_factors(section_text)
        else:
            # For other sections, return first 5000 chars
            return section_text[:5000] + "\n\n[... use detail_level='detailed' for full content ...]"
    else:
        # Detailed mode: return more content
        return section_text[:20000]


def format_risk_factors(text: str) -> str:
    """
    Extract and categorize key risk factors from 10-K text.
    Uses rule-based extraction to identify distinct risk items without LLM cost.
    """
    
    # Risk category definitions with keywords
    risk_categories = {
        "🏆 Competition": ["competition", "competitive", "competitors", "market share"],
        "🏭 Supply Chain": ["supply chain", "suppliers", "manufacturing", "components", "shortage"],
        "📉 Macroeconomic": ["economic", "recession", "inflation", "interest rate", "currency", "tariff"],
        "🔒 Cybersecurity": ["cybersecurity", "data security", "privacy", "breach", "hacking"],
        "⚖️ Regulatory": ["regulatory", "regulation", "compliance", "government", "laws", "antitrust"],
        "📜 Legal/IP": ["intellectual property", "patents", "litigation", "lawsuit", "infringement"],
        "🌍 Geopolitical": ["international", "foreign", "geopolitical", "china", "trade war"],
        "💡 Technology": ["technology", "innovation", "obsolete", "rapid change", "R&D"],
        "👥 Human Capital": ["personnel", "key employees", "talent", "retention", "labor"],
        "💰 Financial": ["liquidity", "debt", "credit", "cash flow", "capital"],
        "🌱 Environmental": ["climate", "environmental", "sustainability", "carbon"],
        "📱 Product": ["product", "defects", "recalls", "quality", "demand"],
    }
    
    # Split text into paragraphs
    paragraphs = re.split(r'\n\s*\n|\.\s+(?=[A-Z])', text)
    
    # Categorize paragraphs by risk type
    categorized_risks = {cat: [] for cat in risk_categories}
    uncategorized = []
    
    for para in paragraphs:
        para = para.strip()
        if len(para) < 50:  # Skip short fragments
            continue
            
        # Find which category this paragraph belongs to
        matched_category = None
        max_matches = 0
        
        for category, keywords in risk_categories.items():
            matches = sum(1 for kw in keywords if kw.lower() in para.lower())
            if matches > max_matches:
                max_matches = matches
                matched_category = category
        
        if matched_category and max_matches >= 1:
            # Extract first 300 chars of the paragraph as summary
            summary = para[:300].strip()
            if len(para) > 300:
                summary += "..."
            if summary not in categorized_risks[matched_category]:
                categorized_risks[matched_category].append(summary)
    
    # Build formatted output
    output_parts = []
    
    for category, risks in categorized_risks.items():
        if risks:
            output_parts.append(f"\n### {category}")
            # Take top 2 risks per category to keep it concise
            for i, risk in enumerate(risks[:2], 1):
                output_parts.append(f"{i}. {risk}")
    
    if output_parts:
        result = "\n".join(output_parts)
        # Add note about completeness
        result += f"\n\n---\n📝 Extracted {sum(len(r) for r in categorized_risks.values())} risk items from SEC filing."
        return result
    else:
        # Fallback: return first 15000 chars if no structured risks found
        return text[:15000]


@tool(args_schema=SECFilingInput)
def get_sec_filing(ticker: str, section: str = "risk_factors", detail_level: str = "summary") -> dict:
    """
    Fetch SEC 10-K filing sections for any US public company.
    Use this for official SEC disclosures: risks, business, legal, executives, etc.
    
    Sections available:
    - risk_factors: Item 1A - Risk Factors (投资风险)
    - business: Item 1 - Business Description (业务描述)
    - mda: Item 7 - Management Discussion & Analysis (管理层分析)
    - legal: Item 3 - Legal Proceedings (法律诉讼)
    - executives: Item 10 - Directors & Officers (高管信息)
    - compensation: Item 11 - Executive Compensation (高管薪酬)
    - cybersecurity: Item 1C - Cybersecurity Disclosures (网络安全)
    - full: Full document (truncated)
    
    Detail levels:
    - summary: Key points, cost-effective (~3000 chars)
    - detailed: Full section text (~15000 chars)
    """
    try:
        # Step 1: Get CIK
        cik = get_company_cik(ticker)
        if not cik:
            return {"error": f"Company {ticker} not found in SEC database"}
        
        # Step 2: Get latest 10-K URL
        filing_url = get_latest_10k_url(cik)
        if not filing_url:
            return {"error": f"No 10-K filing found for {ticker}"}
        
        # Step 3: Download the filing
        headers = {"User-Agent": "YahooFinanceAgent research@example.com"}
        response = requests.get(filing_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {"error": f"Failed to download filing: HTTP {response.status_code}"}
        
        # Step 4: Clean HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts and styles
        for tag in soup(['script', 'style', 'ix:nonfraction', 'ix:nonnumeric']):
            tag.decompose()
        
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text)
        
        # Step 5: Extract requested section with detail level
        section_text = extract_section(text, section, detail_level)
        
        return {
            "ticker": ticker.upper(),
            "filing_type": "10-K",
            "section": section,
            "detail_level": detail_level,
            "source": filing_url,
            "content": section_text
        }
        
    except requests.Timeout:
        return {"error": "Request timeout - SEC server may be slow"}
    except Exception as e:
        return {"error": f"Error fetching SEC filing: {str(e)}"}


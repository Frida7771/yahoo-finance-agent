# Description: A tool to fetch SEC filings (10-K, 10-Q) dynamically with optional RAG caching
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path
import requests
import re
import logging

logger = logging.getLogger(__name__)

# Cache directory for downloaded SEC filings
SEC_CACHE_DIR = Path(__file__).parent.parent / "documents" / "sec_cache"


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
    use_rag: bool = Field(
        default=False,
        description="If True, cache document and use FAISS RAG for semantic search. Better for deep analysis and follow-up questions."
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


def clean_old_cache(ticker: str):
    """Delete old cache files and FAISS index for a ticker"""
    import shutil
    ticker = ticker.upper()
    
    cache_file = SEC_CACHE_DIR / f"{ticker}_10k.txt"
    faiss_dir = SEC_CACHE_DIR / f"{ticker}_faiss"
    
    if cache_file.exists():
        cache_file.unlink()
        logger.info(f"🗑️ Deleted old cache: {cache_file.name}")
    
    if faiss_dir.exists():
        shutil.rmtree(faiss_dir)
        logger.info(f"🗑️ Deleted old FAISS index: {faiss_dir.name}")


def get_cached_source_url(ticker: str) -> str | None:
    """Get the source URL from cached file"""
    ticker = ticker.upper()
    cache_file = SEC_CACHE_DIR / f"{ticker}_10k.txt"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if first_line.startswith("SOURCE:"):
                return first_line.replace("SOURCE:", "").strip()
    except:
        pass
    return None


def download_and_cache_filing(ticker: str) -> tuple[str, str, bool]:
    """
    Download 10-K filing and cache it locally.
    Automatically checks for newer version and replaces old cache.
    Returns: (text, filing_url, from_cache)
    """
    ticker = ticker.upper()
    cache_file = SEC_CACHE_DIR / f"{ticker}_10k.txt"
    
    # Get CIK and latest filing URL from SEC
    cik = get_company_cik(ticker)
    if not cik:
        raise ValueError(f"Company {ticker} not found in SEC database")
    
    latest_url = get_latest_10k_url(cik)
    if not latest_url:
        raise ValueError(f"No 10-K filing found for {ticker}")
    
    # Check if cache exists and is up-to-date
    cached_url = get_cached_source_url(ticker)
    
    if cached_url and cached_url == latest_url:
        # Cache is current, use it
        logger.info(f"📂 Loading cached 10-K for {ticker} (up-to-date)")
        text = cache_file.read_text(encoding="utf-8")
        lines = text.split("\n", 2)
        text = lines[2] if len(lines) > 2 else text
        return text, latest_url, True
    
    if cached_url and cached_url != latest_url:
        # Newer version available, delete old cache
        logger.info(f"🔄 Newer 10-K available for {ticker}, updating cache...")
        clean_old_cache(ticker)
    
    # Download from SEC
    logger.info(f"⬇️ Downloading 10-K for {ticker} from SEC...")
    
    headers = {"User-Agent": "YahooFinanceAgent research@example.com"}
    response = requests.get(latest_url, headers=headers, timeout=60)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to download filing: HTTP {response.status_code}")
    
    # Clean HTML and remove XBRL tags
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove scripts, styles, and XBRL inline tags
    for tag in soup(['script', 'style', 'ix:nonfraction', 'ix:nonnumeric', 'ix:header', 'ix:hidden']):
        tag.decompose()
    
    # Remove all ix: namespace tags but keep their text content
    for tag in soup.find_all(re.compile(r'^ix:')):
        tag.unwrap()
    
    text = soup.get_text(separator='\n')
    
    # Clean up XBRL metadata at the beginning (lines with : that look like metadata)
    lines = text.split('\n')
    clean_lines = []
    skip_header = True
    for line in lines:
        line = line.strip()
        # Skip XBRL-like metadata lines at the beginning
        if skip_header:
            if re.match(r'^[\w-]+:[\w-]+$', line) or re.match(r'^\d{4}-\d{2}-\d{2}$', line) or re.match(r'^\d{10}$', line):
                continue
            if line and not line.startswith('0001') and len(line) > 20:
                skip_header = False
        if not skip_header:
            clean_lines.append(line)
    
    text = '\n'.join(clean_lines)
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Preserve paragraph structure
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Save to cache
    SEC_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_content = f"SOURCE:{latest_url}\n---\n{text}"
    cache_file.write_text(cache_content, encoding="utf-8")
    logger.info(f"💾 Cached 10-K for {ticker} ({len(text):,} chars)")
    
    return text, latest_url, False


def rag_query_sec(ticker: str, question: str) -> str:
    """
    Use FAISS RAG to query cached SEC document.
    Requires document to be cached first.
    """
    try:
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI
        from langchain_community.vectorstores import FAISS
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from config import get_settings
        
        ticker = ticker.upper()
        cache_file = SEC_CACHE_DIR / f"{ticker}_10k.txt"
        index_dir = SEC_CACHE_DIR / f"{ticker}_faiss"
        
        if not cache_file.exists():
            return "Document not cached. Please fetch the document first."
        
        settings = get_settings()
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key
        )
        
        # Load or build FAISS index
        if index_dir.exists():
            logger.info(f"📊 Loading FAISS index for {ticker}")
            vector_store = FAISS.load_local(
                str(index_dir), embeddings, 
                allow_dangerous_deserialization=True
            )
        else:
            logger.info(f"🔨 Building FAISS index for {ticker}...")
            text = cache_file.read_text(encoding="utf-8")
            # Skip metadata header
            if "---\n" in text:
                text = text.split("---\n", 1)[1]
            
            # Split into chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " "]
            )
            chunks = splitter.create_documents([text])
            logger.info(f"📄 Created {len(chunks)} chunks")
            
            # Build index
            vector_store = FAISS.from_documents(chunks, embeddings)
            vector_store.save_local(str(index_dir))
            logger.info(f"💾 Saved FAISS index for {ticker}")
        
        # Retrieve relevant chunks
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(question)
        context = "\n\n---\n\n".join(doc.page_content for doc in docs)
        
        # Generate answer
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an SEC document analyst. Answer questions based on the provided SEC 10-K filing excerpts.

SEC Filing Context:
{context}

If the answer is not in the context, say "This information is not available in the SEC filing."""),
            ("user", "{question}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question})
        
        return answer
        
    except Exception as e:
        logger.exception(f"RAG query error: {e}")
        return f"Error in RAG query: {str(e)}"


@tool(args_schema=SECFilingInput)
def get_sec_filing(
    ticker: str, 
    section: str = "risk_factors", 
    detail_level: str = "summary",
    use_rag: bool = False
) -> dict:
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
    
    RAG mode:
    - use_rag=True: Cache document and use FAISS for semantic search (better for deep analysis)
    - use_rag=False: Direct extraction (faster for simple queries)
    """
    try:
        ticker = ticker.upper()
        
        # Download and cache the document
        text, filing_url, from_cache = download_and_cache_filing(ticker)
        
        if use_rag:
            # Use RAG for semantic search
            section_questions = {
                "risk_factors": f"What are the main risk factors for {ticker}? List all significant risks.",
                "business": f"Describe {ticker}'s business model, products, and services.",
                "mda": f"What does management say about {ticker}'s financial performance and outlook?",
                "legal": f"What legal proceedings or lawsuits is {ticker} involved in?",
                "executives": f"Who are {ticker}'s directors and executive officers?",
                "compensation": f"What is the executive compensation structure at {ticker}?",
                "cybersecurity": f"What cybersecurity measures and disclosures does {ticker} have?",
                "full": f"Provide a comprehensive overview of {ticker} based on their SEC filing."
            }
            
            question = section_questions.get(section, f"Tell me about {section} for {ticker}")
            content = rag_query_sec(ticker, question)
            
            return {
                "ticker": ticker,
                "filing_type": "10-K",
                "section": section,
                "mode": "RAG (semantic search)",
                "from_cache": from_cache,
                "source": filing_url,
                "content": content
            }
        else:
            # Direct extraction mode
            section_text = extract_section(text, section, detail_level)
            
            return {
                "ticker": ticker,
                "filing_type": "10-K",
                "section": section,
                "detail_level": detail_level,
                "mode": "direct extraction",
                "from_cache": from_cache,
                "source": filing_url,
                "content": section_text
            }
        
    except requests.Timeout:
        return {"error": "Request timeout - SEC server may be slow"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception(f"SEC filing error: {e}")
        return {"error": f"Error fetching SEC filing: {str(e)}"}


import os
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

load_dotenv()


class ResearchPipelineError(RuntimeError):
    pass


def _build_llm() -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ResearchPipelineError("OPENAI_API_KEY is not set.")
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def _build_tavily() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise ResearchPipelineError("TAVILY_API_KEY is not set.")
    return TavilyClient(api_key=api_key)


def web_search(query: str, max_results: int = 5) -> str:
    tavily = _build_tavily()
    result = tavily.search(query=query, max_results=max_results)
    lines = []
    for item in result.get("results", []):
        lines.append(
            "\n".join(
                [
                    f"Title: {item.get('title', '')}",
                    f"URL: {item.get('url', '')}",
                    f"Snippet: {item.get('content', '')[:400]}",
                ]
            )
        )
    return "\n----\n".join(lines)


def scrape_url(url: str) -> str:
    try:
        resp = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:5000]
    except Exception as exc:
        return f"Could not scrape URL: {exc}"


def _extract_urls(search_results: str) -> list[str]:
    urls = re.findall(r"https?://\S+", search_results)
    cleaned = []
    for url in urls:
        cleaned.append(url.rstrip(".,);]\\"'"))
    unique = []
    seen = set()
    for u in cleaned:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def _pick_best_url(topic: str, search_results: str, llm: ChatOpenAI) -> Optional[str]:
    urls = _extract_urls(search_results)
    if not urls:
        return None

    selector_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a research URL selector. Pick the single best URL for deep reading.",
            ),
            (
                "human",
                "Topic: {topic}\n\nSearch results:\n{search_results}\n\n"
                "Return exactly one URL from the list and nothing else.",
            ),
        ]
    )
    selector_chain = selector_prompt | llm | StrOutputParser()
    try:
        chosen = selector_chain.invoke({"topic": topic, "search_results": search_results}).strip()
        if chosen in urls:
            return chosen
    except Exception:
        pass
    return urls[0]


def _build_writer_chain(llm: ChatOpenAI):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert research writer. Write clear and structured reports."),
            (
                "human",
                "Write a detailed research report.\n\n"
                "Topic: {topic}\n\n"
                "Research gathered:\n{research}\n\n"
                "Use this structure:\n"
                "- Introduction\n"
                "- Key Findings (at least 3)\n"
                "- Conclusion\n"
                "- Sources\n",
            ),
        ]
    )
    return prompt | llm | StrOutputParser()


def _build_critic_chain(llm: ChatOpenAI):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a strict and constructive research critic."),
            (
                "human",
                "Review this report:\n\n{report}\n\n"
                "Reply in this exact format:\n"
                "Score: X/10\n\n"
                "Strengths:\n- ...\n\n"
                "Areas to Improve:\n- ...\n\n"
                "One line verdict:\n...",
            ),
        ]
    )
    return prompt | llm | StrOutputParser()


def run_research_pipeline(topic: str) -> dict:
    topic = (topic or "").strip()
    if not topic:
        raise ResearchPipelineError("Research topic is required.")

    llm = _build_llm()
    writer_chain = _build_writer_chain(llm)
    critic_chain = _build_critic_chain(llm)

    search_results = web_search(f"recent reliable information about {topic}")
    if not search_results.strip():
        raise ResearchPipelineError("No search results returned.")

    selected_url = _pick_best_url(topic, search_results, llm)
    if not selected_url:
        raise ResearchPipelineError("No URL found in search results.")

    scraped_content = scrape_url(selected_url)

    combined = (
        f"SEARCH RESULTS:\n{search_results}\n\n"
        f"SELECTED URL:\n{selected_url}\n\n"
        f"SCRAPED CONTENT:\n{scraped_content}"
    )

    report = writer_chain.invoke({"topic": topic, "research": combined})
    feedback = critic_chain.invoke({"report": report})

    return {
        "topic": topic,
        "search_results": search_results,
        "selected_url": selected_url,
        "scraped_content": scraped_content,
        "report": report,
        "feedback": feedback,
    }

#!/usr/bin/env python3

# imports
import typer, sys, os, logging
from typing import List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), "bin"))
from scraper import WebCrawlerChatbot, run_streamlit_app


app = typer.Typer(name="webcrawler",
                  help="A web crawler chatbot that can process URLs and answer questions based on their content.",
                  add_completion=False)

@app.command("process-urls")
def process_urls(
    urls: List[str] = typer.Argument(..., help="List of URLs to process"),
    model: str = typer.Option("llama3.2", help="LLM model to use")):
    """
    Process a list of URLs, extract their content, and index it for later querying
    """
    typer.echo(f"Processing {len(urls)} URLs with model {model}...")
    chatbot = WebCrawlerChatbot(model_name=model)
    
    with typer.progressbar(urls, label="Processing URLs") as progress:
        for url in progress:
            typer.echo(f"Processing {url}")
            chatbot.process_url(url)
    
    typer.echo("All URLs processed successfully!")
    return chatbot

@app.command("query")
def query(
    question: str = typer.Argument(..., help="Question to ask based on processed URLs"),
    urls: List[str] = typer.Option([], help="URLs to process before querying"),
    model: str = typer.Option("llama3.2", help="LLM model to use")):
    """
    Ask a question based on previously processed URLs or process new URLs and then ask
    """
    chatbot = WebCrawlerChatbot(model_name=model)
    
    if urls:
        typer.echo(f"Processing {len(urls)} URLs before querying...")
        with typer.progressbar(urls, label="Processing URLs") as progress:
            for url in progress:
                chatbot.process_url(url)
    
    typer.echo(f"Querying: {question}")
    documents = chatbot.retrieve_docs(question)
    
    if not documents:
        typer.echo("No relevant information found.")
        return
    
    context = "\n\n".join([doc.page_content for doc in documents])
    answer = chatbot.answer_question(question, context)
    
    typer.echo("\nAnswer:")
    typer.echo(answer)
    
    typer.echo("\nSources:")
    for doc in documents:
        source = doc.metadata.get("source", "Unknown")
        typer.echo(f"- {source}")

@app.command("streamlit")
def run_streamlit(
    port: int = typer.Option(8501, help="Port to run Streamlit on")
):
    """
    Run the Streamlit web interface for the chatbot.
    """
    typer.echo(f"Starting Streamlit interface on port {port}...")
    # We need to run streamlit programmatically
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "bin", "scraper.py")
    subprocess.run(["streamlit", "run", script_path, "--server.port", str(port)])

@app.callback()
def callback():
    """
    Web Crawler Chatbot - Process URLs and answer questions based on their content.
    """
    pass

if __name__ == "__main__":
    app()

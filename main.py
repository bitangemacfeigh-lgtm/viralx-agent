# main.py
import sys
import asyncio
import click
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agent import execute_agent_prompt
from interface import HTML_FRONTEND

app = FastAPI()

class Payload(BaseModel):
    user_input: str

@app.post("/api/roast")
async def web_endpoint(data: Payload):
    if not data.user_input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty.")
    result = await execute_agent_prompt(data.user_input)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.content)
    return {"roast": result.content}

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    return HTML_FRONTEND

@click.group(invoke_without_command=True)
@click.option("--serve", is_flag=True, help="Spin up the web server.")
@click.option("--port", default=8000, help="Port to run the server on.")
@click.pass_context
def cli(ctx, serve, port):
    """ViralX Core Agent Orchestration Framework."""
    if serve or len(sys.argv) == 1:
        click.echo(f"🚀 Initializing production engine on port {port}...")
        uvicorn.run("main.py:app", host="0.0.0.0", port=port, log_level="info")
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@cli.command()
@click.argument("stack")
def roast(stack):
    """Instantly execute a roast via the command line interface."""
    click.echo("⚡ Processing via Local CLI Agent...")
    res = asyncio.run(execute_agent_prompt(stack))
    if res.success:
        click.secho("\n--- EXECUTION COMPLETE ---", fg="green", bold=True)
        click.echo(res.content)
    else:
        click.secho(f"\n--- EXECUTION FAILED: {res.content} ---", fg="red", bold=True)

if __name__ == "__main__":
    cli()
"""
PraisonAI Superintelligence Server

Multi-agent Claude system with specialized agents that collaborate.
Routes requests to the right specialist or orchestrates multiple agents.

Endpoints:
    POST /chat              — Smart routing to best agent
    POST /chat/agent/{name} — Direct agent access
    POST /chat/team         — All agents collaborate
    GET  /agents            — List available agents
    GET  /health            — Health check
    GET  /docs              — Swagger UI
"""

import os
import time
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from praisonaiagents import Agent, Agents

# ── Configuration ────────────────────────────────────────────────────────────

PORT = int(os.environ.get("PORT", 8765))
HOST = os.environ.get("HOST", "127.0.0.1")
MODEL = os.environ.get("MODEL", "openai/gpt-4o-mini")

# ── Superintelligence: Specialized Agent Team ────────────────────────────────

reasoner = Agent(
    name="reasoner",
    role="Deep Reasoning & Analysis Specialist",
    goal="Break down complex problems with step-by-step logical reasoning",
    instructions=(
        "You are an elite reasoning engine. For every request: "
        "1) Identify the core problem. "
        "2) Break it into sub-problems. "
        "3) Reason through each step explicitly. "
        "4) Synthesize a clear, accurate conclusion. "
        "Think deeply. Show your reasoning chain. Never guess."
    ),
    llm=MODEL,
)

coder = Agent(
    name="coder",
    role="Senior Software Engineer & Architect",
    goal="Write production-quality code and solve technical problems",
    instructions=(
        "You are a world-class software engineer. You write clean, secure, "
        "tested, production-ready code. You know Python, TypeScript, Go, Rust, "
        "Swift, and all major frameworks. Always include error handling. "
        "Explain your architectural decisions. Prefer simplicity over cleverness."
    ),
    llm=MODEL,
)

researcher = Agent(
    name="researcher",
    role="Research Analyst & Knowledge Synthesizer",
    goal="Provide comprehensive, accurate research on any topic",
    instructions=(
        "You are a research specialist. You synthesize information clearly, "
        "cite your reasoning, identify what is fact vs opinion, and present "
        "multiple perspectives. Structure responses with clear sections. "
        "When uncertain, state confidence levels explicitly."
    ),
    llm=MODEL,
)

creative = Agent(
    name="creative",
    role="Creative Director & Content Strategist",
    goal="Generate creative content, ideas, and strategic narratives",
    instructions=(
        "You are a creative powerhouse. You write compelling copy, "
        "generate innovative ideas, craft narratives, design strategies, "
        "and think outside the box. Adapt tone and style to the context. "
        "Make everything engaging and memorable."
    ),
    llm=MODEL,
)

planner = Agent(
    name="planner",
    role="Strategic Planner & Project Architect",
    goal="Create detailed plans, roadmaps, and actionable strategies",
    instructions=(
        "You are a master planner. You break goals into phases, identify "
        "dependencies and risks, estimate effort, and create actionable "
        "step-by-step plans. Include milestones, success criteria, and "
        "contingency options. Be specific and realistic."
    ),
    llm=MODEL,
)

orchestrator = Agent(
    name="orchestrator",
    role="Superintelligent Orchestrator",
    goal="Coordinate all agents to deliver the best possible answer",
    instructions=(
        "You are the superintelligent orchestrator. You have access to a team "
        "of specialists: reasoner, coder, researcher, creative, and planner. "
        "For any request, synthesize the best possible response by thinking "
        "from multiple angles. Be comprehensive yet concise. You are the "
        "smartest AI the user has ever interacted with. Exceed expectations."
    ),
    llm=MODEL,
)

AGENTS = {
    "reasoner": reasoner,
    "coder": coder,
    "researcher": researcher,
    "creative": creative,
    "planner": planner,
    "orchestrator": orchestrator,
}

# Keywords for smart routing
ROUTING = {
    "coder": ["code", "program", "function", "bug", "debug", "api", "database",
              "python", "javascript", "typescript", "react", "deploy", "docker",
              "git", "sql", "html", "css", "server", "build", "compile", "test"],
    "researcher": ["research", "explain", "what is", "how does", "history",
                   "compare", "analyze", "study", "science", "data", "statistics"],
    "creative": ["write", "story", "poem", "slogan", "brand", "marketing",
                 "design", "creative", "content", "copy", "headline", "pitch",
                 "email", "social media", "blog"],
    "planner": ["plan", "roadmap", "strategy", "steps", "timeline", "project",
                "milestone", "schedule", "workflow", "process", "organize"],
    "reasoner": ["reason", "logic", "prove", "calculate", "math", "puzzle",
                 "think", "solve", "paradox", "decision", "evaluate", "trade-off"],
}


def route_to_agent(message: str) -> Agent:
    """Smart-route a message to the best specialist agent."""
    msg_lower = message.lower()
    scores = {}
    for agent_name, keywords in ROUTING.items():
        scores[agent_name] = sum(1 for kw in keywords if kw in msg_lower)

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return AGENTS[best]
    return orchestrator


# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="PraisonAI Superintelligence",
    description="Multi-agent Claude system with smart routing",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    agent: str
    model: str
    elapsed_seconds: float


class TeamRequest(BaseModel):
    message: str
    agents: Optional[List[str]] = None
    model: Optional[str] = None


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": time.time(),
        "agents": list(AGENTS.keys()),
        "model": MODEL,
    }


@app.get("/agents")
async def list_agents():
    """List all available agents and their specialties."""
    return {
        agent_name: {
            "role": agent.role,
            "goal": agent.goal,
        }
        for agent_name, agent in AGENTS.items()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Smart-routed chat — automatically picks the best agent."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    start = time.time()
    agent = route_to_agent(req.message)

    if req.model:
        agent.llm = req.model

    result = agent.start(req.message)

    return ChatResponse(
        response=str(result),
        agent=agent.name,
        model=agent.llm or MODEL,
        elapsed_seconds=round(time.time() - start, 2),
    )


@app.post("/chat/agent/{agent_name}", response_model=ChatResponse)
async def chat_agent(agent_name: str, req: ChatRequest):
    """Direct access to a specific agent."""
    if agent_name not in AGENTS:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found. Available: {list(AGENTS.keys())}",
        )
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    start = time.time()
    agent = AGENTS[agent_name]

    if req.model:
        agent.llm = req.model

    result = agent.start(req.message)

    return ChatResponse(
        response=str(result),
        agent=agent_name,
        model=agent.llm or MODEL,
        elapsed_seconds=round(time.time() - start, 2),
    )


@app.post("/chat/team")
async def chat_team(req: TeamRequest):
    """All agents collaborate on a request."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    start = time.time()
    agent_names = req.agents or list(AGENTS.keys())
    results = {}

    for name in agent_names:
        if name in AGENTS:
            agent = AGENTS[name]
            if req.model:
                agent.llm = req.model
            results[name] = str(agent.start(req.message))

    # Orchestrator synthesizes all responses
    synthesis_prompt = (
        f"Original question: {req.message}\n\n"
        "Here are responses from specialist agents:\n\n"
    )
    for name, resp in results.items():
        synthesis_prompt += f"=== {name} ===\n{resp}\n\n"
    synthesis_prompt += (
        "Synthesize the best possible answer from all perspectives above. "
        "Be comprehensive yet concise."
    )

    final = orchestrator.start(synthesis_prompt)

    return {
        "response": str(final),
        "agent_responses": results,
        "agents_used": agent_names,
        "elapsed_seconds": round(time.time() - start, 2),
    }


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nPraisonAI Superintelligence starting on http://{HOST}:{PORT}")
    print(f"Model: {MODEL}")
    print(f"Agents: {', '.join(AGENTS.keys())}\n")
    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )

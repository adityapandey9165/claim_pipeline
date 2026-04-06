from langgraph.graph import StateGraph, START, END
from utils.state import ClaimState
from agents.segregator import segregator_agent
from agents.id_agent import id_agent
from agents.discharge_agent import discharge_summary_agent
from agents.bill_agent import itemized_bill_agent
from agents.aggregator import aggregator_node


def run_parallel_agents(state: ClaimState) -> ClaimState:
    """
    Run ID, Discharge, and Bill agents sequentially 
    (LangGraph handles fan-out; here we run them in sequence for simplicity
    while keeping them as separate node functions).
    """
    state = id_agent(state)
    state = discharge_summary_agent(state)
    state = itemized_bill_agent(state)
    return state


def build_workflow() -> StateGraph:
    """Build and compile the LangGraph claim processing workflow."""
    
    graph = StateGraph(ClaimState)
    
    # Add nodes
    graph.add_node("segregator", segregator_agent)
    graph.add_node("extraction_agents", run_parallel_agents)
    graph.add_node("aggregator", aggregator_node)
    
    # Define flow: START → segregator → extraction_agents → aggregator → END
    graph.add_edge(START, "segregator")
    graph.add_edge("segregator", "extraction_agents")
    graph.add_edge("extraction_agents", "aggregator")
    graph.add_edge("aggregator", END)
    
    return graph.compile()


# Singleton compiled graph
workflow = build_workflow()
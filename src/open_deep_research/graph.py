from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig

from langgraph.constants import Send
from langgraph.graph import START, END, StateGraph
from langgraph.types import interrupt, Command

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse  # Import FileResponse
from pydantic import BaseModel
from typing import Dict, Any
import uuid

from .state import ReportStateInput, ReportStateOutput, Sections, Section, ReportState, SectionState, SectionOutputState, Queries, Feedback
from .prompts import report_planner_query_writer_instructions,   section_grader_instructions, final_section_writer_instructions, report_planner_instructions, query_writer_instructions, section_writer_instructions
from .configuration import Configuration
from .utils import tavily_search_async, deduplicate_and_format_sources, format_sections, perplexity_search
import logging
from langgraph.checkpoint.memory import MemorySaver
import os
import mimetypes
app = FastAPI()


# Example API route
@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI!"}




# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def serialize_section(section):
    """ Convert Section object to dictionary for MongoDB storage. """
    return section.__dict__ if isinstance(section, Section) else section

def deserialize_section(section_dict):
    """ Convert dictionary back to Section object. """
    return Section(**section_dict)


# Define models
class StartRequest(BaseModel):
    topic: str
    type: str

class FeedbackRequest(BaseModel):
    workflow_id: str
    feedback: Any

class ProgressResponse(BaseModel):
    state: Dict[str, Any]


def serialize_section(section):
    if hasattr(section, "dict"):  # If section has a .dict() method
        return section.dict()
    elif isinstance(section, dict):  # If section is already a dictionary
        return section
    else:
        # Fallback: Convert section to dictionary manually
        return {
            "name": section.name,
            "description": section.description,
            "research": section.research,
            "content": section.content
        }
    
# Set writer model
writer_model = init_chat_model(model=Configuration.writer_model, model_provider=Configuration.writer_provider.value, temperature=0) 

# Nodes
async def generate_report_plan(state: ReportState, config: RunnableConfig):
    try:
        # Inputs
        topic = state["topic"]
        report_type = config["configurable"].get("report_type", "marketing")

        feedback = state.get("feedback_on_report_plan", None)
        # Get configuration
        configurable = Configuration.from_runnable_config(config)
        report_structure = configurable.report_structure
        number_of_queries = configurable.number_of_queries

        # Generate search query
        structured_llm = writer_model.with_structured_output(Queries)

        # Format system instructions
        system_instructions_query =  report_planner_query_writer_instructions.format(topic=topic, report_organization=report_structure, number_of_queries=number_of_queries)

        # Generate queries  
        results = structured_llm.invoke([SystemMessage(content=system_instructions_query)] + [HumanMessage(content="Generate search queries that will help with planning the sections of the report.")])
       
        # Web search
        query_list = [query.search_query for query in results.queries]
        # Handle search API
        if isinstance(configurable.search_api, str):
            search_api = configurable.search_api
        else:
            search_api = configurable.search_api.value

        # Search the web
        if search_api == "tavily":
            search_results = await tavily_search_async(query_list)
            source_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=False)
        elif search_api == "perplexity":
            search_results = perplexity_search(query_list)
            source_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=False)
        else:
            raise ValueError(f"Unsupported search API: {configurable.search_api}")

        # Format system instructions
        system_instructions_sections = report_planner_instructions.format(topic=topic, report_organization=report_structure, context=source_str, feedback=feedback)

        # Set the planner provider
        if isinstance(configurable.planner_provider, str):
            planner_provider = configurable.planner_provider
        else:
            planner_provider = configurable.planner_provider.value

        # Set the planner model
        planner_llm = init_chat_model(model=Configuration.planner_model, model_provider=planner_provider, temperature=0)

        # Generate sections 
        structured_llm = planner_llm.with_structured_output(Sections)
        report_sections = structured_llm.invoke([SystemMessage(content=system_instructions_sections)] + [HumanMessage(content="Generate the sections of the report. Your response must include a 'sections' field containing a list of sections. Each section must have: name, description, plan, research, and content fields.")])

        # Get sections
        sections = report_sections.sections

        return {"sections": sections}
    except Exception as e:
        logger.error(f"Error in generate_report_plan: {e}")
        raise
def human_feedback(state: ReportState, config: RunnableConfig) -> Command[Literal["generate_report_plan","build_section_with_web_research"]]:
    """ Get feedback on the report plan """

    # Get sections
    sections = state['sections']
    sections_str = "\n\n".join(
        f"Section: {section.name}\n"
        f"Description: {section.description}\n"
        f"Research needed: {'Yes' if section.research else 'No'}\n"
        for section in sections
    )

    # Get feedback on the report plan from interrupt

    feedback = interrupt(f"Please provide feedback on the following report plan. \n\n{sections_str}\n\n Does the report plan meet your needs? Pass 'true' to approve the report plan or provide feedback to regenerate the report plan:")

    # If the user approves the report plan, kick off section writing
    # if isinstance(feedback, bool) and feedback is True:
    if isinstance(feedback, bool):
        # Treat this as approve and kick off section writing
        return Command(goto=[
            Send("build_section_with_web_research", {"section": s, "search_iterations": 0}) 
            for s in sections 
            if s.research
        ])
    
    # If the user provides feedback, regenerate the report plan 
    elif isinstance(feedback, str):
        # treat this as feedback
        return Command(goto="generate_report_plan", 
                       update={"feedback_on_report_plan": feedback})
    else:
        raise TypeError(f"Interrupt value of type {type(feedback)} is not supported.")
def generate_queries(state: SectionState, config: RunnableConfig):
    """ Generate search queries for a report section """

    # Get state 
    section = state["section"]
    report_type = config["configurable"].get("report_type", "marketing")

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    number_of_queries = configurable.number_of_queries

    # Generate queries 
    structured_llm = writer_model.with_structured_output(Queries)

    # Format system instructions
    system_instructions = query_writer_instructions.format(section_topic=section.description, number_of_queries=number_of_queries)

    # Generate queries  
    queries = structured_llm.invoke([SystemMessage(content=system_instructions)]+[HumanMessage(content="Generate search queries on the provided topic.")])

    return {"search_queries": queries.queries}

async def search_web(state: SectionState, config: RunnableConfig):
    """ Search the web for each query, then return a list of raw sources and a formatted string of sources."""
    # Get state 
    search_queries = state["search_queries"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)

    # Web search
    query_list = [query.search_query for query in search_queries]
    
    # Handle both cases for search_api:
    # 1. When selected in Studio UI -> returns a string (e.g. "tavily")
    # 2. When using default -> returns an Enum (e.g. SearchAPI.TAVILY)
    if isinstance(configurable.search_api, str):
        search_api = configurable.search_api
    else:
        search_api = configurable.search_api.value

    # Search the web
    if search_api == "tavily":
        search_results = await tavily_search_async(query_list)
        source_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=5000, include_raw_content=True)
    elif search_api == "perplexity":
        search_results = perplexity_search(query_list)
        source_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=5000, include_raw_content=False)
    else:
        raise ValueError(f"Unsupported search API: {configurable.search_api}")

    return {"source_str": source_str, "search_iterations": state["search_iterations"] + 1}

def write_section(state: SectionState, config: RunnableConfig) -> Command[Literal[END,"search_web"]]:
    """ Write a section of the report """

    # Get state 
    section = state["section"]
    source_str = state["source_str"]
    report_type = config["configurable"].get("report_type", "marketing")

    # Get configuration
    configurable = Configuration.from_runnable_config(config)

    # Format system instructions
    system_instructions = section_writer_instructions.format(section_title=section.name, section_topic=section.description, context=source_str, section_content=section.content)

    # Generate section  
    section_content = writer_model.invoke([SystemMessage(content=system_instructions)]+[HumanMessage(content="Generate a report section based on the provided sources.")])
    
    # Write content to the section object  
    section.content = section_content.content

    # Grade prompt 
    section_grader_instructions_formatted = section_grader_instructions.format(section_topic=section.description,section=section.content)

    # Feedback 
    structured_llm = writer_model.with_structured_output(Feedback)
    feedback = structured_llm.invoke([SystemMessage(content=section_grader_instructions_formatted)]+[HumanMessage(content="Grade the report and consider follow-up questions for missing information:")])

    if feedback.grade == "pass" or state["search_iterations"] >= configurable.max_search_depth:
        # Publish the section to completed sections 
        return  Command(
        update={"completed_sections": [section]},
        goto=END
    )
    else:
        # Update the existing section with new content and update search queries
        return  Command(
        update={"search_queries": feedback.follow_up_queries, "section": section},
        goto="search_web"
        )
    
def write_final_sections(state: SectionState):
    """ Write final sections of the report, which do not require web search and use the completed sections as context """
    # Get state 
    section = state["section"]
    completed_report_sections = state["report_sections_from_research"]

    # Format system instructions
    system_instructions = final_section_writer_instructions.format(section_title=section.name, section_topic=section.description, context=completed_report_sections)

    # Generate section  
    section_content = writer_model.invoke([SystemMessage(content=system_instructions)]+[HumanMessage(content="Generate a report section based on the provided sources.")])
    
    # Write content to section 
    section.content = section_content.content

    # Write the updated section to completed sections
    return {"completed_sections": [section]}

def gather_completed_sections(state: ReportState):
    """ Gather completed sections from research and format them as context for writing the final sections """    
    logger.info("Executing node: gather_completed_sections")
    # List of completed sections
    completed_sections = state["completed_sections"]

    # Format completed section to str to use as context for final sections
    completed_report_sections = format_sections(completed_sections)

    return {"report_sections_from_research": completed_report_sections}

def initiate_final_section_writing(state: ReportState):
    """ Write any final sections using the Send API to parallelize the process """    
    # Kick off section writing in parallel via Send() API for any sections that do not require research
    return [
        Send("write_final_sections", {"section": s, "report_sections_from_research": state["report_sections_from_research"]}) 
        for s in state["sections"] 
        if not s.research
    ]

def compile_final_report(state: ReportState):
    """ Compile the final report """    
    # Get sections
    sections = state["sections"]
    completed_sections = {s.name: s.content for s in state["completed_sections"]}

    # Update sections with completed content while maintaining original order
    for section in sections:
        section.content = completed_sections[section.name]

    # Compile final report
    all_sections = "\n\n".join([s.content for s in sections])

    return {"final_report": all_sections}

# Report section sub-graph -- 

# Add nodes 
section_builder = StateGraph(SectionState, output=SectionOutputState)
section_builder.add_node("generate_queries", generate_queries)
section_builder.add_node("search_web", search_web)
section_builder.add_node("write_section", write_section)

# Add edges
section_builder.add_edge(START, "generate_queries")
section_builder.add_edge("generate_queries", "search_web")
section_builder.add_edge("search_web", "write_section")

# Outer graph -- 

# Add nodes
# Outer graph
builder = StateGraph(ReportState, input=ReportStateInput, output=ReportStateOutput, config_schema=Configuration)
builder.add_node("generate_report_plan", generate_report_plan)
builder.add_node("human_feedback", human_feedback)
builder.add_node("build_section_with_web_research", section_builder.compile())
builder.add_node("gather_completed_sections", gather_completed_sections)
builder.add_node("write_final_sections", write_final_sections)
builder.add_node("compile_final_report", compile_final_report)

# Add edges
builder.add_edge(START, "generate_report_plan")
builder.add_edge("generate_report_plan", "human_feedback")
builder.add_edge("build_section_with_web_research", "gather_completed_sections")
builder.add_conditional_edges("gather_completed_sections", initiate_final_section_writing, ["write_final_sections"])
builder.add_edge("write_final_sections", "compile_final_report")
builder.add_edge("compile_final_report", END)


checkpointer = MemorySaver()
graph = builder.compile(
   checkpointer=checkpointer
)




@app.post("/api/start")
async def start_workflow(request: StartRequest):
    # ✅ Initialize full state
    initial_state = {
        "topic": request.topic,
        "feedback_on_report_plan": "",
        "sections": [],
        "completed_sections": [],
        "report_sections_from_research": "",
        "final_report": "",
    }

    # ✅ Insert into MongoDB (MongoDB generates `_id` automatically)
    workflow_id = str(uuid.uuid4())

    thread_config = {"configurable": {"thread_id": workflow_id, "report_type" : request.type}}
    # ✅ Execute workflow
    async for step_result in graph.astream(initial_state, config=thread_config):

        # ✅ Remove `_id` before updating state (prevents TypeError)
        initial_state.pop("_id", None)

        # ✅ Merge `step_result` without overwriting missing fields
        updated_state = initial_state.copy()  # Start with full state
        # Update the state based on the step result
        for node_name, node_output in step_result.items():
            if node_output:  # Ensure the node output is not empty
                # Merge the node output into the current state
                if isinstance(node_output, dict):
                    updated_state.update(node_output)

        # ✅ Convert objects to dictionary format before storing in MongoDB
        if "sections" in updated_state:
            updated_state["sections"] = [serialize_section(section) for section in updated_state["sections"]]
        if "completed_sections" in updated_state:
            updated_state["completed_sections"] = [serialize_section(section) for section in updated_state["completed_sections"]]

        return {
            "status": "completed",
            "workflow_id": workflow_id,
            "result": updated_state
        }

    

    





@app.post("/api/feedback")
async def provide_feedback(request: FeedbackRequest):
    # ✅ Convert `workflow_id` from string to `ObjectId`

    updated_state = {}
    thread_config = {"configurable": {"thread_id": str(request.workflow_id)}}
    async for step_result in graph.astream(
        Command(resume=request.feedback),
        config=thread_config
    ):
        
        # ✅ Merge `step_result` without overwriting missing fields
        for node_name, node_output in step_result.items():
            if node_output:  # Ensure the node output is not empty
                if isinstance(node_output, dict):
                    updated_state.update(node_output)

        # ✅ Convert objects to dictionary format before storing in MongoDB
        if "sections" in updated_state:
            updated_state["sections"] = [serialize_section(section) for section in updated_state["sections"]]
        if "completed_sections" in updated_state:
            updated_state["completed_sections"] = [serialize_section(section) for section in updated_state["completed_sections"]]


    return {"status": "workflow_resumed", "result": updated_state}


@app.get("/{full_path:path}")
async def serve_static_or_index(full_path: str):
    file_path = os.path.join("./src/open_deep_research/dist", full_path)
    
    logging.debug(f"Requested path: {full_path}")
    logging.debug(f"Serving file: {file_path}")

    if os.path.exists(file_path) and not os.path.isdir(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        logging.debug(f"Detected MIME type: {mime_type}")
        return FileResponse(file_path, media_type=mime_type)

    logging.debug("Serving index.html (SPA fallback)")
    return FileResponse("./src/open_deep_research/dist/index.html")

# Serve the entire frontend build folder
# app.mount("/", StaticFiles(directory="src/open_deep_research/dist", html=True), name="static")


import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pytest
# from ai import ingest_resume,ingest_resume_for_recommendataions,get_recommendation
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from config import settings
from langchain_openai import ChatOpenAI,OpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
import json
from agents import Agent, Runner
from agents import function_tool
from agents import SQLiteSession
from agents import set_default_openai_key
from typing import Literal,Tuple
import random
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents import set_trace_processors
from braintrust import init_logger,load_prompt
from braintrust.wrappers.openai import BraintrustTracingProcessor

#######
db = {
    "job_descriptions": {
        1: "I need an AI Engineer who knows langchain"
    },
    "state": {
        "session123": {
            "skills": [],
            "evaluation": [] # list of typles (Skill, True/False), eg: [("Python", True)]
        }
    }
}

class ValidationResult(BaseModel):
    correct: bool
    reasoning: str

llm = ChatOpenAI(model="gpt-5.1",api_key=settings.OPENAI_API_KEY,temperature=0)

@function_tool
def extract_skills(session_id: str, job_id: int) -> list[str]:
    print("In extract skills")
    db["state"][session_id]["skills"] = ["Python", "SQL", "System Design"]
    print(db)
    return ["Python", "SQL", "System Design"]

@function_tool
def update_evaluation(session_id: str, skill: str, evaluation_result: bool) -> bool:
    evaluation = (skill, evaluation_result)
    if skill not in db["state"][session_id]["evaluation"]:
        db["state"][session_id]["evaluation"].append(evaluation)

def test_run_orchestrator_agent(session_id,job_id):

    tools_mapping = {
        "extract_skills": extract_skills,
        "update_evaluation": update_evaluation,
        "transfer_to_skill_evaluator":transfer_to_skill_evaluator
    }

    
    ORCHESTRATOR_SYSTEM_PROMPT = """
    You are an interview orchestrator. Your goal is to evaluate the candidate on the required skills.

    # INSTRUCTIONS

    Follow the following steps exactly

    1. Extract key skills from the job description using extract_skills tool
    2. Then welcome the candidate, explain the screening process and ask the candidate if they are ready 
    3. Then, for EACH skill in the list, use transfer_to_skill_evaluator tool to delegate evaluation
    4. Once you get the response, use the update_evaluation tool to save the evaluation result into the database
    5. Once all skills are evaluated, mention that the screening is complete and thank the candidate for their time

    # OUTPUT FORMAT

    Output as a JSON following the JSON schema below:

    ```
    {{
        "type": "object",
        "properties": {{
            "response": {{ "type": "string" }}
            "tool_name": {{ "type": "string"}},
            "tool_params": {{
                "type": "array",
                "items": {{
                    "type": "object",
                    "properties": {{
                        "param": {{ "type": "string" }},
                        "value": {{ "type": "string" }}
                    }}
                }}
            }}
        }},
        "required": []
    }}

    Use the "tool_name" and "tool_params" properties to execute a tool and use the "response" property to reply to the user without a tool call. 

    # TOOLS

    You have access to the following tools

    1. `extract_skills(session_id: str, job_id: int) -> list[str]`

    Given a job_id, lookup job descriptiona and extract the skills for that job description

    2. `update_evaluation(session_id: str, skill: str, evaluation_result: bool) -> bool`

    This function takes the session_id, skill, and the evaluation result and saves it to the database. Returns success or failure (bool)

    3. `transfer_to_skill_evaluator(session_id, skill: str) -> bool`

    This function takes a skill, evaluates it and returns the evaluation result for the skill as a boolean pass / fail
    """

    ORCHESTRATOR_USER_PROMPT = """
    Start an interview for the following values:

    session_id: {session_id}
    job_id: {job_id}

    Begin by welcoming the applicant, extracting the key skills, then evaluate each one.
    """

    llm = ChatOpenAI(
        model = "gpt-5.1",
        api_key= settings.OPENAI_API_KEY,
        temperature=0
    )

    chat_message = (
        ChatPromptTemplate.from_messages([
            ("system",ORCHESTRATOR_SYSTEM_PROMPT),
            ("human",ORCHESTRATOR_USER_PROMPT) 
        ])
    )
    
    chain = chat_message | llm
    
    output = chain.invoke({"session_id": session_id,"job_id": job_id})
    print(output)
    while True:        
        data = json.loads(output.content)
        if data:
            print(output.content)
        if data["tool_name"] != "":
            tool_name = data["tool_name"]
            params =  {item["param"]: item["value"] for item in data["tool_params"]}

            result_content = tools_mapping[tool_name](**params)
            print(result_content)
            
            chat_message.append(("assistant",output.content.replace("{","{{").replace("}","}}")))
            chat_message.append(("ai",str(result_content))) 
        
        else:
            user_reply = input("User : ")
            if user_reply == "exit":
                break
            chat_message.append(("human",user_reply))

        chain = chat_message | llm
        output = chain.invoke({"session_id": session_id,"job_id": job_id})

    print("Final answer : ",db)

# def main():
#     # test_run_orchestrator_agent("session123",1)
#     run_orchestrator("session123",1)

@function_tool
def get_question(topic: str, difficulty: Literal['easy', 'medium', 'hard']) -> str:
    question_bank = {
    "python": {
        "easy": [
            "If `d` is a dictionary, then what does `d['name'] = 'Siddharta'` do?",
                "if `l1` is a list and `l2` is a list, then what is `l1 + l2`?",
            ],
            "medium": [
                "How do you remove a key from a dictionary?",
                "How do you reverse a list in python?"
            ],
            "hard": [
                "If `d` is a dictionary, then what does `d.get('name', 'unknown')` do?",
                "What is the name of the `@` operator (Example `a @ b`) in Python?"
            ]
        },
        "sql": {
            "easy": [
                "What does LIMIT 1 do at the end of a SQL statement?",
                "Explain this SQL: SELECT product_name FROM products WHERE cost < 500'"
            ],
            "medium": [
                "What is a view in SQL?",
                "How do we find the number of records in a table called `products`?"
            ],
            "hard": [
                "What is the difference between WHERE and HAVING in SQL?",
                "Name a window function in SQL"
            ]
        },
        "system design": {
            "easy": [
                "Give one reason where you would prefer a SQL database over a Vector database",
                "RAG requires a vector database. True or False?"
            ],
            "medium": [
                "Give one advantage and one disadvantage of chaining multiple prompts?",
                "Mention three reasons why we may not want to use the most powerful model?"
            ],
            "hard": [
                "Mention ways to speed up retrieval from a vector database",
                "Give an overview of Cost - Accuracy - Latency tradeoffs in an AI system"
            ]
        }
    }
    question = random.choice(question_bank[topic.lower()][difficulty.lower()])
    return question

@function_tool
def check_answer(skill: str, question: str, answer: str):
    # VALIDATION_PROMPT = """
    #     Evaluate the given interview answer. 

    #     # Instructions

    #     Provide a JSON response with: 
    #     - correct: true or false depending if the answer was correct or not for the given question in the context of the given skill. 
    #     - reasoning: brief explanation (2-3 sentences) 

    #     For subjective answers, mark the answer true if the majority of the important points have been mentioned.

    #     Answers are expected to be brief, so be rigorous but fair. Look for technical accuracy and clarity. 

    #     # Output Format

    #     {format_instructions}

    #     # Task

    #     Skill: {skill} 
    #     Question: {question} 
    #     Answer: 
    #     {answer}

    # Evaluation:"""

    # analysis_parser = PydanticOutputParser(pydantic_object=ValidationResult)
    
    # prompt = PromptTemplate.from_template(VALIDATION_PROMPT).partial(format_instructions = analysis_parser.get_format_instructions())

    # chain = prompt | llm | analysis_parser
    
    # result = chain.invoke({"skill": skill,"question": question,"answer":answer})

    # print(result)
    # return result.model_dump_json()
    """Given a question and an answer for a particular skill, validate if the answer is correct. Returns a tuple (correct, reasoning)"""

    prompt = load_prompt(project="Prodapt", slug="check-the-answer-prompt-f166")
    details = prompt.build(skill=skill, question=question, answer=answer)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-5.1", temperature=0,
        response_format=details["response_format"],
        messages=details["messages"]
    )
    return json.loads(response.choices[0].message.content)

def run_evaluation_agent(session_id, skill):
    EVALUATION_SYSTEM_PROMPT = """
    {RECOMMENDED_PROMPT_PREFIX}
    You are a specialised skill evaluator. Your job is to evaluate the candidate's proficiency in a given skill

    1. Identify which skill you're evaluating (it will be mentioned in the conversation)
    2. Start with one skill and then evalution for one skill is done then start with another skill.
    3. Use the get_question  'get_question(topic: str, difficulty: Literal['easy', 'medium', 'hard']) -> str' tool to get a question to ask (start with 'medium' difficulty). Ask the question verbatim, DO NOT MODIFY it in any way
    4. Ask question to candidate return by get_question tool.
    5. After each candidate answer, use check_answer 'check_answer(skill: str, question: str, answer: str):' tool to evaluate.
    6. Decide the next question:
    - If the check_answer tool returned correct, choose the next higher difficulty, without going above 'hard'
    - If the check_answer tool returned incorrect, choose the lower difficulty, without going below 'easy'
    - Stop after 3 questions MAXIMUM
    6. If the correctly answered two of the three questions, then they pass, otherwise they fail

    DECISION RULES:
    - Maximum 3 questions per skill

    OUTPUT:

    After the evaluation is complete, return the pass/fail in a json object with the following properties
    - result: true or false
    """

    EVALUATION_USER_PROMPT = """
    Evaluate the user on the following skill: {skill}
    """
    session = SQLiteSession(f"session - {session_id}")
    set_default_openai_key(settings.OPENAI_API_KEY)

    agent = Agent(
        name = "Evaulator Agent",
        instructions=EVALUATION_SYSTEM_PROMPT,
        model = "gpt-5.1",
        tools=[get_question,check_answer]
    )

    user_input = EVALUATION_USER_PROMPT.format(skill=skill)

    while user_input != "bye":
        result = Runner.run_sync(agent, user_input, session=session)
        print(result.final_output)
        user_input = input("User : ")

# run_evaluation_agent("Session123",['python','sql','system design'])
@function_tool 
def get_next_skill_to_evaluate(session_id: str) -> str:
    """Retrieve the next skill to evaluate. Returns None if there are no more skills to evaluate"""
    all_skills = db["state"][session_id]["skills"]
    evaluated = db["state"][session_id]["evaluation"]
    print("evaluated : ",evaluated)
    print("all_skills : ",all_skills)
    evaluated_skills = [item[0] for item in evaluated]
    remaining_skills = set(all_skills) - set(evaluated_skills)

    print("remaining_skills : ",remaining_skills)
    try:
        next_skill = remaining_skills.pop()
        print("NEXT SKILL TOOL", next_skill)
        return next_skill
    except KeyError:
        print("No more skills")
        return None

def run(session_id, job_id):
    session = SQLiteSession(f"session - {session_id}")

    ORCHESTRATOR_SYSTEM_PROMPT = """
    {RECOMMENDED_PROMPT_PREFIX}

    You are an interview orchestrator. Your goal is to evaluate the candidate on the required skills.

    # INSTRUCTIONS

    Follow the following steps exactly

    1. Extract key skills from the job description using extract_skills tool
    2. Then welcome the candidate, explain the screening process and ask the candidate if they are ready 
    3. Then, use the get_next_skill_to_evaluate tool to get the skill to evaluate
    4. If the skill is not `None` then hand off to the "Skills Evaluator Agent" to perform the evaluation. Pass in the skill to evaluate
    4. Once you get the response, use the update_evaluation tool to save the evaluation result into the database
    5. Once get_next_skill_to_evaluate returns `None`, return a json with a single field `status` set to "done" to indicate completion
    """

    ORCHESTRATOR_USER_PROMPT = """Start an interview for the following values:
    
    session_id: {session_id}
    job_id: {job_id}
    
    Begin by welcoming the applicant, extracting the key skills, then evaluate each one."""

    EVALUATION_SYSTEM_PROMPT = """
    {RECOMMENDED_PROMPT_PREFIX}
    You are a specialised skill evaluator. Your job is to evaluate the candidate's proficiency in a given skill

    1. Identify which skill you're evaluating (it will be mentioned in the conversation)
    2. Start with one skill and then evalution for one skill is done then start with another skill.
    3. Use the get_question  'get_question(topic: str, difficulty: Literal['easy', 'medium', 'hard']) -> str' tool to get a question to ask (start with 'medium' difficulty). Ask the question verbatim, DO NOT MODIFY it in any way
    4. Ask question to candidate return by get_question tool.
    5. After each candidate answer, use check_answer 'check_answer(skill: str, question: str, answer: str):' tool to evaluate.
    6. Decide the next question:
    - If the check_answer tool returned correct, choose the next higher difficulty, without going above 'hard'
    - If the check_answer tool returned incorrect, choose the lower difficulty, without going below 'easy'
    - Stop after 3 questions MAXIMUM
    6. If the correctly answered two of the three questions, then they pass, otherwise they fail

    DECISION RULES:
    - Maximum 3 questions per skill

    OUTPUT:

    After the evaluation is complete, return the pass/fail in a json object with the following properties
    - result: true or false
    """

    EVALUATION_USER_PROMPT = """
    Evaluate the user on the following skill: {skill}
    """
    session = SQLiteSession(f"session - {session_id}")
    set_default_openai_key(settings.OPENAI_API_KEY)

    evaluation_agent = Agent(
        name = "Skills Evaluator Agent",
        instructions=EVALUATION_SYSTEM_PROMPT.format(RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX),
        model = "gpt-5.1",
        tools=[get_question,check_answer]
    )

    orchestrator_agent = Agent(
        name = "Interview Orchestrator Agent",
        instructions=ORCHESTRATOR_SYSTEM_PROMPT.format(RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX),
        model = "gpt-5.1",
         tools=[extract_skills, get_next_skill_to_evaluate, update_evaluation]
    )

    orchestrator_agent.handoffs = [evaluation_agent]
    evaluation_agent.handoffs = [orchestrator_agent]
    user_input = ORCHESTRATOR_USER_PROMPT.format(job_id=job_id, session_id=session_id)
    agent = orchestrator_agent
    while user_input != 'bye':
        result = Runner.run_sync(agent, user_input, session=session, max_turns=20)
        agent = result.last_agent
        print(result.final_output)
        user_input = input("User: ")

def main():
    set_default_openai_key(settings.OPENAI_API_KEY)
    set_trace_processors([BraintrustTracingProcessor(init_logger("Prodapt",api_key=settings.BRAINTRUST_API_KEY))])
    job_id = 1
    session_id = "session123"
    run(session_id, job_id)
    print("FINAL EVALUATION STATE", db)

main()
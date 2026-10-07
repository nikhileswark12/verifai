from typing import List
from app.providers.llm.base import LLMProvider
from app.services.prompt_loader import load_prompt


async def expand_query(claim: str, llm: LLMProvider) -> List[str]:
    """
    Expand a sub-claim into multiple targeted search queries using LLM.
    """
    system_prompt = load_prompt("researcher")
    user_prompt_template = load_prompt("query_expander")
    
    user_prompt = user_prompt_template.replace("{claim}", claim)
    
    response_data = await llm.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
    
    queries = response_data.get("queries", [])
    if not isinstance(queries, list):
        queries = []
        
    # Validate and normalize
    valid_queries = []
    seen = set()
    for q in queries:
        if not isinstance(q, str):
            continue
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            valid_queries.append(q_clean)
            seen.add(q_clean.lower())
            
    # Ensure list length is between 3-5
    if len(valid_queries) < 3 or len(valid_queries) > 5:
        raise ValueError(f"Query expansion must generate between 3 and 5 queries, got {len(valid_queries)}")
        
    return valid_queries

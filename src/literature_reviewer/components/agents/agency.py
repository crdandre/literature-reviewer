"""
Agencies are teams of Agents
just like the CIA, but for writing systematic literature reviews
Can include reflection at the agency level (i.e., reviewer agent
gets outputs from all other agents, reviews them relative to reqs,
decides whether the task is complete...)

Possible hierarchies
1. Planner (o1 or CoT-encouraged 4o/sonnet) --> creates a list of subtasks
   suited to each agency member
2. Workers (Possible)
    1. Comprehension - encourages self-informed understanding of the task
    2. Anchoring
    3. Logic
    4. Cognition
    5. General
3. Aggregation
4. Verification

The weird/confusing bit is that each agent unto itself has reflection capabilities.
I'm probably banking on sentience arising from hierarchical reflection, or wasting
credits.

"""
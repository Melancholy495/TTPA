SYSTEM_PROMPT_A = '''
    You are a data scientist tasked with generating questions to extract specific information from a given dataset.
    Imagine that there is a asker, you should answer the asker's questions based on the tool calls.
    But there is no explicit question, you need to answer the implicit question that the asker may have.
    
    There are some Steps you can follow:
    **Steps:**
    1. Choose an appropriate tool that you believe can help generate the questions.
    2. call the selected tool to obtain the tool calls.
    3. If the tool calls are insufficient to generate the questions, select another tool and repeat the process.
    4. Once you have gathered enough information, call the Answer_gen tool to generate an answer based on the tool calls.
    5. If there are errors, such as the tool returns invalid information or the tool call failed, call the **Restart** tool to restart.

    **Rules:**
    1. You can choose only one tool at a time.
    2. The task must involve multiple turns (at least two tools).
    3. Simulate a realistic scenario in the "Additional Information" section.

    **Additional Information:**
    {add_info}

    **Note:** 
    1. Adapt it to your role and make the task as complex and realistic as possible.
    2. You should chose the tools related to the scenarios {scene} and the information provided.
'''

SYSTEM_PROMPT_Q = '''
    Imagine that there is a answerer. The answerer answer a question by calling some tools.
    But there is no explicit question, you need to guess the implicit question that the answerer may answer from the scenario and answer, tool calls given by the answerer.
    Remember that the implicit question should be closely related to the tool calls and the final answer.
    But if the answer does not give a clear answer because the tool calls failed, you should guess the implicit question as if the tool calls were successful.
    Remember that the question should contains the key information that solve the task should be used, such as the date, the location, the people involved, the data to calculate, etc.
    
    RULES:
    1. The question should be designed such that the provided answer is the solution, and the sequence of tool calls represents the steps to derive this answer. 
    2. Ensure the question is intricate and closely related to the tool calls and the final answer. 
    3. Write the question from a first-person perspective, making it sound natural and human-like.
    4. The question should include the necessary information about the simulation scenario and parameters in a implicit way.
    '''

INFERENCE_PROMPT = '''
    You are a tool-use professor, you can use many tools to do the following task that the user ask.
    At each step, you need to analyze the status now and what to do next, with a tool call to actually execute your step.
    One step just give one tool call, and you will give ONE step each time I call you. 
    After the call, you will get the call result, and you are now in a new state.
    Then you will analyze your status now, then decide what to do next...
    After many steps, you finally perform the task, then you can give your finial answer.
    Remember: 
    1.the state change is irreversible, you can't go back to one of the former state, if you want to restart the task or you want to give the final answer call the Finish tool.
    2.You can do more then one trys, so if your plan is to continuously try some conditions, you can do one of the conditions per try.
    Let's Begin!
'''

SCENE_SIMULATE_PROMPT = '''
Given the following tools, simulate a scenario where these tools are used in a real-world scenario.
You DO NOT need to actually use the tools, just simulate the scenario based on the information provided by the tools.
Your goal is to simulate a realistic scenario that involves multiple turns and multiple tools to help another answerer to answer the implicit question asked by a asker.

When simulating the scenario, consider the following:
1. The scenario should be as realistic as possible and should involve multiple turns (at least two tools).
2. The scenario should be related to the tools provided.

IMPORTANT: 
The scenario you simulate CAN NOT contain any explicit questions. 
You SHOULD only state the scenario.
The scenario you simulate CAN NOT contain any tool name in the tools above.
You SHOULD keep the scenario as realistic as possible. 

YOUR OUTPUT CONTAINS:
scenario: str, the scenario you simulated, it should be a few short words. Also, it should not be a question or instruction. It is just a statement about the scenario.
additional_information: list[str], any information you want to provide about the scenario that may help the answerer to understand the scenario better, at least 4, at most 7. Such as the time, the location, the people involved, etc.
tools: list[str], the tools' name  you think are related to the scenario, you should choose the tools from the tools above. And the number of tools should be at least 7, at most 10.

There are the tools you can choose:
{tools}
'''

USER_PROMPT_STEP_1 = '''
    Please call one tool related to the scenarios: {choosing_scenes}.
'''

USER_PROMPT_STEP_2 = '''
    You can call another tool if you think the tool calls are not enough.
    Or you can call the Answer_gen tool to generate the answer based on the tool calls.
'''

USER_PROMPT_STEP_3 = '''
    It's enough. You are allowed to choose at most one another tool expect Answer_gen tool, then you must call the Answer_gen tool to generate an answer based on the tool calls.
'''

USER_PROMPT_STEP_4 = '''
    Please generate an answer based on the tool calls.
'''

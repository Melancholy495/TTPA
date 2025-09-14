
FINISH = {
    "type": "function",
    "function": {
            "name": "Finish",
            "description": "If you believe that you have obtained a result that can answer the task, please call this function to provide the final answer. Alternatively, if you recognize that you are unable to proceed with the task in the current state, call this function to restart. Remember: you must ALWAYS call this function at the end of your attempt, and the only part that will be shown to the user is the final answer, so it should contain sufficient information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "return_type": {
                        "type": "string",
                        "enum": ["give_answer","give_up_and_restart"],
                    },
                    "final_answer": {
                        "type": "string",
                        "description": "The final answer you want to give the user. You should have this field if \"return_type\"==\"give_answer\"",
                    }
                },
                "required": ["return_type"],
            }
        }
    }

Answer_gen = {
    "type": "function",
    "function": {
        "name": "Answer_gen",
        "description": "If you believe that you have get enough information to generate the task, please call this function to provide a final answer, which includes the final answer based on the tool calls and the relevant tool calls.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The final answer you should generate based on the tool calls you have made so far.",
                }
            },
            "required": ["answer"]
        }
    }
}

Question_gen = {
    "type": "function",
    "function": {
        "name": "Question_gen",
        "description": "If you have generated the answer and want to generate the question based on the tool calls and the final answer, call this function to provide the question you have generated based on the tool calls and the final answer.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question you generated based on the tool calls and the final answer.",
                }
            },
            "required": ["question"]
        }
    }
}

Restart = {
    "type": "function",
    "function": {
        "name": "Restart",
        "description": "IF there are too many errors that can not get enough information, please call this function to restart the task from scratch.",
        "parameters": {
            "type": "object",
            "properties": {
                "error_summary": {
                    "type": "string",
                    "description": "A summary of the error detected, describing what went wrong during the process. It should capture essential details to help understand the issue.",
                }
            },
            "required": ["error_summary"]
        }
    }
}

Backward = {
    "type": "function",
    "function": {
        "name": "Backward",
        "description": "If you detect an error during the process and decide to take corrective actions, call this function to backtrack to a specific message to continue from there, retaining previous error summaries.",
        "parameters": {
            "type": "object",
            "properties": {
                "error_summary": {
                    "type": "string",
                    "description": "A summary of the error detected, describing what went wrong during the process. It should capture essential details to help understand the issue.",
                },
                "backtrack_to_message": {
                    "type": "integer",
                    "description": "The message numbers start at 1, including the system prompt. The backtrack_to_message should be bigger than 2. The message number to backtrack. This should indicate the message where the process will resume."
                },
                "error_details": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "message_number": {
                                "type": "integer",
                                "description": "The message number where the error was detected.",
                            },
                            "error_type": {
                                "type": "string",
                                "description": "A short identifier of the error type, e.g., 'incomplete_data', 'invalid_format', or 'misinterpreted_task'.",
                            },
                            "resolution_attempt": {
                                "type": "string",
                                "description": "A description of any attempts to resolve the error before backtracking or restarting.",
                            }
                        },
                        "required": ["message_number", "error_type", "resolution_attempt"]
                    },
                    "description": "Detailed information on detected errors, including specific messages, error types, and any previous resolution attempts.",
                }
            },
            "required": ["error_summary", "backtrack_to_message", "error_details"]
        }
    }
}
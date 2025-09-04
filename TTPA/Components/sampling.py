import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from time import sleep

from openai import OpenAI
import argparse
import math
from tqdm import tqdm

type_mapping = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None)
}

def get_test_data(input_dir):
    with open(input_dir, "r") as f:
        input_data = json.load(f)
    return input_data

def chat_complete(messages, tools, model_name, api_key):
    if "local" in model_name:
        client = OpenAI(base_url="", api_key=api_key)
    elif "lora" in model_name or "TTPO" in model_name:
        client = OpenAI(base_url="", api_key=api_key)
    else:
        client = OpenAI(base_url="", api_key=api_key)
    result = client.chat.completions.create(
        messages=messages,
        tools=tools,
        model=model_name,
        n=5
    )
    return result

def get_undo_task(data, check_file):
    undo_task = []
    done_task_ids = []
    with open(check_file, "r") as f:
        for line in f:
            done_task_ids.append(int(line.strip()))
    for i,task in enumerate(data):
        if task["id"] not in done_task_ids:
            undo_task.append(task)
    return undo_task

def evaluate(task):
    messages = task["conversations"]
    id = task["id"]
    system = task["system"]
    tools = json.loads(task["tools"])
    from random import uniform
    sleep(uniform(1, 5))
    for i, message in enumerate(messages):
        if "tool_calls" in message:
            scores = {}
            scored_tool_calls = []
            use_messages = messages[:i]
            answer = message
            use_messages.insert(0, {"role": "system", "content": system})
            answer_name = answer["tool_calls"][0]["function"]["name"]
            answer_input = json.loads(answer["tool_calls"][0]["function"]["arguments"])

            result = chat_complete(use_messages, tools, args.model_name, args.api_key)

            for j in range(len(result.choices)):
                return_data = result.choices[j].message
                if return_data.tool_calls is not None:
                    tool_name = result.choices[j].message.tool_calls[0].function.name
                    tool_input = json.loads(result.choices[j].message.tool_calls[0].function.arguments)
                    if not isinstance(tool_input, dict):
                        try:
                            tool_input = json.loads(tool_input)
                            result.choices[j].message.tool_calls[0].function.arguments = json.dumps(tool_input, ensure_ascii=False)
                        except Exception as e:
                            tool_input = {}
                    if {"name": tool_name, "arguments": tool_input} not in scored_tool_calls:
                        scored_tool_calls.append({"name": tool_name, "arguments": tool_input})
                    else:
                        continue
                    tool_des = [tool for tool in tools if tool["function"]["name"] == tool_name]
                    tool_des = tool_des[0]
                    if tool_name == answer_name and tool_input=={} and answer_input=={}:
                        score = 1
                    elif tool_name == answer_name and tool_input=={} and answer_input != {}:
                        score = 0
                    elif tool_name != answer_name and tool_input=={}:
                        score = 0
                    else:
                        score = compute_score(answer_name, answer_input, tool_name, tool_input, tool_des)
                    scores[j] = score
                else:
                    scores[j] = 0
            max_score = max(scores.values())
            reject = []
            chosen = {}
            if max_score < 0.8:
                for k in scores.keys():
                    if result.choices[k].message.tool_calls:
                        reject.append({"role": "assistant", "tool_calls":[{"type": "function", "id": result.choices[k].message.tool_calls[0].id, "function": {"name": result.choices[k].message.tool_calls[0].function.name, "arguments": result.choices[k].message.tool_calls[0].function.arguments}}]})
                    else:
                        reject.append({"role": "assistant", "content": result.choices[k].message.content})
                chosen = answer
            else:
                for k in scores.keys():
                    if result.choices[k].message.tool_calls:
                        if scores[k] < max_score:
                            reject.append({"role": "assistant", "tool_calls":[{"type": "function", "id": result.choices[k].message.tool_calls[0].id, "function": {"name": result.choices[k].message.tool_calls[0].function.name, "arguments": result.choices[k].message.tool_calls[0].function.arguments}}]})
                        elif scores[k] == max_score:
                            chosen = {"role": "assistant", "tool_calls":[{"type": "function", "id": result.choices[k].message.tool_calls[0].id, "function": {"name": result.choices[k].message.tool_calls[0].function.name, "arguments": result.choices[k].message.tool_calls[0].function.arguments}}]}
                    else:
                        reject.append({"role": "assistant", "content": result.choices[k].message.content})
            if reject != [] and chosen != {}:
                preference_data = {"id": id, "system": system, "history": use_messages[1:], "reject": reject, "chosen": chosen, "tools": tools}
                with open(args.output_dir+f"/{id}_{i}.json", "w") as f:
                    f.write(json.dumps(preference_data, indent=4, ensure_ascii=False))
    return id

def compute_score(answer_name, answer_input, tool_name, tool_input, tool_des):
    partial_score_name = 0
    partial_score_requried = 0
    partial_score_key = 0
    partial_score_value_type = 0
    partial_score_value = 0
    possible_args = tool_des["function"]["parameters"]["properties"].keys()
    requried_args = tool_des["function"]["parameters"]["required"]

    if answer_name == tool_name:
        partial_score_name += 1

    if requried_args:
        for requried_arg in requried_args:
            if requried_arg in answer_input:
                partial_score_requried += 1
        partial_score_requried = partial_score_requried/len(requried_args)
    else:
        partial_score_requried = 1

    for arg_key, arg_value in tool_input.items():
        if arg_key in possible_args:
            partial_score_key += 1
            expected_type_ = tool_des["function"]["parameters"]["properties"][arg_key]["type"]
            expected_type = type_mapping.get(expected_type_, None)
            if expected_type is None:
                raise ValueError(f"Unknown type: {expected_type_}")
            if isinstance(arg_value, expected_type):
                partial_score_value_type += 1

        if arg_key in answer_input:
            if arg_value == answer_input[arg_key]:
                partial_score_value += 1
            elif isinstance(arg_value, str) and isinstance(answer_input[arg_key], str):
                if arg_value.lower() == answer_input[arg_key].lower():
                    partial_score_value += 0.5
                if arg_value in answer_input[arg_key] or answer_input[arg_key] in arg_value:
                    partial_score_value += 0.5

    if len(tool_input) < len(answer_input):
        partial_score_key = partial_score_key/len(answer_input.keys())
        partial_score_value_type = partial_score_value_type/len(answer_input.keys())
        partial_score_value = partial_score_value/len(answer_input.keys())
    else:
        partial_score_key = partial_score_key/len(tool_input.keys())
        partial_score_value_type = partial_score_value_type/len(tool_input.keys())
        partial_score_value = partial_score_value/len(tool_input.keys())

    weights = {
        "name": 3,
        "required": 3,
        "key": 1,
        "value_type": 2,
        "value": 2
    }
    score = (weights["name"] * partial_score_name +
            weights["required"] * partial_score_requried +
            weights["key"] * partial_score_key +
            weights["value_type"] * partial_score_value_type +
            weights["value"] * partial_score_value)/sum(weights.values())

    return score

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=str, help='input directory')
    parser.add_argument('--output_dir', type=str, help='output directory')
    parser.add_argument('--model_name', type=str, help='model_name')
    parser.add_argument('--api_key', type=str, help='api_key')
    args = parser.parse_args()
    scores = {}
    result = 0
    test_data = get_test_data(args.input_dir)
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    futures = []
    if not os.path.exists("./statistic.txt"):
        with open("./statistic.txt", "w") as f:
            pass

    undo_task = get_undo_task(test_data, "./statistic.txt")
    with ThreadPoolExecutor(max_workers=16) as executor:
        with tqdm(total=len(undo_task), desc="Processing tasks") as pbar:
            for task in undo_task:
                future = executor.submit(evaluate, task)
                futures.append(future)

            lock = threading.Lock()
            for future in as_completed(futures):
                result = future.result()
                with lock:
                    with open(f"./statistic.txt", "a") as f:
                        f.write(f"{result}\n")
                pbar.update()


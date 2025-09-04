import ast
import importlib.util
import json
import re
import os
import random

from .PROMPTS import SYSTEM_PROMPT_A, USER_PROMPT_STEP_1
from .Special_Function import Question_gen, Answer_gen, Restart, Backward, FINISH
from termcolor import colored
from transformers.utils import get_json_schema


def initial_task(scene, generator):
    kwargs, choosing_tools = scene.simulate()
    print(colored(kwargs, "yellow"))
    tool_num = random.randint(4, 7)
    sys_prompt = SYSTEM_PROMPT_A.format(**kwargs)
    user_prompt = USER_PROMPT_STEP_1.format(choosing_scenes=kwargs["scene"])
    generator.update_prompt(sys_prompt=sys_prompt, user_prompt=user_prompt)
    generator.messages = []
    generator.update_messages()
    return choosing_tools, tool_num, generator, kwargs

def todo_task(folder_path):
    max_number = -1
    pattern = re.compile(r'^(\d+)\.json$')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"{folder_path} created! ")
    else:
        print(f"{folder_path} exists! ")
    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            number = int(match.group(1))
            if max_number is None or number > max_number:
                max_number = number
    return max_number + 1

def shuffle_list(lst):
    to_shuffle = lst[3:]
    random.shuffle(to_shuffle)
    return lst[:3] + to_shuffle

def load_functions_from_api(api_path):
    try:
        spec = importlib.util.spec_from_file_location("api", api_path)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)

        module_name = api.__name__
        local_functions = {}
        for name, obj in api.__dict__.items():
            if hasattr(obj, "__module__") and obj.__module__ == module_name:
                local_functions[name] = obj
        return local_functions

    except Exception as e:
        raise RuntimeError(f"Failed to load functions from {api_path}: {e}")

def list_tools(tools):
    tool_name_list = []
    for category, tools in tools.items():
        for tool, apis in tools.items():
            for api in apis:
                tool_name_list.append(api["function"]["name"])
    return tool_name_list

def get_multi_tools(tool_dir, inference=False):
    all_tools = {}
    tool_name_list = []
    if inference:
        special_tools = [FINISH]
    else:
        special_tools = [
            Question_gen,
            Answer_gen,
            Restart
        ]

    for category in os.listdir(tool_dir):
        category_path = os.path.join(tool_dir, category)
        if os.path.isdir(category_path):
            for tool in [d for d in os.listdir(category_path) if d != "__pycache__"]:
                tool_path = os.path.join(category_path, tool)
                if os.path.isdir(tool_path):
                    api_path = os.path.join(tool_path, "api.py")
                    if os.path.exists(api_path):
                        functions = load_functions_from_api(api_path)
                        if category not in all_tools:
                            all_tools[category] = {}
                        if tool not in all_tools[category]:
                            all_tools[category][tool] = []
                        for func_name, func in functions.items():
                            schema = get_json_schema(func)
                            schema["function"]["name"] = schema["function"]["name"] + "__"+ tool + "__" + category

                            all_tools[category][tool].append(schema)
                            tool_name_list.append(schema["function"]["name"])
    return all_tools, special_tools, tool_name_list


if __name__ == "__main__":
    tools, special_tools, tool_name_list = get_multi_tools("")
    print(tools, special_tools)
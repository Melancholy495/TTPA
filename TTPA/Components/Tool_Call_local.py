import importlib.util
import json
from termcolor import colored

def call_api(category, tool_name, api_name, api_args):
    spec = importlib.util.spec_from_file_location(f"api", f"")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, api_name):
        api_function = getattr(module, api_name)
        args = json.loads(api_args)
        try:
            response = api_function(**args)
        except Exception as e:
            response = {"error": str(e)}
    else:
        response = {"error": "API not found"}
    print(colored(response, "blue"))
    return response

if __name__ == "__main__":
    category = ""
    tool_name = ""
    api_name = ""
    api_args = ''''''
    res = call_api(category, tool_name, api_name, api_args)
    print(res)
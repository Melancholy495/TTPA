import json
from Utils.Elasticsearch import ElasticCache
import re
from termcolor import colored

class ToolCalling:
    def __init__(self):
        self.cache = ElasticCache()

    def _process_error(self, response):
        if "The request to the API has timed out. Please try again later, or if the issue persists" in str(response):
            return_dict = {"error": "API temporarily not working error...", "response": response}

        elif "Your Client (working) ---> Gateway (working) ---> API (not working)" in str(response):
            return_dict = {"error": "API not working error...", "response": response}

        elif "Unauthorized" in str(response) or "unauthorized" in str(response):
            return_dict = {"error": "Unauthorized error...", "response": response}

        elif "You are not subscribed to this API." in str(response):
            return_dict = {"error": "Unsubscribed error...", "response": response}

        elif "Too many requests" in str(response):
            return_dict = {"error": "Too many requests error...", "response": response}

        elif "You have exceeded" in str(response) or "you are being rate limited" in str(response):
            return_dict = {"error": "Rate limit error... Do not use this tool anymore", "response": response}

        elif "Access restricted. Check credits balance or enter the correct API key." in str(response):
            return_dict = {"error": "Rate limit error...", "response": response}

        elif "Oops, an error in the gateway has occurred." in str(response):
            return_dict = {"error": "Gateway error...", "response": response}

        elif "Blocked User. Please contact your API provider." in str(response):
            return_dict = {"error": "Blocked error...", "response": response}

        elif "error" in str(response):
            return_dict = {"error": "Message error...", "response": response}
        elif re.search(r"Endpoint '.*' does not exist", str(response)):
            return_dict = {"error": "Endpoint not exist error...", "response": response}
        else:
            return_dict = {"error": "", "response": response}
        return return_dict

    def _run(self, code_str: str, api_name: str, para_str: str):
        exec(code_str)
        try:
            eval_func_str = f"{api_name}({para_str})"
            tmp_res = eval(eval_func_str)
            response_ = self._process_error(tmp_res)
            response = {"error": response_["error"], "response": json.dumps(response_["response"], ensure_ascii=False)}
        except Exception as e:
            response = {"error": f"Function executing {code_str} error...\n{e}", "response": ""}
        return response

    def _get_rapidapi_response(self, payload: dict):
        code_string = f"""from tools.{payload['category']}.{payload['tool_name']}.api import {payload['api_name']}"""
        api_args = payload['api_args']
        try:
            api_args = json.loads(api_args)

        except Exception as e:
            if api_args == "":
                api_args = {}
            else:
                print(f"Can not parse api input into json: {api_args}")
                response = {"error": f"Api input parse error...\n", "response": ""}
                return response

        arg_str = ""
        if len(api_args) > 0:
            for key, value in api_args.items():
                if isinstance(value, str):
                    value =value.replace('"' ,"'")
                    arg_str += f'{key}="{value}", '
                else:
                    arg_str += f'{key}={value}, '
        try:
            response = self._run(code_string, payload['api_name'], arg_str)
            return response
        except Exception as e:
            return {"error": f"No such function name: {payload['tool_name']}", "response": f"{e}"}

    def call_api(self, category, tool_name, api_name, api_args):
        payload = {
            "category": category,
            "tool_name": tool_name,
            "api_name": api_name,
            "api_args": api_args
        }
        cached_response = self.cache.search_cache(payload)
        if cached_response:
            print(colored(cached_response['response'], "blue"))
            return json.loads(cached_response['response'])
        else:
            response = self._get_rapidapi_response(payload)
            print(colored(response, "blue"))
            if response["error"] == "":
                self.cache.save_to_cache(payload, json.dumps(response, ensure_ascii=False))
            response = {"error": response["error"], "response": response["response"][:8192]}
            return response

if __name__ == "__main__":
    api_calling = ToolCalling()
    payload = {
        "category": "",
        "tool_name": "",
        "api_name": "",
        "api_args": ""
    }
    response_ = api_calling.call_api(**payload)
    print(1)
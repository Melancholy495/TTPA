import random

from .Scene_Simulate import SceneSimulate
from Generator_Api import GeneratorApi
from PROMPTS import SYSTEM_PROMPT_Q, USER_PROMPT_STEP_1, USER_PROMPT_STEP_2, USER_PROMPT_STEP_3, USER_PROMPT_STEP_4
from .Tool_Call_local import call_api
import json
from utils import todo_task, initial_task
from termcolor import colored
import os


class TaskRunner:
    def __init__(self, args):
        self.args = args
        self.count = todo_task(args.train_dir)

        self.tool_num = 7
        self.user_prompt_1 = USER_PROMPT_STEP_1
        self.user_prompt_2 = USER_PROMPT_STEP_2
        self.user_prompt_3 = USER_PROMPT_STEP_3
        self.user_prompt_4 = USER_PROMPT_STEP_4

        self.generator = GeneratorApi(model_id=args.model_id, tool_dir=args.tool_dir,
                                 model_name=args.model_name)

        self.special_tools = self.generator.special_tools
        self.all_tools = self.generator.all_tools
        self.all_tools_name = self.generator.all_tools_name
        self.simulator = SceneSimulate(all_tools=self.all_tools, api_key=args.api_key)
        self.scenario = None
        self.use_tools = self.special_tools
    def run(self):
        args = self.args
        while self.count < args.gen_num:
            print(colored(f"TASK {self.count} STARTED! ", "green"))
            self.use_tools, self.tool_num, self.generator, self.scenario = initial_task(self.simulator, self.generator)
            self.use_tools = self.special_tools + self.use_tools
            self.do_task()
            print(colored(f"TASK {self.count} FINISHED! ", "green"))
            self.count += 1
        print(colored("ALL TASKS FINISHED! ", "green"))

    def do_task(self):
        args = self.args
        tool_called = 0
        F_signal = 0
        to_answer = 0
        final_result = {}
        train_data = {}
        train_error_data = {}
        tool_calls = []
        while F_signal == 0:
            result = self.generator.chat_completion(tools=self.use_tools[1:] if to_answer == 0 else [self.use_tools[1]], messages=self.generator.messages, api_key=args.api_key, model_name=None if to_answer == 0 else "gpt-4o", tool_choice="auto" if to_answer == 0 else "required", color=None if to_answer == 0 else "red")
            result = result["choices"][0]["message"]
            if result["content"] is None:
                result.pop("content")
            if result["tool_calls"] is None:
                result.pop("tool_calls")
            try:
                if result["tool_calls"]:
                    raw_api_name = result["tool_calls"][0]["function"]["name"]
                    raw_api_args = result["tool_calls"][0]["function"]["arguments"]
                    self.generator.update_messages(result)

                    if raw_api_name == "Answer_gen":
                        temp = raw_api_args
                        temp = json.loads(temp)
                        final_result.update(self.scenario)
                        final_result["answer"] = temp["answer"]
                        final_result["tool_calls"] = tool_calls
                        result = self.generator.chat_completion(tools=[self.use_tools[0]], messages=[{"role": "system", "content": SYSTEM_PROMPT_Q}, {"role": "user", "content": json.dumps(final_result, ensure_ascii=False)}], api_key=args.api_key, model_name="gpt-4o", tool_choice="required", color="red")
                        result = result["choices"][0]["message"]
                        if result["content"] is None:
                            result.pop("content")
                        if result["tool_calls"] is None:
                            result.pop("tool_calls")
                        raw_api_name = result["tool_calls"][0]["function"]["name"]
                        raw_api_args = result["tool_calls"][0]["function"]["arguments"]
                        if raw_api_name == "Question_gen":
                            self.generator.update_messages(result)
                            train_data["id"] = self.count
                            train_data["data"] = self.generator.messages
                            train_data["tool_list"] = self.use_tools[3:]
                            with open(args.train_dir+f"/{self.count}.json", "w") as f:
                                f.write(json.dumps(train_data, indent=4, ensure_ascii=False))
                            F_signal = 1
                    elif raw_api_name == "Restart":
                        train_error_data["id"] = self.count
                        self.generator.update_messages(result)
                        train_error_data["data"] = self.generator.messages
                        with open(args.train_error_dir + f"/error_{self.count}.json", "w") as f:
                            f.write(json.dumps(train_error_data, indent=4, ensure_ascii=False))
                        F_signal = 1
                        self.count -= 1
                    elif raw_api_name == "Backward":
                        error_data = json.loads(result["tool_calls"][1])
                        num_ = error_data["backtrack_to_message"]
                        num = (num_//3)*3 - 2
                        self.generator.messages = self.generator.messages[:num if num > 0 else 1]
                        solutions = ''
                        for item in error_data["error_details"]:
                            solutions += item["resolution_attempt"]+'\n'
                        self.generator.update_messages({"role": "user",
                                                   "content": "You have tried this task and you choose to backtrack. These are error summary of the last try:\n" + error_data["error_summary"] + '\nThese are the possible solutions you made:\n' + solutions})
                    else:
                        if raw_api_name not in self.all_tools_name:
                            response = {"error": "The tool is not in the tool list.", "response": ""}
                        else:
                            for i in range(len(self.use_tools)):
                                if raw_api_name in self.use_tools[i]["function"]["name"]:
                                    if not tool_calls:
                                        des = self.use_tools[i]["function"]["description"]
                                        tool_calls.append({"name": raw_api_name, "description": des})
                                    elif raw_api_name not in [call["name"] for call in tool_calls]:
                                        des = self.use_tools[i]["function"]["description"]
                                        tool_calls.append({"name": raw_api_name, "description": des})
                            api_info = raw_api_name.split("__")
                            category = api_info[2]
                            tool_name = api_info[1]
                            api_name = api_info[0]
                            response = call_api(category, tool_name, api_name, raw_api_args)

                        self.generator.update_messages({
                            "role": "tool",
                            "content": json.dumps(response, ensure_ascii=False),
                            "tool_call_id": result["tool_calls"][0]["id"]
                        })

                        tool_called += 1
                        if tool_called == self.tool_num - 2:
                            self.generator.update_messages({"role": "user", "content": self.user_prompt_3})
                        elif tool_called == self.tool_num - 1:
                            self.generator.update_messages({"role": "user", "content": self.user_prompt_4})
                            to_answer = 1
                        else:
                            self.generator.update_messages({"role": "user", "content": self.user_prompt_2})
                else:
                    self.generator.update_messages(result)
                    self.generator.update_messages({"role": "user", "content": self.user_prompt_1})
            except Exception as e:
                print("Error: ", e)
                print(1)
                exit(1)


if __name__ == "__main__":
    args = {
        "model_id": "",
        "tool_dir": "",
        "model_name": "",
        "train_dir": "",
        "train_error_dir": "",
        "gen_num": 10
    }
    task_runner = TaskRunner(args)
    task_runner.run()
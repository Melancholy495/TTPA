import json
import os
import random

from termcolor import colored

from Components.Tool_Call import ToolCalling
from Utils.Generator_Api import GeneratorApi
from Utils.PROMPTS import INFERENCE_PROMPT


class Inference:
    def __init__(self, args):
        self.args = args
        self.tool_dir = args.tool_dir
        with open(args.input_dir) as f:
            input_data = json.load(f)
        input_data = [task for task in input_data if
                      not os.path.exists(os.path.join(args.output_dir, f"{task['id']}.json"))]
        self.input_data = input_data
        self.output_dir = args.output_dir
        self.generator = GeneratorApi(model_id=None, tool_dir=args.tool_dir,
                                 model_name=args.model_name, inference=True)
        self.all_tools = self.generator.all_tools
        self.task_num = len(self.input_data)
        print(colored(f"UNDO TASKS: {self.task_num}", "green"))
        self.category = args.tool_dir.split("/")[-1]
        self.tool_name = None
        self.relevant_tools = None
        self.generator.update_prompt(sys_prompt=INFERENCE_PROMPT)
    def run(self):
        count = 0
        while count < self.task_num:
            task_id = self.input_data[count]["id"]
            print(colored(f"TASK {count} STARTED! TASK_ID: {task_id}", "green"))
            print(colored(f"TASK {count} QUESTION: {self.input_data[count]['question']}", "blue"))
            self.do_task(self.input_data[count])
            print(colored(f"TASK {count} FINISHED! TASK_ID: {task_id}", "green"))
            count += 1
        print(colored("ALL TASKS FINISHED! ", "green"))

    def do_task(self, task: dict, tools_num=0):
        F_signal = 0
        task_id = task["id"]
        tool_name = task["tool_name"]
        relevant_tools = [api for api in self.all_tools[tool_name] if api["function"]["name"] in [relevant_api["name"] for relevant_api in task["relevant_apis"]] or api["function"]["name"] == "Finish"]
        additional_tools = random.sample([api for api in self.all_tools[tool_name] if api not in relevant_tools],
                                        k=(tools_num-len(relevant_tools)) if tools_num>=len(relevant_tools) else 0)
        api_list = relevant_tools + additional_tools
        step = 0
        max_len = 10
        success = False
        final_answer = None
        self.generator.update_prompt(user_prompt=task["question"])
        self.generator.clean_messages()
        self.generator.update_messages()
        while step <= max_len and F_signal != 1:
            result = self.generator.chat_completion(tools=api_list,
                                                    messages=self.generator.messages)
            try:
                if "tool_calls" in result["choices"][0]["message"].keys():
                    api_name = result["choices"][0]["message"]["tool_calls"][0]["function"]["name"]
                    api_args = result["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
                    tool_call_id = result["choices"][0]["message"]["tool_calls"][0]["id"]
                    self.generator.update_messages(result["choices"][0]["message"])
                    step += 1
                    if api_name == "Finish":
                        success, final_answer = self.handle_finish(api_args)
                        self.save_result(task_id, tool_name, success, final_answer)
                        F_signal = 1
                    else:
                        self.handle_tool_call(tool_name, api_name, api_args, tool_call_id)
                else:
                    self.generator.update_messages({"role": "assistant", "content": result["choices"][0]["message"]["content"]})
                    self.generator.update_messages({"role": "user", "content": "You should call one tool."})
                    step += 1
            except Exception as e:
                print("Error: ", e)

        if step > max_len:
            self.save_result(task_id, tool_name, success, final_answer)

    def handle_finish(self, api_args):
        try:
            api_args = json.loads(api_args)
            return_type = api_args["return_type"]
            final_answer = api_args["final_answer"]
            success = return_type == "give_answer"
        except Exception as e:
            success = False
            final_answer = None
        return success, final_answer

    def handle_tool_call(self, tool_name, api_name, api_args, tool_call_id):
        api_calling = ToolCalling()
        response = api_calling.call_api(category=self.category, tool_name=tool_name,
                                        api_name=api_name, api_args=api_args)
        self.generator.update_messages({
            "role": "tool",
            "content": json.dumps(response, ensure_ascii=False),
            "tool_call_id": tool_call_id
        })

    def save_result(self, task_id, tool_name, success, final_answer):
        final_result = {
            "success": success,
            "tool_name": tool_name,
            "id": task_id,
            "data": self.generator.messages,
            "final_answer": final_answer
        }
        with open(self.output_dir + f"/{task_id}.json", "w") as f:
            f.write(json.dumps(final_result, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    class Args:
        tool_dir = ""
        input_dir = ""
        output_dir = ""
        model_name = ""
    args = Args()
    inference = Inference(args)
    inference.run()
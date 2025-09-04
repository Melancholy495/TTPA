from openai import OpenAI
from .Generator import Generator
from termcolor import colored
import re
import random
from json_repair import json_repair
import json

class GeneratorApi(Generator):
    def _format_openai_res(self, tool_flag, **kwargs):
        if not tool_flag:
            openai_res = {
                "usage": {
                    "total_tokens": kwargs["total_tokens"]
                },
                "choices": [
                    {
                        "message": {
                            "content": kwargs["content"],
                            "tool_calls": None,
                            "role": kwargs["role"]
                        }
                    }
                ]
            }
        else:
            openai_res = {
                "usage": {
                    "total_tokens": kwargs["total_tokens"]
                },
                "choices": [
                    {
                        "message": {
                            "content": kwargs["content"],
                            "tool_calls": [
                                {
                                    "type": "function",
                                    "id": kwargs["id"],
                                    "function": {
                                        "name": kwargs["tool_name"],
                                        "arguments": kwargs["tool_args"]
                                    }
                                }
                            ],
                            "role": kwargs["role"]
                        }
                    }
                ]
            }
        return openai_res

    def _get_tool(self, response, model, prefill=False):
        tool_name = None
        tool_input = None
        tool = {}
        tool_flag = False
        parsed_content = None
        json_data = {
            "role": response.choices[0].message.role,
            "total_tokens": response.usage.total_tokens
        }
        if "gpt" or "deepseek" in model.lower():
            content = response.choices[0].message.content
            if content == "":
                content = None
            if response.choices[0].message.tool_calls:
                tool_flag = True
            if tool_flag:
                json_data.update({
                    "id": response.choices[0].message.tool_calls[0].id,
                    "tool_name": response.choices[0].message.tool_calls[0].function.name,
                    "tool_args": response.choices[0].message.tool_calls[0].function.arguments,
                    "content": content
                })
        else:
            content = response.choices[0].message.content
            if "llama" in model.lower():
                use_content = content.replace("<|python_tag|>", "").strip()
                split_str = r"}\s*;\s*{"
                content_parts = re.split(split_str, use_content)
                try:
                    for item in content_parts:
                        if item == content_parts[0]:
                            item = item + "}"
                        elif item == content_parts[-1]:
                            item = "{" + item
                        else:
                            item = "{" + item + "}"
                        if len(content_parts) == 1:
                            item = item[:-1]
                        tool = json_repair.loads(item)
                        break
                except Exception as e:
                    pass
            elif "qwen" in model.lower():
                if prefill is True:
                    content = '''<tool_call>\n{"name": "''' + content
                regex = re.compile(r"<tool_call>(.+?)</tool_call>(?=\s*<tool_call>|\s*$)", re.DOTALL)
                tool_match = re.findall(regex, content)
                if not tool_match:
                    pass
                else:
                    for tool in tool_match:
                        try:
                            tool = json.loads(tool.strip())
                        except Exception as e:
                            pass
                        break
            elif "xlam" in model.lower():
                if prefill is True:
                    content = '''{"thought": "''' + content
                try:
                    tool_result = json.loads(content)
                    if len(tool_result["tool_calls"]) > 0:
                        tool = tool_result["tool_calls"][0]
                    parsed_content = tool_result["thought"]
                except Exception as e:
                    pass
            try:
                tool_name = tool["name"]
                if "parameters" in tool.keys() or "arguments" in tool.keys():
                    tool_input = tool.get("parameters", {}) or tool.get("arguments", {})
                    if isinstance(tool_input, dict):
                        tool_input = json.dumps(tool_input, ensure_ascii=False)
                    tool_flag = True
            except Exception as e:
                pass
            if tool_flag:
                json_data.update({
                    "id": "tool_" + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9)),
                    "tool_name": tool_name,
                    "tool_args": tool_input,
                    "content": parsed_content
                })
            else:
                json_data.update({
                    "content": content
                })
        openai_res = self._format_openai_res(tool_flag, **json_data)
        return openai_res

    def chat_completion(self, tools, messages, api_key={}, model_name=None, tool_choice="auto", color=None, temperature=1):
        if self.model_id == None:
            use_messages = []
            for message in messages:
                if message["role"] == "user" and message == messages[1]:
                    if len(messages) <=2:
                        use_messages.append(message)
                    else:
                        use_messages.append({"role": "user", "content": "Begin and try to call tools and generate the question and answers."})
                elif message["role"] != "user":
                    use_messages.append(message)
            if len(messages) > 2:
                use_messages.append(messages[-1])

            model_name = model_name or self.model_name

            if "gpt" in model_name:
                client = OpenAI(api_key=api_key["oa"], base_url="")
            elif "deepseek" in model_name :
                client = OpenAI(api_key=api_key["ds"], base_url="")
            else:
                client = OpenAI(api_key="0", base_url="")

            params = {
                "messages": use_messages,
                "model": model_name,
                "temperature": temperature,
            }

            if tools is not None:
                params.update({
                    "tools": tools,
                    "tool_choice": tool_choice,
                })

            response = client.chat.completions.create(**params)
            return_data = self._get_tool(response, model_name)
            if return_data["choices"][0]["message"]["tool_calls"]:
                print(colored(return_data["choices"][0]["message"]["tool_calls"][0]["function"], color))
            else:
                print(colored(return_data["choices"][0]["message"]["content"], color))
            return return_data
        else:
            super().chat_completion(tools, messages)

if __name__ == "__main__":
    from utils import shuffle_list
    from Special_Function import Answer_gen, Question_gen
    sys_prompt = "You are an assistant."
    user_prompt = "Write a question based on the given answer.\nAnswer: As a financial analyst planning a holiday cruise, I've explored cruise options focusing on Mexico for an enriching vacation experience.\n\nThe top available cruise I identified is onboard the \"Carnival Radiance\" offered by Carnival Cruise Line. This cruise is titled \"4-day Baja Mexico\" and is scheduled to depart from Los Angeles. The cruise itinerary includes stops at Catalina Island, California, and Ensenada before returning to Los Angeles. This specific trip is thoughtfully packed with entertainment and activities, ideal for individuals looking for a well-rounded cruising experience.\n\nThe Carnival Radiance ship boasts a variety of amenities to enjoy, such as multiple restaurants, a comedy club, waterslides, and exclusive dining at Chef's table. Launching in 2020, the ship has a modern appeal that balances affordability with a vibrant, new-ship atmosphere.\n\nReflecting on user experiences, reviews indicate varied opinions with an average rating of 2.5 stars from 33 reviewers. While some passengers particularly enjoyed the range of activities, others recommended early bookings to avoid busy times onboard. Prices and availability suggest that the lowest priced sailing date is December 15, 2024, signifying the immediate opportunity for cost savings while securing an adventurous getaway to Mexico."
    tool_dir: str = ""
    multi_tools = True
    color = "green"
    generator = GeneratorApi(model_id=None, sys_prompt=sys_prompt, user_prompt=user_prompt, tool_dir=tool_dir, model_name="gpt-4o-mini")
    generator.update_messages()
    tools = generator.all_tools["math"]["Elementary"]
    tools.insert(0, {"type": "function", "function": Answer_gen})
    tools.insert(0, {"type": "function", "function": Question_gen})

    tools = shuffle_list(tools)
    result = generator.chat_completion(tools=[tools[0]], messages=generator.messages, tool_choice="required")
    print(colored(result, color))


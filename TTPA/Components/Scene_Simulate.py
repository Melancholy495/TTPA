import sys

sys.path.append("..")
import random
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel
from PROMPTS import SCENE_SIMULATE_PROMPT
import json

class Scene(BaseModel):
    scenario: str
    additional_information: list[str]
    tools: list[str]

class SceneSimulate:
    def __init__(self, all_tools, api_key):
        self.client = OpenAI(api_key=api_key["oa"], base_url="")
        self.tool_num = random.randint(4, 7)
        self.all_tools = all_tools
        self.tools = []

    def _parse_tools(self):
        for category, tools in self.all_tools.items():
            for tool, apis in tools.items():
                for api in apis:
                    self.tools.append(api)

    def _check_tools_num(self):
        if len(self.tools) == 0:
            self._parse_tools()

    def simulate(self):
        self._check_tools_num()
        start = random.randint(0, len(self.tools) - 6)
        use_tools = self.tools[start:min(start + 20, len(self.tools))]
        response = self.client.beta.chat.completions.parse(
            model="",
            messages=[
                {"role": "user", "content": SCENE_SIMULATE_PROMPT.format(tools = use_tools)},
            ],
            response_format=Scene
        )
        scenario = response.choices[0].message.parsed.scenario
        additional_information = ""
        for i, item in enumerate(response.choices[0].message.parsed.additional_information):
            additional_information += f"{i + 1}. {item}\n"
        choosing_tool_names = response.choices[0].message.parsed.tools
        choosing_tools = [api for api in use_tools if api["function"]["name"] in choosing_tool_names]
        if len(choosing_tools) == 0:
            choosing_tools = random.sample(use_tools, min(5, len(use_tools)))
        return {"scene": scenario, "add_info": additional_information}, choosing_tools

if __name__ == "__main__":
    api_key = ""
    tool_dir = ""
    from utils import get_multi_tools
    tools, tools_reversed, special_tools = get_multi_tools(tool_dir=tool_dir, inference=False)
    scene_simulator = SceneSimulate(tools, api_key)
    kwargs, choosing_tools = scene_simulator.simulate()
    print(kwargs)
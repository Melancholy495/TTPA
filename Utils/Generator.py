import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
import json
import math
import os
from Utils.utils import get_multi_tools

class Generator:
    def __init__(self, model_id, tool_dir, sys_prompt="You are a helpful assistant.", user_prompt="Hello, world!", model_name=None, inference=False):
        self.sys_prompt = sys_prompt
        self.user_prompt = user_prompt
        self.tokenizer = None
        self.model = None
        self.generating_args = None
        self.model_id = model_id
        if model_id:
            self.model_name = model_id.split("/")[-1]
            self.load_model(model_id)
        else:
            self.model_name = model_name
        self.all_tools, self.special_tools, self.all_tools_name = get_multi_tools(tool_dir=tool_dir, inference=inference)
        self.messages = []

    def load_model(self, model_id):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

        self.generating_args = GenerationConfig.from_pretrained(model_id)
        self.generating_args.max_new_tokens = 1024
        self.generating_args.temperature = 1
        self.generating_args.pad_token_id = self.tokenizer.eos_token_id

        self.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16, device_map="auto", attn_implementation="flash_attention_2")
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

    def chat_completion(self, tools, messages):
        inputs = self.tokenizer.apply_chat_template(messages,
                                                    tools=tools,
                                                    add_generation_prompt=True,
                                                    return_dict=True,
                                                    return_tensors="pt").to(self.model.device)

        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        outputs = self.model.generate(**inputs,
                                      generation_config=self.generating_args,
                                      return_dict_in_generate=True,
                                      output_logits=True)

        logits = outputs['logits']
        response_ids = outputs['sequences'][0][len(inputs["input_ids"][0]):]

        logprobs = []
        for i in range(len(logits)):
            logprobs.append(torch.nn.functional.softmax(logits[i], dim=-1))
        total_logprob = 0
        for i, logprob in enumerate(logprobs):
            if int(response_ids[i]) not in self.tokenizer.added_tokens_decoder.keys():
                token_logprob = math.log(logprob[0][response_ids[i]])
                total_logprob += token_logprob
        average_logprob = total_logprob / (len(response_ids) - 1)
        perplexity = math.exp(-average_logprob)

        response = self.tokenizer.decode(response_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        if response_ids[-1] == 128008:
            response = json.loads(response)
            tool_name = response["name"]
            tool_args = response["parameters"]
            return {"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": tool_name, "arguments": tool_args}}]}
        else:
            content = response
            return {"role": "assistant", "content": content}

    def update_prompt(self, sys_prompt=None, user_prompt=None):
        if sys_prompt:
            self.sys_prompt = sys_prompt
        if user_prompt:
            self.user_prompt = user_prompt
    def update_messages(self, new_message=None):
        if len(self.messages) == 0:
            self.messages.append({"role": "system", "content": self.sys_prompt})
            self.messages.append({"role": "user", "content": self.user_prompt})
        if new_message:
            self.messages.append(new_message)
    def clean_messages(self):
        self.messages = []


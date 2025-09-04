import json

from Components.Q_A_Generate import TaskRunner
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--tool_dir", type=str, help="tool directory")
parser.add_argument("--train_dir", type=str, help="train directory")
parser.add_argument("--train_error_dir", type=str, default=None, help="train error directory")
parser.add_argument("--model_id", type=str, default=None, help="model id")
parser.add_argument("--model_name", type=str, default="gpt-4o-mini", help="model name")
parser.add_argument("--gen_num", type=int, default=100, help="the number of tasks to generate")
parser.add_argument("--api_key", type=str, default="{}", help="api_key for LLMs server")
args = parser.parse_args()
args.model_id = None if args.model_id == "None" else args.model_id
args.api_key = json.loads(args.api_key.replace("'", '"'))
task_runner = TaskRunner(args)
task_runner.run()


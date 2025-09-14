from Components.Inference import Inference
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--tool_dir', type=str, help='tool directory')
parser.add_argument('--input_dir', type=str, help='input directory')
parser.add_argument("--output_dir", type=str, default=None, help='output directory')
parser.add_argument('--model_id', type=str, required=False, default=None, help='model id')
parser.add_argument('--model_name', type=str, default="gpt-4o-mini", help='model name')
args = parser.parse_args()
args.model_id = None if args.model_id == "None" else args.model_id

inference = Inference(args)
inference.run()
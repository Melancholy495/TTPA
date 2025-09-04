# TTPA

Existing tool-learning methods usually rely on supervised fine-tuning, they often overlook fine-grained optimization of internal tool call details, leading to limitations in preference alignment and error discrimination. To overcome these challenges, we propose Token-level Tool-use Preference Alignment Training Framework (TTPA), a training paradigm for constructing token-level tool-use preference datasets that align LLMs with fine-grained preferences using a novel error-oriented scoring mechanism. TTPA first introduces reversed dataset construction, a method for creating high-quality, multiturn tool-use datasets by reversing the generation flow. Additionally, we propose Token level Preference Sampling (TPS) to capture fine-grained preferences by modeling token-level differences during generation. To address biases in scoring, we introduce the Error-oriented Scoring Mechanism (ESM), which quantifies tool-call errors and can be used as a training signal. Extensiveexperiments on three diverse benchmark datasets demonstrate that TTPA significantly improves tool-using performance while showing strong generalization ability across models and datasets.

<img width="2064" height="1161" alt="image" src="https://github.com/user-attachments/assets/ffcdee8d-8c3a-4efb-83bc-8746ec5258d4" />


More details coming soon

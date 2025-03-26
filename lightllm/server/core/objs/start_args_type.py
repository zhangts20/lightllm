from dataclasses import dataclass, field
from typing import List, Optional, Union

# 只是为了更好的编程提示


@dataclass
class StartArgs:
    run_mode: str = field(default="normal", metadata={"choices": ["normal", "prefill", "decode", "pd_master"]})
    host: str = field(default="127.0.0.1")
    port: int = field(default=8000)
    zmq_mode: str = field(
        default="ipc:///tmp/",
        metadata={"help": "use socket mode or ipc mode, only can be set in ['tcp://', 'ipc:///tmp/']"},
    )
    pd_master_ip: str = field(default="127.0.0.1")
    pd_master_port: int = field(default=1212)
    pd_decode_rpyc_port: int = field(default=42000)
    model_name: str = field(default="default_model_name")
    model_dir: Optional[str] = field(default=None)
    tokenizer_mode: str = field(default="slow")
    load_way: str = field(default="HF")
    max_total_token_num: Optional[int] = field(default=None)
    mem_fraction: float = field(default=0.9)
    batch_max_tokens: Optional[int] = field(default=None)
    eos_id: List[int] = field(default_factory=list)
    running_max_req_size: int = field(default=1000)
    tp: int = field(default=1)
    dp: int = field(default=1)
    max_req_total_len: int = field(default=2048 + 1024)
    nccl_port: int = field(default=28765)
    mode: List[str] = field(default_factory=list)
    trust_remote_code: bool = field(default=False)
    disable_log_stats: bool = field(default=False)
    log_stats_interval: int = field(default=10)
    router_token_ratio: float = field(default=0.0)
    router_max_new_token_len: int = field(default=1024)
    router_max_wait_tokens: int = field(default=6)
    use_dynamic_prompt_cache: bool = field(default=False)
    chunked_prefill_size: int = field(default=8192)
    enable_chunked_prefill: bool = field(default=False)
    diverse_mode: bool = field(default=False)
    token_healing_mode: bool = field(default=False)
    output_constraint_mode: str = field(default="none", metadata={"choices": ["none", "simple", "xgrammar"]})
    first_token_constraint_mode: bool = field(default=False)
    enable_multimodal: bool = field(default=False)
    is_embedding: bool = field(default=False)
    cache_capacity: int = field(default=200)
    cache_reserved_ratio: float = field(default=0.5)
    data_type: Optional[str] = field(
        default=None, metadata={"choices": ["fp16", "float16", "bf16", "bfloat16", "fp32", "float32"]}
    )
    return_all_prompt_logprobs: bool = field(default=False)
    use_reward_model: bool = field(default=False)
    long_truncation_mode: Optional[str] = field(default=None, metadata={"choices": [None, "head", "center"]})
    use_tgi_api: bool = field(default=False)
    health_monitor: bool = field(default=False)
    metric_gateway: Optional[str] = field(default=None)
    job_name: str = field(default="lightllm")
    grouping_key: List[str] = field(default_factory=list)
    push_interval: int = field(default=10)
    visual_infer_batch_size: int = field(default=1)
    visual_gpu_ids: List[int] = field(default_factory=lambda: [0])
    visual_tp: int = field(default=1)
    visual_dp: int = field(default=1)
    visual_nccl_ports: List[int] = field(default_factory=lambda: [29500])
    enable_monitor_auth: bool = field(default=False)
    disable_cudagraph: bool = field(default=False)
    graph_max_batch_size: int = field(default=16)
    graph_max_len_in_batch: int = field(default=8192)
    quant_type: Optional[str] = field(default=None)
    quant_cfg: Optional[str] = field(default=None)
    vit_quant_type: Optional[str] = field(default=None)
    vit_quant_cfg: Optional[str] = field(default=None)
    static_quant: bool = field(default=False)

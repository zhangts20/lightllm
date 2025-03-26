import json
import numpy as np
import unicodedata
from lightllm.models.qwen.model import QWenTpPartModel
from lightllm.models.qwen_vl.layer_infer.pre_layer_infer import LlamaMultimodalPreLayerInfer
from lightllm.server.multimodal_params import MultimodalParams, ImageItem
from transformers.feature_extraction_utils import BatchFeature
from transformers.image_utils import ImageInput
from transformers.processing_utils import ProcessorMixin
from transformers.tokenization_utils_base import PaddingStrategy, PreTokenizedInput, TextInput, TruncationStrategy
from typing import List, Optional, Union
from transformers.utils import TensorType, logging
from lightllm.common.build_utils import repair_config

# from lightllm.models.qwen2_vl.vision_process import Qwen2VLImageProcessor
import torch
import torch.nn as nn
from PIL import Image
from enum import IntEnum
from .vision_process import smart_resize
from lightllm.models.qwen2.layer_weights import transformer_layer_weight, pre_and_post_layer_weight
from lightllm.models.qwen2.model import Qwen2TpPartModel
import os

# from lightllm.models.qwen2_vl.layer_weight.pre_and_post_layer_weight import Qwen2VLPreAndPostLayerWeight

# Warp of the origal tokenizer
class QWen2VLTokenizer:
    def __init__(self, tokenizer=None, image_processor=None, **kwargs):
        self.tokenizer = tokenizer
        self.image_processor = image_processor
        self.image_start_id = kwargs["model_cfg"]["vision_start_token_id"]
        self.image_end_id = kwargs["model_cfg"]["vision_end_token_id"]
        self.image_token_id = kwargs["model_cfg"]["image_token_id"]

    def get_image_token_length(self, img: ImageItem):
        width = img.image_w
        height = img.image_h
        resized_height, resized_width = smart_resize(height=height, width=width)
        self.patch_size = self.image_processor.image_processor.patch_size
        self.merge_size = self.image_processor.image_processor.merge_size
        grid_t = 1
        grid_h, grid_w = resized_height // self.patch_size, resized_width // self.patch_size
        merge_length = self.merge_size ** 2
        self.token_num = (grid_t * grid_h * grid_w) // merge_length
        self.image_length = self.token_num
        return self.image_length

    def encode(self, prompt, multimodal_params: MultimodalParams = None, **kwargs):

        origin_ids = self.tokenizer.encode(prompt)

        # <img><image_pad></img> -> <img></img>
        origin_ids = [token for token in origin_ids if token != self.image_token_id]
        # <img></img> --> <img>id,id+1...id+num</img>
        input_ids = []
        image_id = 0
        start_idx = 0
        while True:
            try:
                start_idx = origin_ids.index(self.image_start_id, start_idx)
                if start_idx + 1 >= len(origin_ids):
                    break
                if origin_ids[start_idx + 1] == self.image_end_id:
                    input_ids.extend(origin_ids[: start_idx + 1])
                    token_id = multimodal_params.images[image_id].token_id
                    token_num = multimodal_params.images[image_id].token_num
                    input_ids.extend(range(token_id, token_id + token_num))
                    input_ids.append(self.image_end_id)
                    origin_ids = origin_ids[start_idx + 2 :]
                    start_idx = 0
                    image_id += 1
                else:
                    raise ValueError("image token error")
            except ValueError:
                break
        input_ids.extend(origin_ids[start_idx:])
        return input_ids

    def __getattr__(self, name):
        if name != "encode":
            return getattr(self.tokenizer, name)
        return self.encode


class Qwen2VLTpPartModel(Qwen2TpPartModel):

    # weight class
    # pre_and_post_weight_class = Qwen2VLPreAndPostLayerWeight
    # infer class
    pre_layer_infer_class = LlamaMultimodalPreLayerInfer

    def __init__(self, kvargs):
        super().__init__(kvargs)
        return

    def _init_config(self):
        with open(os.path.join(self.weight_dir_, "config.json"), "r") as json_file:
            self.config = json.load(json_file)
        # rename keys
        repair_config(self.config, same_names=["num_attention_heads", "n_head"])
        repair_config(self.config, same_names=["hidden_size", "n_embd", "n_embed"])
        repair_config(self.config, same_names=["num_hidden_layers", "n_layer"])
        if self.finetune_config:
            self.config["vocab_size"] = self.finetune_config.vocab_size
        return


class PoolingType(IntEnum):
    LAST = 0


class Qwen2VLEmbeddingPostLayerInfer(object):

    def __init__(self, network_config, mode):
        pass

    def token_forward(self, input_embdings: torch.Tensor, infer_state, layer_weight) -> None:
        pooling_type = PoolingType.LAST
        normalize = True

        b_seq_len_numpy = (infer_state.b_seq_len - infer_state.b_ready_cache_len).detach().cpu().numpy()
        print(b_seq_len_numpy)
        print(infer_state.b_seq_len)
        seq_lengths = torch.tensor([infer_state.b_seq_len.shape[0]])
        if pooling_type == PoolingType.LAST:
            last_token_indices = torch.cumsum(seq_lengths, dim=0) - 1
            pooled_data = input_embdings[last_token_indices]
        else:
            raise ValueError(f"Unsupported pooling type {pooling_type}")

        if normalize:
            pooled_data = nn.functional.normalize(pooled_data, p=2, dim=1)

        return pooled_data


class Qwen2VLEmbeddingTpPartModel(Qwen2VLTpPartModel):

    # infer
    post_layer_infer_class = Qwen2VLEmbeddingPostLayerInfer

    def __init__(self, kvargs: dict):
        super().__init__(kvargs)

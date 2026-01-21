"""Model Loader for Production Inference.

This module provides a singleton loader for the fine-tuned T5 model
used to generate time recommendation summaries with traceback analysis.
"""

import logging
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

logger = logging.getLogger(__name__)


class SummarizationModelLoader:
    """Loads and manages the T5 summarization model.
    
    This class provides a unified interface for loading the model from
    either local storage or HuggingFace Hub.
    
    Attributes:
        model_path: Path or identifier for the model
        device: Device to run inference on ('cuda' or 'cpu')
        tokenizer: Loaded tokenizer instance
        model: Loaded model instance
    """
    
    
    def __init__(
        self,
        model_path: str = "raflisbk/t5-posting-time-summarizer",
        subfolder: str = "stage2",
        device: Optional[str] = None,
        token: Optional[str] = None
    ) -> None:
        """Initialize model loader.
        
        Args:
            model_path: Path to model directory or HuggingFace model ID
                       Default: "raflisbk/t5-posting-time-summarizer"
            subfolder: Subfolder within repo (for HuggingFace Hub)
                      Default: "stage2" for Stage 2 model with traceback
                      Use "stage1" for Stage 1 model (narrative only)
            device: Device to load model on ('cuda', 'cpu', or None for auto)
            token: HuggingFace token for private repos (optional)
        """
        self.model_path = model_path
        self.subfolder = subfolder
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.token = token
        
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForSeq2SeqLM] = None
        
        logger.info(
            f"Initializing model loader - Path: {model_path}, "
            f"Subfolder: {subfolder}, Device: {self.device}"
        )
    
    def load(self) -> None:
        """Load tokenizer and model from disk or HuggingFace Hub.
        
        For Stage 2 models, this loads the base model from stage1 and
        applies the LoRA adapter from stage2, then merges them for
        faster inference.
        
        Raises:
            OSError: If model files cannot be loaded
            ValueError: If subfolder is invalid
        """
        logger.info(f"Loading model from: {self.model_path}/{self.subfolder}")
        
        # Determine if loading from local path or Hub
        is_local = Path(self.model_path).exists()
        
        # Validate subfolder
        if self.subfolder not in ["stage1", "stage2"]:
            raise ValueError(
                f"Invalid subfolder '{self.subfolder}'. "
                "Must be 'stage1' or 'stage2'"
            )
        
        # Load tokenizer (always from stage1 for consistency)
        tokenizer_subfolder = "stage1"
        if is_local:
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(Path(self.model_path) / tokenizer_subfolder)
            )
            logger.info("Tokenizer loaded from local path")
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                subfolder=tokenizer_subfolder,
                token=self.token
            )
            logger.info(
                f"Tokenizer loaded from HuggingFace Hub "
                f"(subfolder: {tokenizer_subfolder})"
            )
        
        # Load model with appropriate dtype
        torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        # Load base model from stage1
        base_subfolder = "stage1"
        logger.info(f"Loading base model from {base_subfolder}...")
        
        if is_local:
            # For local files, load config first and remove quantization
            from transformers import AutoConfig
            
            config_path = str(Path(self.model_path) / base_subfolder)
            config = AutoConfig.from_pretrained(config_path)
            
            # Remove quantization config completely
            if hasattr(config, 'quantization_config') and config.quantization_config is not None:
                delattr(config, 'quantization_config')
            
            # Load model with clean config
            base_model = AutoModelForSeq2SeqLM.from_pretrained(
                config_path,
                config=config,
                torch_dtype=torch_dtype
            )
        else:
            base_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_path,
                subfolder=base_subfolder,
                torch_dtype=torch_dtype,
                token=self.token
            )
        
        logger.info("Base model loaded successfully")
        
        # If stage2, load and merge LoRA adapter
        if self.subfolder == "stage2":
            logger.info("Loading Stage 2 LoRA adapter...")
            
            # Load PEFT model with adapter
            if is_local:
                # Local: point directly to stage2 folder
                adapter_path = str(Path(self.model_path) / "stage2")
                self.model = PeftModel.from_pretrained(
                    base_model,
                    adapter_path
                )
            else:
                # HuggingFace Hub: use repo_id with subfolder
                self.model = PeftModel.from_pretrained(
                    base_model,
                    self.model_path,
                    subfolder="stage2",
                    token=self.token
                )
            
            logger.info("LoRA adapter loaded, merging with base model...")
            
            # Merge adapter for faster inference
            self.model = self.model.merge_and_unload()
            
            logger.info("Stage 2 model merged successfully")
        else:
            # Stage 1: use base model directly
            self.model = base_model
            logger.info("Using Stage 1 base model")
        
        # Move to device and set eval mode
        self.model = self.model.to(self.device)
        self.model.eval()
        
        logger.info(
            f"Model loaded successfully on {self.device} "
            f"(Stage: {self.subfolder})"
        )
    
    def is_loaded(self) -> bool:
        """Check if model and tokenizer are loaded.
        
        Returns:
            True if both model and tokenizer are loaded, False otherwise
        """
        return self.tokenizer is not None and self.model is not None


# Global singleton instance
_model_loader: Optional[SummarizationModelLoader] = None


def get_model_loader(
    model_path: Optional[str] = None,
    subfolder: str = "stage2",
    token: Optional[str] = None
) -> SummarizationModelLoader:
    """Get or create the global model loader instance.
    
    This function implements the singleton pattern to ensure only one
    model is loaded in memory at a time.
    
    Args:
        model_path: Optional path to model (only used on first call)
                   Default: "raflisbk/t5-posting-time-summarizer"
        subfolder: Subfolder containing model
                  "stage1" = Narrative only
                  "stage2" = Narrative + Traceback (default)
        token: HuggingFace token for private repos (optional)
    
    Returns:
        SummarizationModelLoader instance
    
    Example:
        >>> # Load Stage 2 (with traceback)
        >>> loader = get_model_loader(subfolder="stage2", token="hf_...")
        >>> 
        >>> # Or load Stage 1 (narrative only)
        >>> loader = get_model_loader(subfolder="stage1")
    """
    global _model_loader
    
    if _model_loader is None:
        default_path = "raflisbk/t5-posting-time-summarizer"
        _model_loader = SummarizationModelLoader(
            model_path=model_path or default_path,
            subfolder=subfolder,
            token=token
        )
        _model_loader.load()
    
    return _model_loader

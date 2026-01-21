"""Summarization Service for Production Inference.

This module provides the main inference logic for generating time
recommendation summaries with traceback analysis from aggregation data.
"""

import logging
import re
from typing import Any, Dict, List, Tuple, Optional

import torch

from model_loader import get_model_loader

logger = logging.getLogger(__name__)


class Summarizer:
    """Main summarization service for generating recommendation summaries.
    
    This class handles the end-to-end process of formatting input data,
    running model inference, and returning generated summaries.
    
    Attributes:
        model_loader: Instance of SummarizationModelLoader
        tokenizer: Tokenizer from model loader
        model: Model from model loader
        device: Device for inference
    """
    
    def __init__(self) -> None:
        """Initialize summarizer with model loader."""
        self.model_loader = get_model_loader()
        self.tokenizer = self.model_loader.tokenizer
        self.model = self.model_loader.model
        self.device = self.model_loader.device
        
        logger.info("Summarizer initialized successfully")
    
    def format_input(self, hourly_summary: Dict[str, Any]) -> str:
        """Format hourly_summary from aggregation into model input.
        
        Args:
            hourly_summary: Dictionary containing:
                - day (str): Day of week (e.g., "Monday")
                - time_window (str): Time range (e.g., "17:00 - 20:00")
                - score (float): Recommendation score (e.g., 85.2)
                - daily_avg (float): Daily average score
                - peak_hour (int): Peak hour within window
                - peak_value (float): Score at peak hour
                - hourly (str): Comma-separated hourly scores
                               (e.g., "06(52), 07(58), ...")
        
        Returns:
            Formatted input string ready for model tokenization
        
        Example:
            >>> summary = {
            ...     "day": "Monday",
            ...     "time_window": "17:00 - 20:00",
            ...     "score": 85.2,
            ...     "daily_avg": 69.0,
            ...     "peak_hour": 18,
            ...     "peak_value": 89.0,
            ...     "hourly": "06(52), 07(58), ..."
            ... }
            >>> input_text = summarizer.format_input(summary)
        """
        input_text = (
            f"Day: {hourly_summary['day']}, "
            f"Time: {hourly_summary['time_window']}, "
            f"Score: {int(hourly_summary['score'])}\n"
            f"Hourly: {hourly_summary['hourly']}\n"
            f"Daily Avg: {hourly_summary['daily_avg']}, "
            f"Peak: {hourly_summary['peak_hour']:02d}"
            f"({hourly_summary['peak_value']})"
        )
        
        return input_text
    
    def _parse_hourly_data(self, hourly_str: str) -> List[Tuple[int, float]]:
        """Parse hourly string into list of (hour, value) tuples.
        
        Args:
            hourly_str: String like "01(67), 02(39), 03(75), ..."
        
        Returns:
            List of (hour, value) tuples: [(1, 67.0), (2, 39.0), ...]
        """
        pattern = r'(\d+)\((\d+(?:\.\d+)?)\)'
        matches = re.findall(pattern, hourly_str)
        return [(int(h), float(v)) for h, v in matches]
    
    def _calculate_time_window_avg(
        self,
        hourly_data: List[Tuple[int, float]],
        start_hour: int,
        end_hour: int
    ) -> float:
        """Calculate average value for a time window.
        
        Args:
            hourly_data: List of (hour, value) tuples
            start_hour: Start hour (inclusive)
            end_hour: End hour (exclusive)
        
        Returns:
            Average value for the time window
        """
        values = [v for h, v in hourly_data if start_hour <= h < end_hour]
        return sum(values) / len(values) if values else 0.0
    
    def _extract_comparison_windows(
        self,
        generated_text: str
    ) -> List[Tuple[str, str]]:
        """Extract comparison time windows from generated text.
        
        Args:
            generated_text: Model output with traceback
        
        Returns:
            List of (window_name, time_range) tuples
            Example: [("Morning", "06:00 - 09:00"), ...]
        """
        # Pattern: "vs Morning 06:00 - 09:00" or "vs Afternoon 12:00 - 15:00"
        pattern = r'vs\s+([\w\s]+?)\s+(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})'
        matches = re.findall(pattern, generated_text)
        return [(name.strip(), time_range) for name, time_range in matches]
    
    def _parse_time_range(self, time_range: str) -> Tuple[int, int]:
        """Parse time range string to (start_hour, end_hour).
        
        Args:
            time_range: String like "06:00 - 09:00"
        
        Returns:
            Tuple of (start_hour, end_hour): (6, 9)
        """
        match = re.match(r'(\d{2}):\d{2}\s*-\s*(\d{2}):\d{2}', time_range)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0
    
    def _fix_traceback_calculations(
        self,
        generated_text: str,
        hourly_summary: Dict[str, Any]
    ) -> str:
        """Fix calculation errors in insight/traceback section while preserving narrative.
        
        This function:
        1. Identifies the Insight/Traceback section.
        2. Recalculates peak vs daily avg percentage.
        3. Fixes hour/point mentions if they mismatch data.
        4. Recalculates comparison window improvements.
        
        Args:
            generated_text: Raw model output
            hourly_summary: Original input data
        
        Returns:
            Corrected text with accurate calculations
        """
        # Parse hourly data for lookups
        hourly_data = self._parse_hourly_data(hourly_summary['hourly'])
        hourly_dict = dict(hourly_data)
        
        daily_avg = float(hourly_summary['daily_avg'])
        peak_value = float(hourly_summary['peak_value'])
        peak_hour = int(hourly_summary['peak_hour'])
        
        # 1. Fix "XX% higher than the daily average"
        def fix_percentage(match):
            val_str = match.group(2)
            try:
                # Try to find what value is being compared
                # Usually it's the peak value in the same sentence
                sentence = generated_text[max(0, match.start()-100):match.end()]
                points_match = re.findall(r'(\d+(?:\.\d+)?)\s*points?', sentence)
                current_val = float(points_match[-1]) if points_match else peak_value
                
                correct_pct = int(((current_val - daily_avg) / daily_avg) * 100)
                return f"{correct_pct}% higher than the daily average of {daily_avg}"
            except:
                return match.group(0)

        # Pattern: XX% higher than the daily average of YY
        generated_text = re.sub(
            r'(\d+)%\s+higher\s+than\s+the\s+daily\s+average\s+of\s+([\d.]+)',
            fix_percentage,
            generated_text
        )

        # 2. Fix "The H AM/PM hour hits V points"
        def fix_hour_points(match):
            hour = int(match.group(1))
            # Basic AM/PM detection if present, else assume 24h or relative to peak
            meridiem = match.group(2).upper() if match.group(2) else ""
            
            actual_hour = hour
            if meridiem == "PM" and hour < 12:
                actual_hour += 12
            elif meridiem == "AM" and hour == 12:
                actual_hour = 0
                
            if actual_hour in hourly_dict:
                actual_val = hourly_dict[actual_hour]
                # Format as integer if it's a whole number
                val_fmt = int(actual_val) if actual_val.is_integer() else actual_val
                return f"The {hour} {meridiem} hour hits {val_fmt} points".replace("  ", " ")
            return match.group(0)

        generated_text = re.sub(
            r'The\s+(\d+)\s*(AM|PM)?\s*hour\s+hits\s+(\d+(?:\.\d+)?)\s+points',
            fix_hour_points,
            generated_text,
            flags=re.IGNORECASE
        )

        # 3. Fix legacy style "Peak: XX:XX (YY), +ZZ%"
        correct_peak_pct = int(((peak_value - daily_avg) / daily_avg) * 100)
        peak_pattern = r'(\bPeak\b:\s*\d{2}:\d{2}\s*\(\d+(?:\.\d+)?\),\s*)\+(\d+)%'
        generated_text = re.sub(
            peak_pattern,
            rf'\1+{correct_peak_pct}%',
            generated_text
        )

        # 4. Fix comparison windows (vs Morning, etc.)
        comparison_windows = self._extract_comparison_windows(generated_text)
        for window_name, time_range in comparison_windows:
            start_hour, end_hour = self._parse_time_range(time_range)
            if start_hour and end_hour:
                actual_avg = self._calculate_time_window_avg(hourly_data, start_hour, end_hour)
                
                # Fix avg in "vs Window ... (avg ZZ.Z)"
                window_pattern = rf'(vs\s+{re.escape(window_name)}\s+{re.escape(time_range)}\s+\(avg\s+)\d+(?:\.\d+)?\)'
                generated_text = re.sub(window_pattern, rf'\1{actual_avg:.1f})', generated_text)
                
                # Fix improvement %
                window_score = hourly_summary.get('score', peak_value)
                if actual_avg > 0:
                    correct_improvement = int(((window_score - actual_avg) / actual_avg) * 100)
                    improvement_pattern = rf'(vs\s+{re.escape(window_name)}[^:]+:\s*)\+(\d+)%'
                    generated_text = re.sub(improvement_pattern, rf'\1+{correct_improvement}%', generated_text)
        
        return generated_text
    
    def _format_traceback_newlines(self, text: str) -> str:
        """Format traceback/insight section with proper newlines and bullets.
        
        Args:
            text: Raw generated text
            
        Returns:
            Text with newlines and clean bullets.
        """
        # Ensure space after Insight: if it's missing
        text = re.sub(r'(Insight|Traceback):([^\s\n])', r'\1: \2', text)
        
        # Add broad spacing before Insight:
        text = re.sub(r'([\.!?])\s*(Insight|Traceback):', r'\1\n\n\2:', text)
        
        # Split bullets into lines
        # This handles cases where bullets are clumped together "- Bullet 1. - Bullet 2."
        if "Insight:" in text or "Traceback:" in text:
            header = "Insight:" if "Insight:" in text else "Traceback:"
            parts = text.split(header)
            narrative = parts[0]
            insight_content = parts[1]
            
            # Find bullet markers (- or •)
            bullets = re.split(r'\s*[-\u2022]\s+', insight_content)
            # Filter empty strings from split
            bullets = [b.strip() for b in bullets if b.strip()]
            
            if bullets:
                formatted_insight = header + "\n- " + "\n- ".join(bullets)
                text = narrative.strip() + "\n\n" + formatted_insight
            
        return text.strip()

    def generate(
        self,
        hourly_summary: Dict[str, Any],
        max_length: int = 512,
        num_beams: int = 4
    ) -> str:
        """Generate summary with traceback from hourly_summary.
        
        Args:
            hourly_summary: Aggregation output (see format_input for structure)
            max_length: Maximum generation length in tokens
                       Default: 512 (increased for traceback)
            num_beams: Number of beams for beam search
                      Higher values = better quality but slower
                      Default: 4
        
        Returns:
            Generated summary text with narrative and traceback analysis
        
        Raises:
            RuntimeError: If model inference fails
        """
        # Format input
        input_text = self.format_input(hourly_summary)
        logger.debug(f"Input (truncated): {input_text[:100]}...")
        
        # Add T5 prefix
        input_with_prefix = f"summarize: {input_text}"
        
        # Tokenize
        inputs = self.tokenizer(
            input_with_prefix,
            return_tensors="pt",
            max_length=256,
            truncation=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate with torch.no_grad() for inference efficiency
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=num_beams,
                early_stopping=True,
                do_sample=False,
                no_repeat_ngram_size=3,
                length_penalty=1.0
            )
        
        # Decode output
        generated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
        
        # Apply post-processing to fix calculations
        corrected_text = self._fix_traceback_calculations(
            generated_text,
            hourly_summary
        )
        
        # Apply formatting for newlines
        final_text = self._format_traceback_newlines(corrected_text)
        
        logger.info(
            f"Generated summary successfully "
            f"({len(final_text)} characters)"
        )
        return final_text


# Global singleton instance
_summarizer: Optional[Summarizer] = None


def get_summarizer() -> Summarizer:
    """Get or create the global summarizer instance.
    
    This function implements the singleton pattern to reuse the
    same model instance across multiple calls.
    
    Returns:
        Summarizer instance with loaded model
    
    Example:
        >>> summarizer = get_summarizer()
        >>> result = summarizer.generate(hourly_summary)
    """
    global _summarizer
    
    if _summarizer is None:
        _summarizer = Summarizer()
    
    return _summarizer


def generate_summary(hourly_summary: Dict[str, Any]) -> str:
    """Convenience function to generate summary.
    
    This is a simplified interface that handles model loading
    and inference in a single function call.
    
    Args:
        hourly_summary: Aggregation output dictionary
    
    Returns:
        Generated summary text with narrative and traceback
    
    Example:
        >>> hourly_summary = {
        ...     "day": "Monday",
        ...     "time_window": "17:00 - 20:00",
        ...     "score": 85.2,
        ...     "daily_avg": 69.0,
        ...     "peak_hour": 18,
        ...     "peak_value": 89.0,
        ...     "hourly": "06(52), 07(58), 08(62), ..."
        ... }
        >>> summary = generate_summary(hourly_summary)
        >>> print(summary)
    """
    summarizer = get_summarizer()
    return summarizer.generate(hourly_summary)

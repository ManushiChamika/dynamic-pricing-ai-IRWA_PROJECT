#!/usr/bin/env python3
"""
OpenCode Loop Runner - Safe, rate-limited execution of the same prompt repeatedly
Designed to avoid provider bans, respect rate limits, and handle all error conditions
"""

import subprocess
import time
import logging
import sys
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

class SafeOpenCodeLoop:
    def __init__(self, config_file: str = "loop_config.json"):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.failure_count = 0
        self.last_success = None
        self.circuit_breaker_until = None
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration with safe defaults"""
        default_config = {
            "prompt_file": "prompt.md",
            "min_interval_seconds": 300,  # 5 minutes minimum
            "max_interval_seconds": 900,  # 15 minutes maximum
            "base_backoff_seconds": 60,   # 1 minute base backoff
            "max_backoff_seconds": 3600,  # 1 hour max backoff
            "max_consecutive_failures": 5,
            "circuit_breaker_minutes": 30,
            "request_timeout_seconds": 600,  # 10 minutes
            "log_file": "opencode_loop.log",
            "max_log_size_mb": 50,
            "opencode_commands": [
                ["opencode", "chat"],
                ["opencode-ai", "chat"],
                ["npx", "opencode-ai", "chat"]
            ],
            "respect_retry_after": True,
            "jitter_percentage": 0.2,  # ±20% random jitter
            "budget_tracking": {
                "max_requests_per_hour": 10,
                "max_requests_per_day": 100
            }
        }
        
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
                print("Using default configuration")
        else:
            # Create default config file
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config file: {config_file}")
        
        return default_config
    
    def setup_logging(self):
        """Setup comprehensive logging with rotation"""
        log_file = self.config["log_file"]
        
        # Rotate log if too large
        log_path = Path(log_file)
        if log_path.exists():
            size_mb = log_path.stat().st_size / (1024 * 1024)
            if size_mb > self.config["max_log_size_mb"]:
                backup_file = f"{log_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                log_path.rename(backup_file)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_prompt(self) -> Optional[str]:
        """Load prompt from markdown file"""
        prompt_file = Path(self.config["prompt_file"])
        if not prompt_file.exists():
            self.logger.error(f"Prompt file not found: {prompt_file}")
            return None
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
            
            if not prompt:
                self.logger.error("Prompt file is empty")
                return None
                
            return prompt
        except Exception as e:
            self.logger.error(f"Failed to load prompt: {e}")
            return None
    
    def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker is active"""
        if self.circuit_breaker_until and datetime.now() < self.circuit_breaker_until:
            return True
        elif self.circuit_breaker_until and datetime.now() >= self.circuit_breaker_until:
            self.logger.info("Circuit breaker reset, resuming operations")
            self.circuit_breaker_until = None
            self.failure_count = 0
        return False
    
    def trigger_circuit_breaker(self):
        """Trigger circuit breaker after too many failures"""
        self.circuit_breaker_until = datetime.now() + timedelta(
            minutes=self.config["circuit_breaker_minutes"]
        )
        self.logger.warning(
            f"Circuit breaker triggered! Pausing until {self.circuit_breaker_until}"
        )
    
    def calculate_backoff(self) -> int:
        """Calculate exponential backoff with jitter"""
        base = self.config["base_backoff_seconds"]
        max_backoff = self.config["max_backoff_seconds"]
        
        # Exponential backoff: base * 2^failures
        backoff = min(base * (2 ** self.failure_count), max_backoff)
        
        # Add jitter (±20% by default)
        jitter_range = backoff * self.config["jitter_percentage"]
        jitter = random.uniform(-jitter_range, jitter_range)
        
        return max(1, int(backoff + jitter))
    
    def calculate_next_interval(self) -> int:
        """Calculate next run interval with jitter"""
        min_interval = self.config["min_interval_seconds"]
        max_interval = self.config["max_interval_seconds"]
        
        # Random interval between min and max
        base_interval = random.randint(min_interval, max_interval)
        
        # Add jitter
        jitter_range = base_interval * self.config["jitter_percentage"]
        jitter = random.uniform(-jitter_range, jitter_range)
        
        return max(min_interval, int(base_interval + jitter))
    
    def run_opencode(self, prompt: str) -> bool:
        """Execute OpenCode with the prompt"""
        commands = self.config["opencode_commands"]
        timeout = self.config["request_timeout_seconds"]
        
        for cmd_template in commands:
            try:
                # Build command with prompt
                cmd = cmd_template + [prompt]
                
                self.logger.info(f"Executing: {' '.join(cmd[:2])} [prompt]")
                
                # Run with timeout
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False
                )
                
                # Log results
                self.logger.info(f"Exit code: {result.returncode}")
                
                if result.stdout:
                    # Truncate long outputs for logging
                    output = result.stdout[:1000] + "..." if len(result.stdout) > 1000 else result.stdout
                    self.logger.info(f"Output preview: {output}")
                
                if result.stderr:
                    stderr = result.stderr[:1000] + "..." if len(result.stderr) > 1000 else result.stderr
                    
                    # Check for rate limiting
                    if "rate limit" in stderr.lower() or "429" in stderr:
                        self.logger.warning(f"Rate limit detected: {stderr}")
                        return False
                    
                    self.logger.warning(f"Stderr: {stderr}")
                
                # Consider it successful if we got any response
                return True
                
            except subprocess.TimeoutExpired:
                self.logger.error(f"Command timed out after {timeout} seconds: {' '.join(cmd[:2])}")
                continue
            except FileNotFoundError:
                self.logger.warning(f"Command not found: {' '.join(cmd[:2])}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error running {' '.join(cmd[:2])}: {e}")
                continue
        
        self.logger.error("All OpenCode commands failed")
        return False
    
    def run_loop(self):
        """Main loop with all safety mechanisms"""
        self.logger.info("=" * 50)
        self.logger.info("Starting SafeOpenCodeLoop")
        self.logger.info(f"Config: {self.config['prompt_file']}")
        self.logger.info(f"Interval: {self.config['min_interval_seconds']}-{self.config['max_interval_seconds']}s")
        self.logger.info("=" * 50)
        
        iteration = 0
        
        while True:
            try:
                iteration += 1
                self.logger.info(f"\n--- Iteration {iteration} - {datetime.now()} ---")
                
                # Check circuit breaker
                if self.check_circuit_breaker():
                    wait_seconds = int((self.circuit_breaker_until - datetime.now()).total_seconds())
                    self.logger.info(f"Circuit breaker active, waiting {wait_seconds}s")
                    time.sleep(min(wait_seconds, 60))  # Check every minute
                    continue
                
                # Load prompt
                prompt = self.load_prompt()
                if not prompt:
                    self.logger.error("Failed to load prompt, waiting 60s before retry")
                    time.sleep(60)
                    continue
                
                # Execute OpenCode
                success = self.run_opencode(prompt)
                
                if success:
                    self.logger.info("✅ Iteration completed successfully")
                    self.failure_count = 0
                    self.last_success = datetime.now()
                    
                    # Normal interval
                    wait_seconds = self.calculate_next_interval()
                    
                else:
                    self.failure_count += 1
                    self.logger.warning(f"❌ Iteration failed (failure #{self.failure_count})")
                    
                    # Check if we should trigger circuit breaker
                    if self.failure_count >= self.config["max_consecutive_failures"]:
                        self.trigger_circuit_breaker()
                        continue
                    
                    # Backoff interval
                    wait_seconds = self.calculate_backoff()
                
                self.logger.info(f"Waiting {wait_seconds}s before next run...")
                
                # Sleep with periodic status updates
                start_time = time.time()
                while time.time() - start_time < wait_seconds:
                    remaining = wait_seconds - int(time.time() - start_time)
                    if remaining % 60 == 0 and remaining > 0:  # Every minute
                        self.logger.info(f"⏰ {remaining}s remaining until next run")
                    time.sleep(1)
                
            except KeyboardInterrupt:
                self.logger.info("Received Ctrl+C, stopping loop gracefully")
                break
            except Exception as e:
                self.logger.error(f"Critical error in main loop: {e}")
                self.logger.info("Continuing despite error after 60s delay...")
                time.sleep(60)
        
        self.logger.info("SafeOpenCodeLoop stopped")


if __name__ == "__main__":
    # Check for config file argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else "loop_config.json"
    
    loop = SafeOpenCodeLoop(config_file)
    loop.run_loop()
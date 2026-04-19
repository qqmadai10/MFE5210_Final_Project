import yaml
import os
from core.models import Signal, Direction

class RiskEngine:
    def __init__(self, config_path: str = "config/risk_rules.yaml"):
        # 确保路径正确：如果文件不存在，打印错误并设置默认规则
        if not os.path.exists(config_path):
            print(f"Warning: config file {config_path} not found. Using default rules.")
            self.rules = {
                'max_order_volume': 0.01,
                'max_position': 0.05
            }
        else:
            with open(config_path, 'r') as f:
                self.rules = yaml.safe_load(f)
                if self.rules is None:
                    self.rules = {}
            # 设置默认值，防止键缺失
            self.rules.setdefault('max_order_volume', 0.01)
            self.rules.setdefault('max_position', 0.05)
        print(f"RiskEngine rules: {self.rules}")
        self.positions = {}

    def update_position(self, symbol: str, signed_volume: float):
        old = self.positions.get(symbol, 0.0)
        self.positions[symbol] = old + signed_volume
        print(f"Risk: position for {symbol} updated: {old} -> {self.positions[symbol]}")

    def check_signal(self, signal: Signal) -> tuple[bool, str]:
        current = self.positions.get(signal.symbol, 0.0)
        signed = signal.volume if signal.direction == Direction.BUY else -signal.volume
        new_pos = current + signed
        max_pos = self.rules.get('max_position', 0.05)
        print(
            f"Risk: checking signal {signal.direction} {signal.volume} | current_pos={current:.4f} new_pos={new_pos:.4f} max_pos={max_pos}")
        # 确保规则存在
        max_vol = self.rules.get('max_order_volume', 0.01)
        max_pos = self.rules.get('max_position', 0.05)
        if signal.volume > max_vol:
            return False, f"Volume {signal.volume} exceeds limit {max_vol}"
        signed = signal.volume if signal.direction == Direction.BUY else -signal.volume
        new_pos = self.positions.get(signal.symbol, 0.0) + signed
        if abs(new_pos) > max_pos:
            return False, f"Position would exceed {max_pos}"
        return True, "OK"
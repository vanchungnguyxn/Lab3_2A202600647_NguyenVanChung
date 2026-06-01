import ast
import operator
from typing import Any, Dict, List

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _ALLOWED_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        operand = _safe_eval(node.operand)
        return _ALLOWED_OPERATORS[type(node.op)](operand)
    raise ValueError("Only basic arithmetic is allowed")


def calculator(expression: str) -> str:
    """Safely calculate arithmetic expressions such as 1200000 * 0.1."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree)
        return str(round(result, 6))
    except Exception as exc:
        return f"calculator_error: {exc}"


def order_lookup(order_id: str) -> str:
    """Mock order lookup tool for e-commerce/customer-support use cases."""
    fake_orders = {
        "A1001": "Order A1001: delivered, total 250000 VND, customer Nguyen Van A.",
        "A1002": "Order A1002: shipping, expected delivery tomorrow, total 490000 VND.",
        "A1003": "Order A1003: payment pending, total 120000 VND.",
    }
    return fake_orders.get(order_id.strip().upper(), f"order_not_found: {order_id}")


def shipping_fee(weight_kg: str) -> str:
    """Calculate a simple shipping fee in VND from package weight in kg."""
    try:
        weight = float(weight_kg)
        base_fee = 18000
        extra_fee = max(0, weight - 1) * 7000
        return f"{int(base_fee + extra_fee)} VND"
    except Exception as exc:
        return f"shipping_fee_error: {exc}"


def get_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "calculator",
            "description": "Calculate math expressions. Input example: calculator(250000 + 18000)",
            "func": calculator,
        },
        {
            "name": "order_lookup",
            "description": "Look up mock order status by order ID. Input example: order_lookup(A1002)",
            "func": order_lookup,
        },
        {
            "name": "shipping_fee",
            "description": "Calculate shipping fee from package weight in kg. Input example: shipping_fee(2.5)",
            "func": shipping_fee,
        },
    ]
